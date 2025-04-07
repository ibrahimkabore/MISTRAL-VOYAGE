
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
    # Devise par défaut pour les prix
    DEFAULT_CURRENCY = 'EUR'
   
    def get(self, request):
        tomorrow = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')
        
        # Récupérer la localisation de l'utilisateur
        user_country = self.get_user_country(request)
        
        # Déterminer la devise locale de l'utilisateur en fonction de son pays
        user_currency = self.get_currency_by_country(user_country)
        
        # Obtenir les routes populaires en fonction du pays de l'utilisateur
        #popular_routes = self.get_popular_routes_by_country(user_country)
        
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