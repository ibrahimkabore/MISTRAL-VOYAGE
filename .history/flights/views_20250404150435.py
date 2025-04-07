
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

 
import logging
from datetime import datetime, timedelta
import requests
from rest_framework import views, permissions
from rest_framework.response import Response

logger = logging.getLogger(__name__)

class PopularRoutesView(views.APIView):
    permission_classes = [permissions.AllowAny]
    # Délai d'expiration pour les requêtes externes en secondes
    REQUEST_TIMEOUT = 3
    # Valeur par défaut pour le pays
    DEFAULT_COUNTRY = 'CI'
   
    def get(self, request):
        tomorrow = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')
        
        # Récupérer la localisation de l'utilisateur
        user_country = self.get_user_country(request)
        
        # Obtenir les routes populaires en fonction du pays de l'utilisateur
        popular_routes = self.get_popular_routes_by_country(user_country)
        
        # Obtenir les informations de prix pour chaque route
        self.enrich_routes_with_pricing(popular_routes, tomorrow)
        
        return Response(popular_routes)
    
    def enrich_routes_with_pricing(self, routes, departure_date, adults=1):
        """
        Enrichit les routes avec les informations de prix depuis Amadeus.
        Séparé pour une meilleure lisibilité et maintenance.
        """
        amadeus = AmadeusAPI()
        for route in routes:
            try:
                # Clé de cache pour éviter des requêtes répétées
                cache_key = f"flight_{route['origin']}_{route['destination']}_{departure_date}_{adults}"
                cached_result = self.get_cached_price(cache_key)
                
                if cached_result:
                    route['price'] = cached_result['price']
                    route['currency'] = cached_result['currency']
                else:
                    flight_offers = amadeus.search_flights(
                        origin=route['origin'],
                        destination=route['destination'],
                        departure_date=departure_date,
                        return_date=None,
                        adults=adults,
                        children=0,
                        infants=0,
                        travel_class='ECONOMY'
                    )
                   
                    if flight_offers and len(flight_offers) > 0:
                        route['price'] = flight_offers[0]['price']['total']
                        route['currency'] = flight_offers[0]['price']['currency']
                        
                        # Mettre en cache pour les requêtes futures
                        self.cache_price(cache_key, {
                            'price': route['price'],
                            'currency': route['currency']
                        })
                    else:
                        route['price'] = None
                        route['currency'] = None
            except Exception as e:
                logger.error(f"Erreur lors de la récupération des prix: {e}")
                route['price'] = None
                route['currency'] = None
    
    def get_cached_price(self, key):
        """
        Récupère les prix mis en cache. À implémenter avec Redis, Memcached, ou autre.
        """
        # Implémentation simplifiée - à remplacer par votre système de cache
        # Exemple avec django.core.cache
        # from django.core.cache import cache
        # return cache.get(key)
        return None
    
    def cache_price(self, key, data, timeout=3600):
        """
        Met en cache les informations de prix. À implémenter avec Redis, Memcached, ou autre.
        """
        # Implémentation simplifiée - à remplacer par votre système de cache
        # Exemple avec django.core.cache
        # from django.core.cache import cache
        # cache.set(key, data, timeout)
        pass
    
    def get_user_country(self, request):
        """
        Détermine le pays de l'utilisateur en utilisant différentes méthodes:
        1. Paramètre de requête (si fourni)
        2. Géolocalisation par IP
        3. Par défaut: 'CI' (Côte d'Ivoire)
        """
        # Méthode 1: Utiliser un paramètre de requête s'il est fourni
        country_param = request.query_params.get('country')
        if country_param:
            return country_param.upper()
            
        # Méthode 2: Géolocalisation basée sur l'IP
        client_ip = self.get_client_ip(request)
        try:
            # Utiliser un service de géolocalisation IP avec timeout
            response = requests.get(
                f'https://ipinfo.io/{client_ip}/json', 
                timeout=self.REQUEST_TIMEOUT
            )
            if response.status_code == 200:
                data = response.json()
                country = data.get('country')
                if country:
                    logger.info(f"Pays détecté via IP: {country}")
                    return country
        except requests.Timeout:
            logger.warning("Timeout lors de la requête de géolocalisation IP")
        except Exception as e:
            logger.warning(f"Erreur lors de la géolocalisation IP: {e}")
            
        # Méthode 3: Valeur par défaut
        return self.DEFAULT_COUNTRY
    
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
        # Obtenir l'aéroport d'origine
        origin_airport = self.get_main_airport_by_country(country_code)
        
        # Déterminer la région du pays
        region = self.get_region_by_country(country_code)
        
        # Obtenir les destinations populaires pour cette région
        destinations = self.get_popular_destinations_by_region(region)
        
        # Créer la liste des routes populaires
        routes = []
        for destination in destinations:
            routes.append({
                'origin': origin_airport['code'],
                'destination': destination['code'],
                'origin_city': origin_airport['city'],
                'destination_city': destination['city'],
                'image_url': destination['image'],
                'price': None,
                'currency': None
            })
            
        return routes
    
    def get_main_airport_by_country(self, country_code):
        """
        Renvoie l'aéroport principal pour un pays donné.
        """
        # Dictionnaire étendu des aéroports principaux par pays
        country_airports = {
            'FR': {'code': 'CDG', 'city': 'Paris'},
            'US': {'code': 'JFK', 'city': 'New York'},
            'UK': {'code': 'LHR', 'city': 'London'},
            'DE': {'code': 'FRA', 'city': 'Frankfurt'},
            'ES': {'code': 'MAD', 'city': 'Madrid'},
            'IT': {'code': 'FCO', 'city': 'Rome'},
            'CI': {'code': 'ABJ', 'city': 'Abidjan'},
            'JP': {'code': 'NRT', 'city': 'Tokyo'},
            'CN': {'code': 'PEK', 'city': 'Beijing'},
            'AU': {'code': 'SYD', 'city': 'Sydney'},
            'CA': {'code': 'YYZ', 'city': 'Toronto'},
            'BR': {'code': 'GRU', 'city': 'São Paulo'},
            'IN': {'code': 'DEL', 'city': 'New Delhi'},
            'RU': {'code': 'SVO', 'city': 'Moscow'},
            'ZA': {'code': 'JNB', 'city': 'Johannesburg'},
            'AE': {'code': 'DXB', 'city': 'Dubai'},
            'SG': {'code': 'SIN', 'city': 'Singapore'},
            'NL': {'code': 'AMS', 'city': 'Amsterdam'},
            'MX': {'code': 'MEX', 'city': 'Mexico City'},
            'TH': {'code': 'BKK', 'city': 'Bangkok'},
            # Ajout d'autres pays d'Afrique
            'SN': {'code': 'DSS', 'city': 'Dakar'},
            'CM': {'code': 'DLA', 'city': 'Douala'},
            'MA': {'code': 'CMN', 'city': 'Casablanca'},
            'DZ': {'code': 'ALG', 'city': 'Algiers'},
            'TN': {'code': 'TUN', 'city': 'Tunis'},
            'KE': {'code': 'NBO', 'city': 'Nairobi'},
            'NG': {'code': 'LOS', 'city': 'Lagos'},
            'GH': {'code': 'ACC', 'city': 'Accra'}
        }
        
        # Retourner l'aéroport ou une valeur par défaut pour Abidjan si pas trouvé
        return country_airports.get(country_code, {'code': 'ABJ', 'city': 'Abidjan'})
    
    def get_region_by_country(self, country_code):
        """
        Détermine la région du monde en fonction du code pays.
        """
        # Mapping amélioré des pays aux régions
        regions = {
            'EU': ['FR', 'DE', 'UK', 'ES', 'IT', 'NL', 'BE', 'PT', 'CH', 'AT', 'SE', 'DK', 'NO', 'FI', 'GR', 'IE', 
                   'PL', 'RO', 'HU', 'CZ', 'BG', 'HR', 'LT', 'SI', 'LV', 'EE', 'CY', 'LU', 'MT', 'SK'],
            'US': ['US', 'CA', 'MX', 'BR', 'AR', 'CO', 'CL', 'PE', 'EC', 'VE', 'CR', 'PA', 'DO', 'JM', 'BS'],
            'AS': ['JP', 'CN', 'KR', 'TH', 'SG', 'MY', 'ID', 'IN', 'VN', 'PH', 'HK', 'TW', 'AE', 'SA', 'QA', 'IL', 'TR'],
            'AF': ['ZA', 'EG', 'MA', 'NG', 'KE', 'GH', 'SN', 'CI', 'TN', 'ET', 'DZ', 'CM', 'MU', 'TZ', 'UG'],
            'OC': ['AU', 'NZ', 'FJ', 'PG', 'NC', 'VU', 'SB', 'TO', 'WS']
        }
        
        # Recherche du pays dans les régions
        for region, countries in regions.items():
            if country_code in countries:
                return region
        
        # Si le pays n'est pas trouvé, on retourne 'CI' (pour l'Afrique)
        return 'AF'
    
    def get_popular_destinations_by_region(self, region):
        """
        Renvoie les destinations populaires pour une région donnée.
        """
        # Destinations populaires par région
        popular_destinations = {
            'EU': [
                {'code': 'JFK', 'city': 'New York', 'image': 'https://images.unsplash.com/photo-1496442226666-8d4d0e62e6e9?w=500'},
                {'code': 'DXB', 'city': 'Dubai', 'image': 'https://images.unsplash.com/photo-1512453979798-5ea266f8880c?w=500'},
                {'code': 'BKK', 'city': 'Bangkok', 'image': 'https://images.unsplash.com/photo-1508009603885-50cf7c8dd0d5?w=500'},
                {'code': 'SIN', 'city': 'Singapore', 'image': 'https://images.unsplash.com/photo-1525625293386-3f8f99389edd?w=500'},
                {'code': 'HKG', 'city': 'Hong Kong', 'image': 'https://images.unsplash.com/photo-1576788469213-49654bdf5452?w=500'}
            ],
            'US': [
                {'code': 'CDG', 'city': 'Paris', 'image': 'https://images.unsplash.com/photo-1502602898657-3e91760cbb34?w=500'},
                {'code': 'LHR', 'city': 'London', 'image': 'https://images.unsplash.com/photo-1505761671935-60b3a7427bad?w=500'},
                {'code': 'CUN', 'city': 'Cancun', 'image': 'https://images.unsplash.com/photo-1552074284-5e84a731c7ca?w=500'},
                {'code': 'TYO', 'city': 'Tokyo', 'image': 'https://images.unsplash.com/photo-1540959733332-eab4deabeeaf?w=500'},
                {'code': 'BCN', 'city': 'Barcelona', 'image': 'https://images.unsplash.com/photo-1583422409516-2895a77efded?w=500'}
            ],
            'AS': [
                {'code': 'SYD', 'city': 'Sydney', 'image': 'https://images.unsplash.com/photo-1506973035872-a4ec16b8e8d9?w=500'},
                {'code': 'CDG', 'city': 'Paris', 'image': 'https://images.unsplash.com/photo-1502602898657-3e91760cbb34?w=500'},
                {'code': 'LHR', 'city': 'London', 'image': 'https://images.unsplash.com/photo-1505761671935-60b3a7427bad?w=500'},
                {'code': 'JFK', 'city': 'New York', 'image': 'https://images.unsplash.com/photo-1496442226666-8d4d0e62e6e9?w=500'},
                {'code': 'LAX', 'city': 'Los Angeles', 'image': 'https://images.unsplash.com/photo-1534253893894-10d024888e49?w=500'}
            ],
            'AF': [
                {'code': 'CDG', 'city': 'Paris', 'image': 'https://images.unsplash.com/photo-1502602898657-3e91760cbb34?w=500'},
                {'code': 'LHR', 'city': 'London', 'image': 'https://images.unsplash.com/photo-1505761671935-60b3a7427bad?w=500'},
                {'code': 'DXB', 'city': 'Dubai', 'image': 'https://images.unsplash.com/photo-1512453979798-5ea266f8880c?w=500'},
                {'code': 'JNB', 'city': 'Johannesburg', 'image': 'https://images.unsplash.com/photo-1577948000111-9c970dfe3743?w=500'},
                {'code': 'CPT', 'city': 'Cape Town', 'image': 'https://images.unsplash.com/photo-1580060839134-75a5edca2e99?w=500'}
            ],
            'OC': [
                {'code': 'LAX', 'city': 'Los Angeles', 'image': 'https://images.unsplash.com/photo-1534253893894-10d024888e49?w=500'},
                {'code': 'TYO', 'city': 'Tokyo', 'image': 'https://images.unsplash.com/photo-1540959733332-eab4deabeeaf?w=500'},
                {'code': 'SIN', 'city': 'Singapore', 'image': 'https://images.unsplash.com/photo-1525625293386-3f8f99389edd?w=500'},
                {'code': 'LHR', 'city': 'London', 'image': 'https://images.unsplash.com/photo-1505761671935-60b3a7427bad?w=500'},
                {'code': 'HKG', 'city': 'Hong Kong', 'image': 'https://images.unsplash.com/photo-1576788469213-49654bdf5452?w=500'}
            ],
            # Si aucune région correspondante n'est trouvée, utiliser ces destinations par défaut
            'default': [
                {'code': 'CDG', 'city': 'Paris', 'image': 'https://images.unsplash.com/photo-1502602898657-3e91760cbb34?w=500'},
                {'code': 'LHR', 'city': 'London', 'image': 'https://images.unsplash.com/photo-1505761671935-60b3a7427bad?w=500'},
                {'code': 'JFK', 'city': 'New York', 'image': 'https://images.unsplash.com/photo-1496442226666-8d4d0e62e6e9?w=500'},
                {'code': 'DXB', 'city': 'Dubai', 'image': 'https://images.unsplash.com/photo-1512453979798-5ea266f8880c?w=500'},
                {'code': 'SYD', 'city': 'Sydney', 'image': 'https://images.unsplash.com/photo-1506973035872-a4ec16b8e8d9?w=500'}
            ]
        }
        
        # Renvoyer les destinations pour la région demandée ou une liste par défaut
        return popular_destinations.get(region, popular_destinations['default'])


class AmadeusAPI:
    """
    Classe pour interagir avec l'API Amadeus.
    Dans un projet réel, cette classe devrait être dans un module séparé.
    """
    def __init__(self):
        # Initialiser avec les clés d'API nécessaires
        # self.api_key = settings.AMADEUS_API_KEY
        pass
        
    def search_flights(self, origin, destination, departure_date, return_date=None, 
                       adults=1, children=0, infants=0, travel_class='ECONOMY'):
        """
        Recherche des vols sur l'API Amadeus.
        Renvoie une liste d'offres de vol.
        
        Dans un cas réel, implémenter la connexion à l'API Amadeus ici.
        Pour cet exemple, nous retournons des données simulées.
        """
        try:
            # Simulation d'une réponse d'API pour l'exemple
            # Dans un cas réel, effectuer la requête à l'API Amadeus ici
            import random
            
            # Simulation de prix en fonction des destinations
            base_prices = {
                'JFK': {'base': 800, 'var': 200},
                'LHR': {'base': 250, 'var': 100},
                'CDG': {'base': 220, 'var': 80},
                'BKK': {'base': 700, 'var': 150},
                'DXB': {'base': 500, 'var': 120},
                'SYD': {'base': 1200, 'var': 300},
                'SIN': {'base': 650, 'var': 150},
                'HKG': {'base': 750, 'var': 200},
                'TYO': {'base': 900, 'var': 250},
                'default': {'base': 400, 'var': 100}
            }
            
            dest_data = base_prices.get(destination, base_prices['default'])
            base_price = dest_data['base']
            variation = dest_data['var']
            
            # Prix simulé avec une variation aléatoire
            price = base_price + random.randint(-variation, variation)
            
            # Simulation d'une réponse
            return [{
                'id': f'offer_{origin}_{destination}_{departure_date}',
                'price': {
                    'total': f'{price:.2f}',
                    'currency': 'EUR'
                },
                'itineraries': [
                    {
                        'duration': 'PT3H20M',
                        'segments': [
                            {
                                'departure': {
                                    'iataCode': origin,
                                    'at': f'{departure_date}T10:00:00'
                                },
                                'arrival': {
                                    'iataCode': destination,
                                    'at': f'{departure_date}T13:20:00'
                                },
                                'carrierCode': 'AF',
                                'number': '1234'
                            }
                        ]
                    }
                ]
            }]
        except Exception as e:
            logger.error(f"Erreur lors de la recherche de vols: {e}")
            return []

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