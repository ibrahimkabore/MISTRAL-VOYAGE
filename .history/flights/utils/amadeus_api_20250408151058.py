# import logging
# from amadeus import Client, ResponseError
# from django.conf import settings

# logger = logging.getLogger(__name__)

# class AmadeusAPI:
#     def __init__(self):
#         self.client = Client(
#             client_id=settings.AMADEUS_CLIENT_ID,
#             client_secret=settings.AMADEUS_CLIENT_SECRET
#         )

#     def search_flights(self, origin, destination, departure_date, return_date=None, adults=2, children=2, infants=0, travel_class='ECONOMY', currency_code='ANY'):
#         """
#         Recherche des vols en utilisant l'API Amadeus
#         """
#         try:
#             if return_date:
#                 # Recherche aller-retour
#                 response = self.client.shopping.flight_offers_search.get(
#                     originLocationCode=origin,
#                     destinationLocationCode=destination,
#                     departureDate=departure_date,
#                     returnDate=return_date,
#                     adults=adults,
#                     children=children,
#                     infants=infants,
#                     travelClass=travel_class,
#                     currencyCode=currency_code,
#                     max=100
#                 )
#             else:
#                 # Recherche aller simple
#                 response = self.client.shopping.flight_offers_search.get(
#                     originLocationCode=origin,
#                     destinationLocationCode=destination,
#                     departureDate=departure_date,
#                     adults=adults,
#                     children=children,
#                     infants=infants,
#                     travelClass=travel_class,
#                     currencyCode=currency_code,
#                     max=100
#                 )
            
#             return response.data
        
#         except ResponseError as error:
#             logger.error(f"Amadeus API error: {error}")
#             return None
#         except Exception as e:
#             logger.error(f"Unexpected error with Amadeus API: {str(e)}")
#             return None

import logging
from amadeus import Client, ResponseError
from django.conf import settings
logger = logging.getLogger(__name__)

class AmadeusAPI:
    def __init__(self):
        self.client = Client(
            client_id=settings.AMADEUS_CLIENT_ID,
            client_secret=settings.AMADEUS_CLIENT_SECRET,
            hostname='test' if settings.AMADEUS_ENV == 'test' else 'production'
        )
    
    def search_flights(self, origin, destination, departure_date, return_date=None, adults=2, children=2, infants=0, travel_class='ECONOMY', currency_code='ANY'):
        """
        Recherche des vols en utilisant l'API Amadeus
        """
        try:
            if return_date:
                # Recherche aller-retour
                response = self.client.shopping.flight_offers_search.get(
                    originLocationCode=origin,
                    destinationLocationCode=destination,
                    departureDate=departure_date,
                    returnDate=return_date,
                    adults=adults,
                    children=children,
                    infants=infants,
                    travelClass=travel_class,
                    currencyCode=currency_code,
                    max=100
                )
            else:
                # Recherche aller simple
                response = self.client.shopping.flight_offers_search.get(
                    originLocationCode=origin,
                    destinationLocationCode=destination,
                    departureDate=departure_date,
                    adults=adults,
                    children=children,
                    infants=infants,
                    travelClass=travel_class,
                    currencyCode=currency_code,
                    max=100
                )
           
            return response.data
       
        except ResponseError as error:
            logger.error(f"Amadeus API error: {error}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error with Amadeus API: {str(e)}")
            return None
    
    def search_multi_city_flights(self, segments, adults=2, children=2, infants=0, travel_class='ECONOMY', currency_code='ANY'):
        """
        Recherche des vols avec plusieurs destinations (multi-city) en utilisant l'API Amadeus
        
        Parameters:
        segments -- Liste de dictionnaires au format [
            {'origin': 'PAR', 'destination': 'NYC', 'date': '2025-05-01'},
            {'origin': 'NYC', 'destination': 'MIA', 'date': '2025-05-10'},
            {'origin': 'MIA', 'destination': 'PAR', 'date': '2025-05-20'}
        ]
        """
        try:
            # Préparer les paramètres pour la recherche multi-city
            params = {
                "originDestinations": []
            }
            
            # Ajouter chaque segment à la liste des originDestinations
            for i, segment in enumerate(segments):
                params["originDestinations"].append({
                    "id": str(i+1),
                    "originLocationCode": segment['origin'],
                    "destinationLocationCode": segment['destination'],
                    "departureDateTimeRange": {
                        "date": segment['date']
                    }
                })
            
            # Ajouter les informations sur les voyageurs
            params["travelers"] = []
            for i in range(adults):
                params["travelers"].append({
                    "id": str(i+1),
                    "travelerType": "ADULT"
                })
            
            for i in range(children):
                params["travelers"].append({
                    "id": str(adults+i+1),
                    "travelerType": "CHILD"
                })
                
            for i in range(infants):
                params["travelers"].append({
                    "id": str(adults+children+i+1),
                    "travelerType": "HELD_INFANT"
                })
            
            # Ajouter des paramètres supplémentaires
            params["sources"] = ["GDS"]
            params["searchCriteria"] = {
                "maxFlightOffers": 50,
                "flightFilters": {
                    "cabinRestrictions": [{
                        "cabin": travel_class,
                        "coverage": "MOST_SEGMENTS",
                        "originDestinationIds": ["1"]
                    }]
                }
            }
            
            # Effectuer la recherche avec tous les paramètres
            response = self.client.shopping.flight_offers_search.post(body=params)
            
            return response.data
            
        except ResponseError as error:
            logger.error(f"Amadeus API error in multi-city search: {error}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error with Amadeus API in multi-city search: {str(e)}")
            return None