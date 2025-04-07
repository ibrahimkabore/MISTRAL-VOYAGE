
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

from rest_framework import views, permissions, status
from rest_framework.response import Response
from datetime import datetime, timedelta
import requests

class CountryBasedFlightsView(views.APIView):
    permission_classes = [permissions.AllowAny]
    
    def get(self, request):
        tomorrow = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')
        week_later = (datetime.now() + timedelta(days=7)).strftime('%Y-%m-%d')
        
        # Récupérer le pays de l'utilisateur
        user_country = self.get_user_country(request)
        
        # Trouver le principal aéroport du pays
        main_airport = self.get_main_airport(user_country)
        
        # Obtenir les destinations recommandées pour ce pays/région
        recommended_destinations = self.get_recommended_destinations(user_country, main_airport)
        
        # Récupérer les prix des vols pour ces destinations
        flights_with_prices = self.get_flight_prices(
            main_airport['code'], 
            recommended_destinations, 
            departure_date=tomorrow,
            return_date=week_later
        )
        
        return Response({
            'user_location': {
                'country_code': user_country,
                'country_name': self.get_country_name(user_country),
                'main_airport': main_airport
            },
            'recommended_flights': flights_with_prices
        })
    
    def get_user_country(self, request):
        """
        Détermine le pays de l'utilisateur en utilisant différentes méthodes:
        1. Paramètre de requête (si fourni)
        2. Géolocalisation par IP
        3. Langue du navigateur
        4. Par défaut: 'FR' (France)
        """
        # Méthode 1: Utiliser un paramètre de requête s'il est fourni
        country_param = request.query_params.get('country')
        if country_param:
            return country_param.upper()
        
        # Méthode 2: Géolocalisation basée sur l'IP
        client_ip = self.get_client_ip(request)
        try:
            # Utiliser un service de géolocalisation IP
            response = requests.get(f'https://ipinfo.io/{client_ip}/json')
            if response.status_code == 200:
                data = response.json()
                if 'country' in data and data['country']:
                    return data['country'].upper()
        except Exception as e:
            print(f"Erreur lors de la géolocalisation IP: {e}")
        
        # Méthode 3: Vérifier l'en-tête Accept-Language
        accept_language = request.META.get('HTTP_ACCEPT_LANGUAGE', '')
        if accept_language:
            # Format typique: fr-FR,fr;q=0.9,en-US;q=0.8,en;q=0.7
            languages = accept_language.split(',')
            for lang in languages:
                if '-' in lang:
                    country = lang.split('-')[1].split(';')[0].upper()
                    if len(country) == 2:  # Code pays ISO à 2 lettres
                        return country
        
        # Méthode 4: Valeur par défaut
        return 'FR'
    
    def get_client_ip(self, request):
        """Récupère l'adresse IP du client."""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = request.META.get('REMOTE_ADDR')
        return ip
    
    def get_country_name(self, country_code):
        """Renvoie le nom du pays à partir du code ISO."""
        country_names = {
            'FR': 'France',
            'US': 'États-Unis',
            'GB': 'Royaume-Uni',
            'DE': 'Allemagne',
            'ES': 'Espagne',
            'IT': 'Italie',
            'CA': 'Canada',
            'JP': 'Japon',
            'CN': 'Chine',
            'AU': 'Australie',
            'BR': 'Brésil',
            'MX': 'Mexique',
            'IN': 'Inde',
            'RU': 'Russie',
            # Ajoutez d'autres pays selon vos besoins
        }
        return country_names.get(country_code, f"Pays ({country_code})")
    
    def get_main_airport(self, country_code):
        """
        Renvoie le principal aéroport du pays spécifié.
        """
        # Mapping des pays vers leurs principaux aéroports
        country_airports = {
            'FR': {'code': 'CDG', 'name': 'Paris Charles de Gaulle', 'city': 'Paris'},
            'US': {'code': 'JFK', 'name': 'New York John F. Kennedy', 'city': 'New York'},
            'GB': {'code': 'LHR', 'name': 'London Heathrow', 'city': 'Londres'},
            'DE': {'code': 'FRA', 'name': 'Frankfurt am Main', 'city': 'Francfort'},
            'ES': {'code': 'MAD', 'name': 'Madrid Barajas', 'city': 'Madrid'},
            'IT': {'code': 'FCO', 'name': 'Rome Fiumicino', 'city': 'Rome'},
            'CA': {'code': 'YYZ', 'name': 'Toronto Pearson', 'city': 'Toronto'},
            'JP': {'code': 'NRT', 'name': 'Tokyo Narita', 'city': 'Tokyo'},
            'CN': {'code': 'PEK', 'name': 'Beijing Capital', 'city': 'Pékin'},
            'AU': {'code': 'SYD', 'name': 'Sydney Kingsford Smith', 'city': 'Sydney'},
            'BR': {'code': 'GRU', 'name': 'São Paulo Guarulhos', 'city': 'São Paulo'},
            'MX': {'code': 'MEX', 'name': 'Mexico City International', 'city': 'Mexico'},
            'IN': {'code': 'DEL', 'name': 'Delhi Indira Gandhi', 'city': 'Delhi'},
            'RU': {'code': 'SVO', 'name': 'Moscow Sheremetyevo', 'city': 'Moscou'},
            # Ajoutez d'autres pays/aéroports selon vos besoins
        }
        
        # Renvoyer l'aéroport du pays ou un aéroport par défaut (Paris CDG)
        return country_airports.get(country_code, country_airports['FR'])
    
    def get_region_by_country(self, country_code):
        """
        Détermine la région du monde en fonction du code pays.
        """
        # Mapping des pays aux régions
        regions = {
            'Europe': ['FR', 'GB', 'DE', 'ES', 'IT', 'NL', 'BE', 'CH', 'AT', 'SE', 'DK', 'NO', 'FI', 'PT', 'GR', 'IE', 'PL', 'CZ', 'HU', 'RO'],
            'Amérique du Nord': ['US', 'CA', 'MX'],
            'Amérique du Sud': ['BR', 'AR', 'CL', 'CO', 'PE', 'VE'],
            'Asie': ['JP', 'CN', 'IN', 'KR', 'SG', 'TH', 'MY', 'ID', 'VN', 'PH', 'HK'],
            'Moyen-Orient': ['AE', 'SA', 'QA', 'IL', 'TR', 'EG'],
            'Océanie': ['AU', 'NZ', 'FJ'],
            'Afrique': ['ZA', 'MA', 'EG', 'TN', 'KE', 'NG', 'GH']
        }
        
        # Trouver la région du pays
        for region, countries in regions.items():
            if country_code in countries:
                return region
        
        return 'Europe'  # Par défaut
    
    def get_recommended_destinations(self, country_code, origin_airport):
        """
        Renvoie une liste de destinations recommandées en fonction du pays d'origine.
        """
        # Obtenir la région du pays
        region = self.get_region_by_country(country_code)
        
        # Destinations populaires par région d'origine
        destinations_by_region = {
            'Europe': [
                {'code': 'JFK', 'city': 'New York', 'country': 'États-Unis', 'image': 'https://images.unsplash.com/photo-1496442226666-8d4d0e62e6e9?w=500'},
                {'code': 'DXB', 'city': 'Dubai', 'country': 'Émirats arabes unis', 'image': 'https://images.unsplash.com/photo-1512453979798-5ea266f8880c?w=500'},
                {'code': 'BKK', 'city': 'Bangkok', 'country': 'Thaïlande', 'image': 'https://images.unsplash.com/photo-1508009603885-50cf7c8dd0d5?w=500'},
                {'code': 'SYD', 'city': 'Sydney', 'country': 'Australie', 'image': 'https://images.unsplash.com/photo-1506973035872-a4ec16b8e8d9?w=500'},
                {'code': 'TYO', 'city': 'Tokyo', 'country': 'Japon', 'image': 'https://images.unsplash.com/photo-1540959733332-eab4deabeeaf?w=500'}
            ],
            'Amérique du Nord': [
                {'code': 'CDG', 'city': 'Paris', 'country': 'France', 'image': 'https://images.unsplash.com/photo-1502602898657-3e91760cbb34?w=500'},
                {'code': 'CUN', 'city': 'Cancun', 'country': 'Mexique', 'image': 'https://images.unsplash.com/photo-1552074284-5e84a731c7ca?w=500'},
                {'code': 'LAS', 'city': 'Las Vegas', 'country': 'États-Unis', 'image': 'https://images.unsplash.com/photo-1581351721010-8cf859cb14a4?w=500'},
                {'code': 'HNL', 'city': 'Honolulu', 'country': 'États-Unis', 'image': 'https://images.unsplash.com/photo-1573990295519-12aa09baed71?w=500'},
                {'code': 'LHR', 'city': 'Londres', 'country': 'Royaume-Uni', 'image': 'https://images.unsplash.com/photo-1505761671935-60b3a7427bad?w=500'}
            ],
            'Asie': [
                {'code': 'CDG', 'city': 'Paris', 'country': 'France', 'image': 'https://images.unsplash.com/photo-1502602898657-3e91760cbb34?w=500'},
                {'code': 'SYD', 'city': 'Sydney', 'country': 'Australie', 'image': 'https://images.unsplash.com/photo-1506973035872-a4ec16b8e8d9?w=500'},
                {'code': 'SIN', 'city': 'Singapour', 'country': 'Singapour', 'image': 'https://images.unsplash.com/photo-1525625293386-3f8f99389edd?w=500'},
                {'code': 'DXB', 'city': 'Dubai', 'country': 'Émirats arabes unis', 'image': 'https://images.unsplash.com/photo-1512453979798-5ea266f8880c?w=500'},
                {'code': 'LHR', 'city': 'Londres', 'country': 'Royaume-Uni', 'image': 'https://images.unsplash.com/photo-1505761671935-60b3a7427bad?w=500'}
            ],
            # Ajoutez d'autres régions selon vos besoins
        }
        
        # Par défaut, utiliser les destinations européennes
        destinations = destinations_by_region.get(region, destinations_by_region['Europe'])
        
        # Filtrer les destinations pour éviter de proposer la ville d'origine comme destination
        filtered_destinations = [
            dest for dest in destinations 
            if dest['code'] != origin_airport['code']
        ]
        
        # Si après filtrage il reste moins de 3 destinations, ajouter des destinations supplémentaires
        if len(filtered_destinations) < 3:
            for region_name, region_destinations in destinations_by_region.items():
                if region_name != region:
                    for dest in region_destinations:
                        if dest['code'] != origin_airport['code'] and dest not in filtered_destinations:
                            filtered_destinations.append(dest)
                            if len(filtered_destinations) >= 5:
                                break
                    if len(filtered_destinations) >= 5:
                        break
        
        return filtered_destinations[:5]  # Limiter à 5 destinations
    
    def get_flight_prices(self, origin_code, destinations, departure_date, return_date=None):
        """
        Obtient les prix pour chaque vol recommandé.
        """
        amadeus = AmadeusAPI()
        flights = []
        
        for dest in destinations:
            flight = {
                'origin': origin_code,
                'destination': dest['code'],
                'destination_city': dest['city'],
                'destination_country': dest['country'],
                'image_url': dest['image'],
                'departure_date': departure_date,
                'return_date': return_date
            }
            
            try:
                flight_offers = amadeus.search_flights(
                    origin=origin_code,
                    destination=dest['code'],
                    departure_date=departure_date,
                    return_date=return_date,
                    adults=1,
                    children=0,
                    infants=0,
                    travel_class='ECONOMY'
                )
                
                if flight_offers and len(flight_offers) > 0:
                    flight['price'] = flight_offers[0]['price']['total']
                    flight['currency'] = flight_offers[0]['price']['currency']
                    
                    # Ajouter des détails de vol si disponibles
                    if 'itineraries' in flight_offers[0] and flight_offers[0]['itineraries']:
                        segments = flight_offers[0]['itineraries'][0]['segments']
                        if segments:
                            flight['departure_time'] = segments[0]['departure']['at']
                            flight['arrival_time'] = segments[-1]['arrival']['at']
                            flight['duration'] = flight_offers[0]['itineraries'][0].get('duration')
                            flight['stops'] = len(segments) - 1
                else:
                    flight['price'] = None
                    flight['currency'] = None
            except Exception as e:
                print(f"Erreur lors de la recherche de vols: {e}")
                flight['price'] = None
                flight['currency'] = None
            
            flights.append(flight)
        
        return flights


class AmadeusAPI:
    """
    Classe factice pour simuler l'API Amadeus.
    Dans une implémentation réelle, cette classe se connecterait à l'API Amadeus.
    """
    def search_flights(self, origin, destination, departure_date, return_date=None, 
                      adults=1, children=0, infants=0, travel_class='ECONOMY'):
        """
        Simule une recherche de vols via l'API Amadeus.
        """
        # Dans une implémentation réelle, ceci ferait un appel API à Amadeus
        
        # Pour démonstration, retournons des données simulées
        import random
        
        # Génération d'une heure de départ aléatoire
        hour = random.randint(6, 22)
        minute = random.randint(0, 55) // 5 * 5  # Arrondi aux 5 minutes
        
        # Calcul de l'heure d'arrivée (vol de 1h30 à 12h selon la distance)
        if origin[0] == destination[0]:  # Même continent (première lettre du code)
            duration_hours = random.randint(1, 4)
        else:
            duration_hours = random.randint(6, 12)
        
        arrival_hour = (hour + duration_hours) % 24
        arrival_minute = minute
        
        # Formatage des heures
        departure_at = f"{departure_date}T{hour:02d}:{minute:02d}:00"
        arrival_at = f"{departure_date}T{arrival_hour:02d}:{arrival_minute:02d}:00"
        
        # Prix en fonction de la distance et de la demande
        base_price = 0
        if origin[0] == destination[0]:  # Même continent
            base_price = random.randint(100, 400)
        else:
            base_price = random.randint(400, 1200)
        
        # Ajuster le prix en fonction de la demande, classe, etc.
        if travel_class == 'BUSINESS':
            base_price *= 2.5
        
        # Données de retour simulées
        return [{
            'price': {
                'total': str(base_price),
                'currency': 'EUR'
            },
            'itineraries': [{
                'duration': f'PT{duration_hours}H{random.randint(0, 59)}M',
                'segments': [{
                    'departure': {
                        'iataCode': origin,
                        'at': departure_at
                    },
                    'arrival': {
                        'iataCode': destination,
                        'at': arrival_at
                    },
                    'carrierCode': 'AF',
                    'number': str(random.randint(1000, 9999)),
                    'duration': f'PT{duration_hours}H{random.randint(0, 59)}M'
                }]
            }]
        }]


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
            'CI': [
                {'code': 'YCC', 'city': 'Yamoussoukro', 'image': 'https://images.unsplash.com/photo-1506973035872-a4ec16b8e8d9?w=500'},
                {'code': 'ABJ', 'city': 'Abidjan', 'image': 'https://images.unsplash.com/photo-1502602898657-3e91760cbb34?w=500'},
                {'code': 'BYK', 'city': 'Bouake', 'image': 'https://images.unsplash.com/photo-1505761671935-60b3a7427bad?w=500'},
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
                'price': None,
                'currency': None
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