from django.shortcuts import render, redirect
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required
from rest_framework import views, status, permissions
from rest_framework.response import Response
from rest_framework.renderers import TemplateHTMLRenderer, JSONRenderer
from datetime import datetime, timedelta
import json

from .models import FeaturedDestination
from .serializers import FeaturedDestinationSerializer
from .utils.amadeus_api import AmadeusAPI


class HomeView(views.APIView):
    """
    Vue pour la page d'accueil qui combine API et rendu HTML
    """
    permission_classes = [permissions.AllowAny]
    renderer_classes = [TemplateHTMLRenderer, JSONRenderer]
    template_name = 'api_reservation/home.html'
    
    def get(self, request, format=None):
        tomorrow = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')
        
        # Définir les routes populaires
        popular_routes = [
            {
                'origin': 'CDG',  # Paris Charles de Gaulle
                'destination': 'JFK',  # New York JFK
                'origin_city': 'Paris',
                'destination_city': 'New York',
                'image_url': 'https://images.unsplash.com/photo-1496442226666-8d4d0e62e6e9?w=500',
            },
            {
                'origin': 'CDG',  # Paris
                'destination': 'DXB',  # Dubai
                'origin_city': 'Paris',
                'destination_city': 'Dubai',
                'image_url': 'https://images.unsplash.com/photo-1512453979798-5ea266f8880c?w=500',
            },
            {
                'origin': 'CDG',  # Paris
                'destination': 'BCN',  # Barcelona
                'origin_city': 'Paris',
                'destination_city': 'Barcelone',
                'image_url': 'https://images.unsplash.com/photo-1583422409516-2895a77efded?w=500',
            },
            {
                'origin': 'CDG',  # Paris
                'destination': 'LHR',  # London Heathrow
                'origin_city': 'Paris',
                'destination_city': 'Londres',
                'image_url': 'https://images.unsplash.com/photo-1513635269975-59663e0ac1ad?w=500',
            },
        ]
        
        # Récupérer les prix pour chaque route
        amadeus = AmadeusAPI()
        for route in popular_routes:
            try:
                flight_offers = amadeus.search_flights(
                    origin=route['origin'],
                    destination=route['destination'],
                    departure_date=tomorrow,
                    return_date=None,
                    adults=1,
                    children=0,
                    infants=0,
                    travel_class='ECONOMY'
                )
                
                if flight_offers and len(flight_offers) > 0:
                    route['price'] = flight_offers[0]['price']['total']
                    route['currency'] = flight_offers[0]['price']['currency']
                else:
                    route['price'] = None
                    route['currency'] = None
            except Exception as e:
                route['price'] = None
                route['currency'] = None
        
        # Selon le format demandé, renvoyer HTML ou JSON
        if request.accepted_renderer.format == 'html':
            return Response({'popular_routes': popular_routes, 'tomorrow': tomorrow})
        return Response(popular_routes)


class FlightSearchView(views.APIView):
    """
    Vue pour la recherche de vols qui combine API et rendu HTML
    """
    permission_classes = [permissions.AllowAny]
    renderer_classes = [TemplateHTMLRenderer, JSONRenderer]
    template_name = 'api_reservation/search_form.html'
    
    def get(self, request, format=None):
        context = {
            'tomorrow': (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')
        }
        return Response(context)
    
    @method_decorator(csrf_exempt)
    def post(self, request, format=None):
        # Déterminer si la requête est une soumission de formulaire ou une requête API
        is_api_request = request.content_type == 'application/json' or format == 'json'
        
        if is_api_request:
            # Traitement comme API
            serializer = FlightSearchSerializer(data=request.data)
            if serializer.is_valid():
                amadeus = AmadeusAPI()
                
                flight_offers = amadeus.search_flights(
                    origin=serializer.validated_data['origin'],
                    destination=serializer.validated_data['destination'],
                    departure_date=serializer.validated_data['departure_date'].strftime('%Y-%m-%d'),
                    return_date=serializer.validated_data.get('return_date', None).strftime('%Y-%m-%d') if serializer.validated_data.get('return_date') else None,
                    adults=serializer.validated_data['adults'],
                    children=serializer.validated_data['children'],
                    infants=serializer.validated_data.get('infants', 0),
                    travel_class=serializer.validated_data['travel_class']
                )
                
                if flight_offers:
                    return Response(flight_offers)
                return Response({"error": "Aucun vol trouvé."}, status=status.HTTP_404_NOT_FOUND)
            
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        else:
            # Traitement comme formulaire HTML
            data = request.data if isinstance(request.data, dict) else request.POST.dict()
            
            origin = data.get('origin', '').strip().upper()
            destination = data.get('destination', '').strip().upper()
            departure_date = data.get('departure_date', '').strip()
            adults = int(data.get('adults', 1))
            
            # Validation des données
            context = {
                'tomorrow': (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')
            }
            
            if not all([origin, destination, departure_date]):
                context['error'] = 'Veuillez remplir tous les champs obligatoires.'
                return Response(context, template_name='api_reservation/search_form.html')
            
            try:
                # Recherche avec l'API Amadeus
                amadeus = AmadeusAPI()
                
                # Vérification des aéroports
                origin_data = amadeus.search_airport(origin)
                destination_data = amadeus.search_airport(destination)
                
                if not origin_data:
                    raise ValueError(f"Aéroport de départ '{origin}' non trouvé")
                if not destination_data:
                    raise ValueError(f"Aéroport d'arrivée '{destination}' non trouvé")
                
                origin_code = origin_data[0]['iataCode']
                destination_code = destination_data[0]['iataCode']
                origin_city = origin_data[0]['name']
                destination_city = destination_data[0]['name']
                
                # Recherche des vols
                flight_offers = amadeus.search_flights(
                    origin=origin_code,
                    destination=destination_code,
                    departure_date=departure_date,
                    return_date=data.get('return_date', None),
                    adults=adults,
                    children=int(data.get('children', 0)),
                    infants=int(data.get('infants', 0)),
                    travel_class=data.get('travel_class', 'ECONOMY')
                )
                
                search_results_context = {
                    'flights': flight_offers,
                    'origin_city': origin_city,
                    'destination_city': destination_city,
                    'departure_date': departure_date,
                    'adults': adults
                }
                
                if not flight_offers:
                    search_results_context['message'] = 'Aucun vol trouvé pour ces critères.'
                
                return Response(
                    search_results_context, 
                    template_name='api_reservation/search_results.html'
                )
                
            except ValueError as e:
                context['error'] = str(e)
                return Response(context, template_name='api_reservation/search_form.html')
            except Exception as e:
                error_message = str(e)
                context['error'] = error_message
                return Response(context, template_name='api_reservation/search_form.html')


class AirportSearchView(views.APIView):
    """
    Recherche d'aéroports pour l'autocomplétion
    """
    permission_classes = [permissions.AllowAny]
    
    def get(self, request):
        term = request.query_params.get('term', '')
        if term:
            try:
                amadeus = AmadeusAPI()
                results = amadeus.search_airport(term)
                
                formatted_results = []
                for item in results:
                    formatted_results.append({
                        'label': f"{item['name']} ({item['iataCode']})",
                        'value': item['iataCode']
                    })
                    
                return Response(formatted_results)
            except Exception as e:
                return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)
        return Response([])


class BookFlightView(views.APIView):
    """
    Vue pour la réservation de vols
    """
    permission_classes = [permissions.IsAuthenticated]
    renderer_classes = [TemplateHTMLRenderer, JSONRenderer]
    template_name = 'api_reservation/booking_form.html'
    
    def post(self, request, format=None):
        # Récupération des données du vol
        flight_data = {
            'id': request.data.get('flight_id'),
            'origin': request.data.get('origin'),
            'destination': request.data.get('destination'),
            'departure_date': request.data.get('departure_date'),
            'number_of_passengers': int(request.data.get('number_of_passengers', 1)),
            'total_price': float(request.data.get('total_price')),
            'currency': request.data.get('currency'),
            'flight_details': request.data.get('flight_details')
        }
        
        # Stockage dans la session
        request.session['selected_flight'] = flight_data
        
        # Retourner le formulaire de réservation
        return Response({
            'flight': flight_data,
            'number_of_passengers': flight_data['number_of_passengers']
        })


class ConfirmBookingView(views.APIView):
    """
    Vue pour confirmer une réservation
    """
    permission_classes = [permissions.IsAuthenticated]
    renderer_classes = [TemplateHTMLRenderer, JSONRenderer]
    
    def post(self, request, format=None):
        flight_data = request.session.get('selected_flight')
        if not flight_data:
            if request.accepted_renderer.format == 'html':
                messages.error(request, 'Session expirée. Veuillez recommencer votre recherche.')
                return redirect('search_flights')
            return Response(
                {'error': 'Session expirée. Veuillez recommencer votre recherche.'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        try:
            # Création de la réservation
            reservation = Reservation.objects.create(
                user=request.user,
                flight_offer_id=flight_data['id'],
                origin=flight_data['origin'],
                destination=flight_data['destination'],
                departure_date=flight_data['departure_date'],
                return_date=flight_data.get('return_date'),
                number_of_passengers=flight_data['number_of_passengers'],
                total_price=flight_data['total_price'],
                currency=flight_data['currency'],
                status='EN_ATTENTE',
                flight_details=flight_data
            )
            
            # Création des passagers
            passengers_data = []
            for i in range(flight_data['number_of_passengers']):
                prefix = f'passenger_{i}_'
                
                # Récupération des données du formulaire pour chaque passager
                passenger = Passenger(
                    reservation=reservation,
                    first_name=request.data.get(f'{prefix}first_name'),
                    last_name=request.data.get(f'{prefix}last_name'),
                    email=request.data.get(f'{prefix}email'),
                    phone_number=request.data.get(f'{prefix}phone'),
                    date_of_birth=request.data.get(f'{prefix}date_of_birth'),
                    gender=request.data.get(f'{prefix}gender'),
                    passport_number=request.data.get(f'{prefix}passport'),
                    passport_expiry=request.data.get(f'{prefix}passport_expiry')
                )
                passengers_data.append(passenger)
            
            # Création en masse des passagers
            Passenger.objects.bulk_create(passengers_data)
            
            # Nettoyage de la session
            if 'selected_flight' in request.session:
                del request.session['selected_flight']
            
            # Envoi d'un email de confirmation (optionnel)
            try:
                from .utils import send_booking_confirmation_email
                send_booking_confirmation_email(reservation, passengers_data)
            except:
                pass
            
            if request.accepted_renderer.format == 'html':
                messages.success(request, 'Votre réservation a été confirmée avec succès!')
                return redirect('booking_confirmation', reservation_id=reservation.id)
            
            return Response({
                'success': True,
                'message': 'Votre réservation a été confirmée avec succès!',
                'reservation_id': reservation.id
            })
            
        except Exception as e:
            if request.accepted_renderer.format == 'html':
                messages.error(request, f'Une erreur est survenue lors de la réservation: {str(e)}')
                return redirect('search_flights')
            
            return Response(
                {'error': f'Une erreur est survenue lors de la réservation: {str(e)}'},
                status=status.HTTP_400_BAD_REQUEST
            )


class BookingConfirmationView(views.APIView):
    """
    Vue pour afficher la confirmation de réservation
    """
    permission_classes = [permissions.IsAuthenticated]
    renderer_classes = [TemplateHTMLRenderer, JSONRenderer]
    template_name = 'api_reservation/booking_confirmation.html'
    
    def get(self, request, reservation_id, format=None):
        try:
            reservation = Reservation.objects.get(id=reservation_id, user=request.user)
            
            if request.accepted_renderer.format == 'html':
                return Response({'reservation': reservation})
            
            # Sérialiser la réservation pour l'API
            # Pour simplifier, on renvoie directement les données brutes
            # Vous devriez normalement utiliser un sérialiseur approprié
            return Response({
                'id': reservation.id,
                'flight_offer_id': reservation.flight_offer_id,
                'origin': reservation.origin,
                'destination': reservation.destination,
                'departure_date': reservation.departure_date,
                'return_date': reservation.return_date,
                'number_of_passengers': reservation.number_of_passengers,
                'total_price': reservation.total_price,
                'currency': reservation.currency,
                'status': reservation.status,
                'created_at': reservation.created_at
            })
            
        except Reservation.DoesNotExist:
            if request.accepted_renderer.format == 'html':
                messages.error(request, 'Réservation non trouvée.')
                return redirect('search_flights')
            
            return Response(
                {'error': 'Réservation non trouvée.'},
                status=status.HTTP_404_NOT_FOUND
            )


class MyBookingsView(views.APIView):
    """
    Vue pour afficher les réservations de l'utilisateur
    """
    permission_classes = [permissions.IsAuthenticated]
    renderer_classes = [TemplateHTMLRenderer, JSONRenderer]
    template_name = 'api_reservation/my_bookings.html'
    
    def get(self, request, format=None):
        reservations = Reservation.objects.filter(user=request.user).order_by('-created_at')
        
        if request.accepted_renderer.format == 'html':
            return Response({'reservations': reservations})
        
        # Pour l'API, vous devriez utiliser un sérialiseur approprié
        # Ceci est une simplification
        reservations_data = []
        for reservation in reservations:
            reservations_data.append({
                'id': reservation.id,
                'flight_offer_id': reservation.flight_offer_id,
                'origin': reservation.origin,
                'destination': reservation.destination,
                'departure_date': reservation.departure_date,
                'return_date': reservation.return_date,
                'number_of_passengers': reservation.number_of_passengers,
                'total_price': reservation.total_price,
                'currency': reservation.currency,
                'status': reservation.status,
                'created_at': reservation.created_at
            })
        
        return Response(reservations_data)


class CancelReservationView(views.APIView):
    """
    Vue pour annuler une réservation
    """
    permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request, reservation_id, format=None):
        try:
            reservation = Reservation.objects.get(id=reservation_id, user=request.user)
            if reservation.status == 'EN_ATTENTE':
                reservation.status = 'ANNULE'
                reservation.save()
                
                if format == 'html':
                    messages.success(request, 'Votre réservation a été annulée avec succès.')
                    return redirect('my_bookings')
                
                return Response({'success': True, 'message': 'Votre réservation a été annulée avec succès.'})
            else:
                if format == 'html':
                    messages.error(request, 'Cette réservation ne peut pas être annulée.')
                    return redirect('my_bookings')
                
                return Response(
                    {'error': 'Cette réservation ne peut pas être annulée.'},
                    status=status.HTTP_400_BAD_REQUEST
                )
                
        except Reservation.DoesNotExist:
            if format == 'html':
                messages.error(request, 'Réservation non trouvée.')
                return redirect('my_bookings')
            
            return Response(
                {'error': 'Réservation non trouvée.'},
                status=status.HTTP_404_NOT_FOUND
            )


class RandomDestinationsView(views.APIView):
    """
    Vue pour afficher des destinations aléatoires
    """
    permission_classes = [permissions.AllowAny]
    
    def get(self, request):
        # Sélectionner des destinations aléatoires à partir des destinations caractérisées
        import random
        featured = list(FeaturedDestination.objects.filter(is_active=True))
        random_destinations = []
        
        if featured:
            # Prendre au maximum 6 destinations aléatoires
            random_count = min(6, len(featured))
            random_destinations = random.sample(featured, random_count)
        
        serializer = FeaturedDestinationSerializer(random_destinations, many=True)
        return Response(serializer.data)


# Ajouter cette méthode utilitaire pour faciliter la recherche d'aéroports
class AmadeusAPIUtils(AmadeusAPI):
    """
    Extension de la classe AmadeusAPI avec des méthodes utilitaires supplémentaires
    """
    
    def search_airport(self, keyword):
        """
        Recherche d'aéroports par mot-clé
        """
        try:
            # Utiliser l'instance d'Amadeus pour rechercher les aéroports
            # Cette méthode doit être implémentée dans votre classe AmadeusAPI
            return self.amadeus_client.reference_data.locations.get(
                keyword=keyword,
                subType=["AIRPORT"]
            ).data
        except Exception as e:
            # Gérer les erreurs de l'API
            print(f"Erreur lors de la recherche d'aéroport: {str(e)}")
            return []