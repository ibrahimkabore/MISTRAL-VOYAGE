import random
from rest_framework import views, generics, permissions, status
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
    # Devise par défaut pour les prix
    DEFAULT_CURRENCY = 'EUR'
   
    def get(self, request):
        tomorrow = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')
        
        # Récupérer la localisation de l'utilisateur
        user_country = self.get_user_country(request)
        
        # Déterminer la devise locale de l'utilisateur en fonction de son pays
        user_currency = self.get_currency_by_country(user_country)
        
        # Obtenir les routes populaires en fonction du pays de l'utilisateur
        popular_routes = self.get_popular_routes_by_country(user_country)
        
        # Obtenir les informations de prix pour chaque route
        self.enrich_routes_with_pricing(popular_routes, tomorrow, user_currency)
        
        return Response({
            'routes': popular_routes,
            'user_country': user_country,
            'user_currency': user_currency
        })
    
    def enrich_routes_with_pricing(self, routes, departure_date, user_currency, adults=1):
        """
        Enrichit les routes avec les informations de prix depuis Amadeus.
        Convertit les prix dans la devise de l'utilisateur.
        """
        amadeus = AmadeusAPI()
        exchange_rates = self.get_exchange_rates()
        
        for route in routes:
            try:
                # Clé de cache pour éviter des requêtes répétées
                cache_key = f"flight_{route['origin']}_{route['destination']}_{departure_date}_{adults}"
                cached_result = self.get_cached_price(cache_key)
                
                if cached_result:
                    original_price = float(cached_result['price'])
                    original_currency = cached_result['currency']
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
                        original_price = float(flight_offers[0]['price']['total'])
                        original_currency = flight_offers[0]['price']['currency']
                        
                        # Mettre en cache pour les requêtes futures
                        self.cache_price(cache_key, {
                            'price': original_price,
                            'currency': original_currency
                        })
                    else:
                        route['price'] = None
                        route['currency'] = None
                        continue
                
                # Convertir le prix dans la devise de l'utilisateur
                if original_currency != user_currency:
                    converted_price = self.convert_currency(
                        amount=original_price,
                        from_currency=original_currency,
                        to_currency=user_currency,
                        exchange_rates=exchange_rates
                    )
                    route['price'] = f"{converted_price:.2f}"
                else:
                    route['price'] = f"{original_price:.2f}"
                
                route['original_price'] = f"{original_price:.2f}"
                route['original_currency'] = original_currency
                route['currency'] = user_currency
                
            except Exception as e:
                logger.error(f"Erreur lors de la récupération des prix: {e}")
                route['price'] = None
                route['currency'] = None
    
    def get_currency_by_country(self, country_code):
        """
        Détermine la devise locale en fonction du code pays.
        """
        # Mapping des pays aux devises
        country_to_currency = {
            # Europe
            'FR': 'EUR', 'DE': 'EUR', 'IT': 'EUR', 'ES': 'EUR', 'NL': 'EUR',
            'BE': 'EUR', 'AT': 'EUR', 'GR': 'EUR', 'IE': 'EUR', 'PT': 'EUR',
            'FI': 'EUR', 'SK': 'EUR', 'SI': 'EUR', 'LV': 'EUR', 'LT': 'EUR',
            'EE': 'EUR', 'CY': 'EUR', 'MT': 'EUR', 'LU': 'EUR',
            # Royaume-Uni
            'UK': 'GBP', 'GB': 'GBP',
            # USA et dollars
            'US': 'USD', 'EC': 'USD', 'SV': 'USD',
            # Afrique
            'CI': 'XOF', 'BJ': 'XOF', 'BF': 'XOF', 'GW': 'XOF', 'ML': 'XOF',
            'NE': 'XOF', 'SN': 'XOF', 'TG': 'XOF',
            'CM': 'XAF', 'CF': 'XAF', 'TD': 'XAF', 'CG': 'XAF', 'GQ': 'XAF', 'GA': 'XAF',
            'MA': 'MAD', 'DZ': 'DZD', 'TN': 'TND', 'EG': 'EGP',
            'NG': 'NGN', 'GH': 'GHS', 'KE': 'KES', 'ZA': 'ZAR',
            # Asie
            'JP': 'JPY', 'CN': 'CNY', 'HK': 'HKD', 'SG': 'SGD', 'TH': 'THB',
            'IN': 'INR', 'AE': 'AED', 'SA': 'SAR', 'QA': 'QAR',
            # Océanie
            'AU': 'AUD', 'NZ': 'NZD'
        }
        
        return country_to_currency.get(country_code, self.DEFAULT_CURRENCY)
    
    def get_exchange_rates(self):
        """
        Récupère les taux de change actuels depuis une API externe ou un cache.
        """
        try:
            # Vérifier d'abord si les taux sont en cache
            cached_rates = self.get_cached_exchange_rates()
            if cached_rates:
                return cached_rates
            
            # Si pas en cache, récupérer à partir d'une API (exemple avec exchangerate-api.com)
            response = requests.get(
                'https://api.exchangerate-api.com/v4/latest/EUR',
                timeout=self.REQUEST_TIMEOUT
            )
            
            if response.status_code == 200:
                data = response.json()
                # Mettre en cache pour éviter trop de requêtes
                self.cache_exchange_rates(data['rates'])
                return data['rates']
            else:
                logger.warning(f"Échec de récupération des taux de change: {response.status_code}")
                # Retourner des taux par défaut si l'API échoue
                return self.get_default_exchange_rates()
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des taux de change: {e}")
            return self.get_default_exchange_rates()
    
    def get_default_exchange_rates(self):
        """
        Taux de change par défaut en cas d'échec de l'API.
        Ces taux doivent être mis à jour régulièrement.
        """
        return {
            'EUR': 1.0,
            'USD': 1.09,
            'GBP': 0.86,
            'JPY': 160.23,
            'CHF': 0.98,
            'CAD': 1.47,
            'AUD': 1.64,
            'CNY': 7.83,
            'HKD': 8.52,
            'XOF': 655.957,  # Franc CFA (UEMOA)
            'XAF': 655.957,  # Franc CFA (CEMAC)
            'MAD': 10.91,
            'NGN': 1630.92,
            'ZAR': 20.11,
            'AED': 4.01,
            'INR': 90.84
        }
    
    def convert_currency(self, amount, from_currency, to_currency, exchange_rates):
        """
        Convertit un montant d'une devise à une autre en utilisant les taux de change fournis.
        """
        if from_currency == to_currency:
            return amount
        
        # Tous les taux sont basés sur l'EUR dans cet exemple
        if from_currency == 'EUR':
            # Conversion directe de EUR vers la devise cible
            return amount * exchange_rates.get(to_currency, 1.0)
        elif to_currency == 'EUR':
            # Conversion de la devise source vers EUR
            return amount / exchange_rates.get(from_currency, 1.0)
        else:
            # Conversion via EUR comme devise intermédiaire
            eur_amount = amount / exchange_rates.get(from_currency, 1.0)
            return eur_amount * exchange_rates.get(to_currency, 1.0)
    
    def get_cached_exchange_rates(self):
        """
        Récupère les taux de change du cache. À implémenter avec votre système de cache.
        """
        # Implémentation à adapter avec votre système de cache
        # from django.core.cache import cache
        # return cache.get('exchange_rates')
        return None
    
    def cache_exchange_rates(self, rates, timeout=86400):  # 24 heures
        """
        Met en cache les taux de change. À implémenter avec votre système de cache.
        """
        # Implémentation à adapter avec votre système de cache
        # from django.core.cache import cache
        # cache.set('exchange_rates', rates, timeout)
        pass
    
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
        
        # Méthode 2: Utiliser un paramètre de requête pour la devise s'il est fourni
        currency_param = request.query_params.get('currency')
        if currency_param:
            for country, currency in self.get_currency_by_country_mapping().items():
                if currency == currency_param.upper():
                    return country
            
        # Méthode 3: Géolocalisation basée sur l'IP
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
            
        # Méthode 4: Valeur par défaut
        return self.DEFAULT_COUNTRY
    
    def get_currency_by_country_mapping(self):
        """
        Retourne un mapping inversé pays -> devise pour la recherche par devise
        """
        # Ce mapping est l'inverse de celui dans get_currency_by_country
        # Pour simplifier, je renvoie un sous-ensemble
        return {
            'FR': 'EUR', 'DE': 'EUR', 'US': 'USD', 'UK': 'GBP', 
            'CI': 'XOF', 'JP': 'JPY', 'ZA': 'ZAR'
        }
    
    def get_client_ip(self, request):
        """Récupère l'adresse IP du client."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
    
    # Le reste du code est identique à la version précédente...
    # Inclure ici get_popular_routes_by_country, get_main_airport_by_country, 
    # get_region_by_country, get_popular_destinations_by_region...

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

from rest_framework import views, permissions, status
from rest_framework.response import Response
from rest_framework.decorators import api_view, permission_classes
from django.shortcuts import get_object_or_404
from django.utils import timezone
import random
import logging

from .models import FlightOffer, Airport
from bookings.models import Booking, Passenger
from .serializers import (
    FlightSearchSerializer, 
    MultiCityFlightSearchSerializer,
    BookingSerializer
)
 
logger = logging.getLogger(__name__)

class FlightSearchView(views.APIView):
    permission_classes = [permissions.AllowAny]
   
    def post(self, request):
        serializer = FlightSearchSerializer(data=request.data)
        if serializer.is_valid():
            amadeus = AmadeusAPI()
            
            # Récupérer les codes IATA
            origin_code = serializer.validated_data['origin']
            destination_code = serializer.validated_data['destination']
            
            # Récupérer les détails des aéroports
            origin_details = self.get_airport_details(origin_code)
            print(origin_details)
            destination_details = self.get_airport_details(destination_code)
            print(destination_details)
           
            flight_offers = amadeus.search_flights(
                origin=origin_code,
                destination=destination_code,
                departure_date=serializer.validated_data['departure_date'].strftime('%Y-%m-%d'),
                return_date=serializer.validated_data.get('return_date', None).strftime('%Y-%m-%d') if serializer.validated_data.get('return_date') else None,
                adults=serializer.validated_data['adults'],
                children=serializer.validated_data['children'],
                infants=serializer.validated_data.get('infants', 0),
                travel_class=serializer.validated_data['travel_class'],
                currency_code=serializer.validated_data['currency_code']
            )
           
            if flight_offers:
                # Ajouter les détails d'aéroports à la réponse
                enhanced_response = {
                    "origin": origin_details,
                    "destination": destination_details,
                    "flight_offers": flight_offers,
                }
                print(enhanced_response)
                return Response(enhanced_response)
            return Response({"error": "Aucun vol trouvé."}, status=404)
       
        return Response(serializer.errors, status=400)
    
    def get_airport_details(self, iata_code):
        """
        Récupère les détails d'un aéroport via l'API Amadeus
        """
        try:
            amadeus = AmadeusAPI()
            response = amadeus.client.reference_data.locations.get(
                keyword=iata_code,
                subType=["AIRPORT"]
            )
            
            if response.data and len(response.data) > 0:
                airport = response.data[0]
                return {
                    'code': airport.get('iataCode'),
                    'name': airport.get('name'),
                    'city': airport.get('address', {}).get('cityName'),
                    'country': airport.get('address', {}).get('countryName')
                }
            return {'code': iata_code, 'name': f"Aéroport {iata_code}"}
        
        except Exception as e:
            logger.error(f"Erreur lors de la récupération des détails d'aéroport: {str(e)}")
            return {'code': iata_code, 'name': f"Aéroport {iata_code}"}


class MultiCityFlightSearchView(views.APIView):
    permission_classes = [permissions.AllowAny]
   
    def post(self, request):
        serializer = MultiCityFlightSearchSerializer(data=request.data)
        if serializer.is_valid():
            # Récupérer les données validées
            validated_data = serializer.validated_data
            segments = validated_data.get('segments', [])
            adults = validated_data.get('adults', 1)
            children = validated_data.get('children', 0)
            infants = validated_data.get('infants', 0)
            travel_class = validated_data.get('travel_class', 'ECONOMY')
            currency_code = serializer.validated_data['currency_code']
            # Vérifier qu'il y a au moins 2 segments pour un itinéraire multi-city
            if len(segments) < 2:
                return Response(
                    {"error": "Au moins 2 segments sont nécessaires pour une recherche multi-destination."},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Formater les segments pour l'API Amadeus et convertir les dates en chaînes de caractères
            formatted_segments = []
            for segment in segments:
                formatted_segments.append({
                    'origin': segment['origin'],
                    'destination': segment['destination'],
                    'date': segment['departure_date'].strftime('%Y-%m-%d')  # Convertir la date en chaîne de caractères
                })
            
            # Effectuer la recherche multi-city via l'API Amadeus
            amadeus_api = AmadeusAPI()
            results = amadeus_api.search_multi_city_flights(
                segments=formatted_segments,
                adults=adults,
                children=children,
                infants=infants,
                travel_class=travel_class,
                currency_code=currency_code
            )
            
            if results is None:
                return Response(
                    {"error": "Une erreur s'est produite lors de la recherche. Veuillez réessayer plus tard."},
                    status=status.HTTP_503_SERVICE_UNAVAILABLE
                )
            
            return Response(results, status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class FlightBookingView(views.APIView):
    #permission_classes = [permissions.IsAuthenticated]
    
    def post(self, request):
        """
        Créer une réservation de vol
        """

        if request.user.is_anonymous:
            return Response(
                {"error": "Vous devez être connecté pour effectuer une réservation."},
                status=status.HTTP_401_UNAUTHORIZED
            )
        
        try:
            # Récupération des données du vol
            flight_data = request.data.get('flight_data', {})
            
            if not flight_data:
                return Response({"error": "Données de vol manquantes"}, status=status.HTTP_400_BAD_REQUEST)
            
            # On vérifie si le vol existe déjà en base ou on le crée
            amadeus_id = flight_data.get('id')
            
            try:
                # Récupération ou création des objets Airport
                origin_code = flight_data.get('origin', {}).get('code')
                destination_code = flight_data.get('destination', {}).get('code')
                
                origin_airport, _ = Airport.objects.get_or_create(
                    code=origin_code,
                    defaults={
                        'name': flight_data.get('origin', {}).get('name', f'Aéroport {origin_code}'),
                        'city': flight_data.get('origin', {}).get('city', ''),
                        'country': flight_data.get('origin', {}).get('country', '')
                    }
                )
                
                destination_airport, _ = Airport.objects.get_or_create(
                    code=destination_code,
                    defaults={
                        'name': flight_data.get('destination', {}).get('name', f'Aéroport {destination_code}'),
                        'city': flight_data.get('destination', {}).get('city', ''),
                        'country': flight_data.get('destination', {}).get('country', '')
                    }
                )
                
                # Récupération ou création de l'offre de vol
                flight_offer, created = FlightOffer.objects.get_or_create(
                    amadeus_id=amadeus_id,
                    defaults={
                        'origin': origin_airport,
                        'destination': destination_airport,
                        'departure_date': flight_data.get('departure_date'),
                        'arrival_date': flight_data.get('arrival_date', flight_data.get('departure_date')),  # Fallback si non fourni
                        'return_departure_date': flight_data.get('return_departure_date'),
                        'return_arrival_date': flight_data.get('return_arrival_date'),
                        'price': flight_data.get('price', 0),
                        'currency': flight_data.get('currency', 'EUR'),
                        'flight_number': flight_data.get('flight_number', 'N/A'),
                        'airline': flight_data.get('airline', 'N/A'),
                        'travel_class': flight_data.get('travel_class', 'ECONOMY'),
                        'is_round_trip': flight_data.get('return_departure_date') is not None,
                        'available_seats': flight_data.get('available_seats', 0),
                        'raw_data': flight_data
                    }
                )
                
            except Exception as e:
                logger.error(f"Erreur lors de la création de l'offre de vol: {str(e)}")
                return Response(
                    {"error": f"Erreur lors de la création de l'offre de vol: {str(e)}"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Récupération des données des passagers
            passengers_data = request.data.get('passengers', [])
            
            if not passengers_data:
                return Response({"error": "Données des passagers manquantes"}, status=status.HTTP_400_BAD_REQUEST)
            
            # Création de la réservation
            booking = Booking(
                user=request.user,
                flight_offer=flight_offer,
                status='PENDING',
                total_price=flight_data.get('price', 0),
                contact_email=request.data.get('contact_email', request.user.email),
                contact_phone=request.data.get('contact_phone', '')
            )
            booking.save()  # Sauvegarde pour générer la référence de réservation
            
            # Création des passagers
            passengers = []
            for passenger_data in passengers_data:
                passenger = Passenger(
                    first_name=passenger_data.get('first_name'),
                    last_name=passenger_data.get('last_name'),
                    date_of_birth=passenger_data.get('date_of_birth'),
                    gender=passenger_data.get('gender'),
                    passport_number=passenger_data.get('passport_number'),
                    passenger_type=passenger_data.get('passenger_type', 'ADULT')
                )
                passengers.append(passenger)
            
            # Création en masse des passagers
            created_passengers = Passenger.objects.bulk_create(passengers)
            
            # Association des passagers à la réservation
            booking.passengers.add(*created_passengers)
            
            # Si méthode de paiement spécifiée
            payment_method = request.data.get('payment_method')
            if payment_method:
                booking.payment_method = payment_method
                
                # Si c'est un paiement en agence, enregistrer la date du rendez-vous
                if payment_method == 'OFFICE':
                    appointment_date = request.data.get('appointment_date')
                    if appointment_date:
                        booking.office_appointment_date = appointment_date
                booking.save()
            
            # Envoi d'un email de confirmation (à implémenter)
            try:
                self.send_booking_confirmation_email(booking, created_passengers)
            except Exception as e:
                logger.error(f"Erreur lors de l'envoi de l'email de confirmation: {str(e)}")
            
            # Retourner les détails de la réservation
            serializer = BookingSerializer(booking)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            logger.error(f"Erreur lors de la création de la réservation: {str(e)}")
            return Response(
                {"error": f"Une erreur est survenue lors de la réservation: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def send_booking_confirmation_email(self, booking, passengers):
        """
        Envoie un email de confirmation de réservation
        """
        # À implémenter selon votre configuration d'envoi d'emails
        pass


class BookingDetailView(views.APIView):
    permission_classes = [permissions.IsAuthenticated]
    
    def get(self, request, booking_reference):
        """
        Récupérer les détails d'une réservation
        """
        try:
            booking = get_object_or_404(Booking, booking_reference=booking_reference, user=request.user)
            serializer = BookingSerializer(booking)
            return Response(serializer.data)
        except Exception as e:
            return Response(
                {"error": f"Erreur lors de la récupération de la réservation: {str(e)}"},
                status=status.HTTP_404_NOT_FOUND
            )


class UpdateBookingStatusView(views.APIView):
    permission_classes = [permissions.IsAdminUser]  # Réservé aux administrateurs
    
    def patch(self, request, booking_reference):
        """
        Mettre à jour le statut d'une réservation
        """
        try:
            booking = get_object_or_404(Booking, booking_reference=booking_reference)
            
            new_status = request.data.get('status')
            if not new_status or new_status not in [status[0] for status in Booking.STATUS_CHOICES]:
                return Response(
                    {"error": "Statut invalide"},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            booking.status = new_status
            
            # Si le statut est "PAID", mettre à jour les informations de paiement
            if new_status == 'PAID':
                booking.payment_status = True
                booking.payment_date = timezone.now()
            
            booking.save()
            
            return Response({"message": f"Statut de la réservation mis à jour: {new_status}"})
            
        except Exception as e:
            return Response(
                {"error": f"Erreur lors de la mise à jour du statut: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )