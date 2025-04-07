
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

class PopularRoutesView(views.APIView):
    permission_classes = [permissions.AllowAny]
   
    def get(self, request):
        tomorrow = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')
        
        # Récupérer la localisation de l'utilisateur (IP ou paramètres)
        user_country = self.get_user_country(request)
        
        # Obtenir les routes populaires en fonction du pays de l'utilisateur
        popular_routes = self.get_popular_routes_by_country(user_country)
        
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
                    travel_class='ECONOMY'
                )
               
                if flight_offers and len(flight_offers) > 0:
                    route['price'] = flight_offers[0]['price']['total']
                    route['currency'] = flight_offers[0]['price']['currency']
                else:
                    route['price'] = None
                    route['currency'] = None
            except Exception:
                route['price'] = None
                route['currency'] = None
       
        return Response(popular_routes)
    
    def get_user_country(self, request):
        """
        Détermine le pays de l'utilisateur en utilisant différentes méthodes:
        1. Paramètre de requête (si fourni)
        2. Géolocalisation par IP
        3. Par défaut: 'FR' (France)
        """
        # Méthode 1: Utiliser un paramètre de requête s'il est fourni
        country_param = request.query_params.get('country')
        if country_param:
            return country_param.upper()
            
        # Méthode 2: Géolocalisation basée sur l'IP
        client_ip = self.get_client_ip(request)
        try:
            # Utiliser un service de géolocalisation IP (exemple avec ipinfo.io)
            # Remarque: vous devrez installer et configurer cette bibliothèque
            import requests
            response = requests.get(f'https://ipinfo.io/{client_ip}/json')
            if response.status_code == 200:
                data = response.json()
                return data.get('country', 'CI')
        except Exception:
            pass
            
        # Méthode 3: Valeur par défaut
        return 'FR'
    
    def get_client_ip(self, request):
        """Récupère l'adresse IP du client."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
    
    def get_popular_routes_by_country(self, country_code):
        """
        Renvoie une liste de routes populaires basées sur le pays d'origine.
        """
        # Dictionnaire des aéroports principaux par pays
        country_airports = {
            'FR': {'code': 'CDG', 'city': 'Paris'},
            'US': {'code': 'JFK', 'city': 'New York'},
            'UK': {'code': 'LHR', 'city': 'London'},
            'DE': {'code': 'FRA', 'city': 'Frankfurt'},
            'ES': {'code': 'MAD', 'city': 'Madrid'},
            'IT': {'code': 'FCO', 'city': 'Rome'},
            'CI': {'code': 'CI', 'city': 'Côte d\'Ivoire'},
            # Ajoutez d'autres pays selon vos besoins
        }
        
        # Destinations populaires par région
        popular_destinations = {

            'EU': [
                {'code': 'JFK', 'city': 'New York', 'image': 'https://images.unsplash.com/photo-1496442226666-8d4d0e62e6e9?w=500'},
                {'code': 'DXB', 'city': 'Dubai', 'image': 'https://images.unsplash.com/photo-1512453979798-5ea266f8880c?w=500'},
                {'code': 'BKK', 'city': 'Bangkok', 'image': 'https://images.unsplash.com/photo-1508009603885-50cf7c8dd0d5?w=500'},
            ],
            'US': [
                {'code': 'CDG', 'city': 'Paris', 'image': 'https://images.unsplash.com/photo-1502602898657-3e91760cbb34?w=500'},
                {'code': 'LHR', 'city': 'London', 'image': 'https://images.unsplash.com/photo-1505761671935-60b3a7427bad?w=500'},
                {'code': 'CUN', 'city': 'Cancun', 'image': 'https://images.unsplash.com/photo-1552074284-5e84a731c7ca?w=500'},
            ],
            'AS': [
                {'code': 'SYD', 'city': 'Sydney', 'image': 'https://images.unsplash.com/photo-1506973035872-a4ec16b8e8d9?w=500'},
                {'code': 'CDG', 'city': 'Paris', 'image': 'https://images.unsplash.com/photo-1502602898657-3e91760cbb34?w=500'},
                {'code': 'LHR', 'city': 'London', 'image': 'https://images.unsplash.com/photo-1505761671935-60b3a7427bad?w=500'},
            ],
            # Ajoutez d'autres régions
        }
        
        # Déterminer la région du pays
        region = self.get_region_by_country(country_code)
        
        # Obtenir l'aéroport d'origine (ou utiliser CDG par défaut)
        origin_airport = country_airports.get(country_code, {'code': 'CDG', 'city': 'Paris'})
        
        # Créer la liste des routes populaires
        routes = []
        for destination in popular_destinations.get(region, popular_destinations['CI']):
            routes.append({
                'origin': origin_airport['code'],
                'destination': destination['code'],
                'origin_city': origin_airport['city'],
                'destination_city': destination['city'],
                'image_url': destination['image'],
            })
            
        return routes
    
    def get_region_by_country(self, country_code):
        """
        Détermine la région du monde en fonction du code pays.
        """
        # Mapping simplifié des pays aux régions
        eu_countries = ['FR', 'DE', 'UK', 'ES', 'IT', 'NL', 'BE', 'PT', 'CH', 'AT', 'SE', 'DK', 'NO', 'FI', 'GR', 'IE']
        us_countries = ['US', 'CA', 'MX']
        as_countries = ['JP', 'CN', 'KR', 'TH', 'SG', 'MY', 'ID', 'IN', 'VN', 'PH']
        
        if country_code in eu_countries:
            return 'EU'
        elif country_code in us_countries:
            return 'US'
        elif country_code in as_countries:
            return 'AS'
        else:
            return 'EU'  # Par défaut: traiter comme Europe

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
            return Response({"error": "Aucun vol trouvé ICI."}, status=404)
        
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