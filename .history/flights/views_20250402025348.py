
import random
from rest_framework import views, generics, permissions
from rest_framework.response import Response
from .models import Airport, FlightOffer, FeaturedDestination
from .serializers import (
    AirportSerializer, FeaturedDestinationSerializer,
    FlightSearchSerializer, MultiCityFlightSearchSerializer
)
from .utils.amadeus_api import AmadeusAPI
from datetime import datetime, timedelta
from django.http import HttpRequest
import requests
from ipware import get_client_ip
from amadeus import Client, ResponseError
from decouple import config
amadeus = Client(
    client_id=config('AMADEUS_CLIENT_ID'),
    client_secret=config('AMADEUS_CLIENT_SECRET')
)



class PopularRoutesView(views.APIView):
    permission_classes = [permissions.AllowAny]
   
    def get(self, request):
        tomorrow = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')
        
        # Get user's IP address
        client_ip, is_routable = get_client_ip(request)
        
        # Get user's country and currency from IP
        user_info = self.get_location_info_from_ip(client_ip)
        user_country = user_info['country_code']
        user_currency = user_info['currency']
        
        # Define primary airports for African countries
        african_airports = {
            'CI': {'code': 'ABJ', 'city': 'Abidjan'},  # Côte d'Ivoire
            'SN': {'code': 'DSS', 'city': 'Dakar'},    # Sénégal
            'CM': {'code': 'DLA', 'city': 'Douala'},   # Cameroun
            'NG': {'code': 'LOS', 'city': 'Lagos'},    # Nigeria
            'MA': {'code': 'CMN', 'city': 'Casablanca'}, # Maroc
        }
        
        # Get the appropriate origin airport based on user's country
        origin_airport = african_airports.get(user_country, {'code': 'CDG', 'city': 'Paris'})
        
        # Define popular routes based on user's location
        if user_country == 'CI':  # Côte d'Ivoire
            popular_routes = [
                {
                    'origin': 'ABJ',
                    'destination': 'CDG',
                    'origin_city': 'Abidjan',
                    'destination_city': 'Paris',
                    'image_url': 'https://images.unsplash.com/photo-1502602898657-3e91760cbb34?w=500',
                },
                {
                    'origin': 'ABJ',
                    'destination': 'LHR',
                    'origin_city': 'Abidjan',
                    'destination_city': 'London',
                    'image_url': 'https://images.unsplash.com/photo-1505761671935-60b3a7427bad?w=500',
                },
                {
                    'origin': 'ABJ',
                    'destination': 'JFK',
                    'origin_city': 'Abidjan',
                    'destination_city': 'New York',
                    'image_url': 'https://images.unsplash.com/photo-1496442226666-8d4d0e62e6e9?w=500',
                },
            ]
        else:
            # Default routes for other countries
            popular_routes = [
                {
                    'origin': origin_airport['code'],
                    'destination': 'CDG',
                    'origin_city': origin_airport['city'],
                    'destination_city': 'Paris',
                    'image_url': 'https://images.unsplash.com/photo-1502602898657-3e91760cbb34?w=500',
                },
                {
                    'origin': origin_airport['code'],
                    'destination': 'LHR',
                    'origin_city': origin_airport['city'],
                    'destination_city': 'London',
                    'image_url': 'https://images.unsplash.com/photo-1505761671935-60b3a7427bad?w=500',
                },
            ]
       
        # Get pricing information for each route
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
                    travel_class='ECONOMY',
                    currency=user_currency  # Specify the user's currency
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
                route['error'] = str(e)  # Log error for debugging
        
        # Include user's info in response
        response_data = {
            'user_country': user_country,
            'user_currency': user_currency,
            'device_type': self.get_device_type(request),
            'routes': popular_routes
        }
       
        return Response(response_data)
    
    def get_location_info_from_ip(self, ip):
        """Get country code and currency from IP address"""
        default_info = {
            'country_code': 'FR',
            'currency': 'EUR',
            'country_name': 'France'
        }
        
        if not ip or ip == '127.0.0.1':
            return default_info
            
        try:
            # Using a free IP geolocation API
            response = requests.get(f'https://ipapi.co/{ip}/json/')
            if response.status_code == 200:
                data = response.json()
                return {
                    'country_code': data.get('country_code', default_info['country_code']),
                    'currency': data.get('currency', default_info['currency']),
                    'country_name': data.get('country_name', default_info['country_name'])
                }
        except Exception:
            pass
            
        return default_info
    
    def get_device_type(self, request):
        """Determine device type from user agent"""
        user_agent = request.META.get('HTTP_USER_AGENT', '').lower()
        
        if 'mobile' in user_agent or 'android' in user_agent or 'iphone' in user_agent:
            return 'mobile'
        elif 'tablet' in user_agent or 'ipad' in user_agent:
            return 'tablet'
        else:
            return 'desktop'

   

class AirportListView(generics.ListAPIView):
    queryset = Airport.objects.all()
    serializer_class = AirportSerializer
    permission_classes = [permissions.AllowAny]
    filterset_fields = ['city', 'country']
    search_fields = ['code', 'name', 'city', 'country']

class FeaturedDestinationsView(generics.ListAPIView):
    queryset = FeaturedDestination.objects.filter(is_active=True)
    serializer_class = FeaturedDestinationSerializer
    permission_classes = [permissions.AllowAny]

class RandomDestinationsView(views.APIView):
    permission_classes = [permissions.AllowAny]
    
    def get(self, request):
        # Sélectionner des destinations aléatoires à partir des destinations caractérisées
        featured = list(FeaturedDestination.objects.filter(is_active=True))
        random_destinations = []
        
        if featured:
            # Prendre au maximum 6 destinations aléatoires
            random_count = min(6, len(featured))
            random_destinations = random.sample(featured, random_count)
        
        serializer = FeaturedDestinationSerializer(random_destinations, many=True)
        return Response(serializer.data)

class FlightSearchView(views.APIView):
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
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
            return Response({"error": "Aucun vol trouvé."}, status=404)
        
        return Response(serializer.errors, status=400)

class MultiCityFlightSearchView(views.APIView):
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        serializer = MultiCityFlightSearchSerializer(data=request.data)
        if serializer.is_valid():
            # Pour l'instant, nous retournons une réponse d'erreur car l'API Amadeus
            # nécessite une configuration plus avancée pour les recherches multi-destination
            return Response({"error": "La recherche multi-destination n'est pas encore implémentée."}, status=501)
        
        return Response(serializer.errors, status=400)