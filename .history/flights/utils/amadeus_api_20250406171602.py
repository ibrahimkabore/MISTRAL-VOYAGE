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
            client_secret=settings.AMADEUS_CLIENT_SECRET
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
            # Préparer les segments de vol pour la requête
            origin_destinations = []
            
            for segment in segments:
                origin_destinations.append({
                    "id": str(len(origin_destinations) + 1),
                    "originLocationCode": segment['origin'],
                    "destinationLocationCode": segment['destination'],
                    "departureDateTimeRange": {
                        "date": segment['date']
                    }
                })
            
            # Configurer la requête pour le voyage multi-city
            response = self.client.shopping.flight_offers_search.post(
                originDestinations=origin_destinations,
                travelers=[
                    {"id": "1", "travelerType": "ADULT"} for _ in range(adults)
                ] + [
                    {"id": str(adults + i + 1), "travelerType": "CHILD"} for i in range(children)
                ] + [
                    {"id": str(adults + children + i + 1), "travelerType": "HELD_INFANT"} for i in range(infants)
                ],
                sources=["GDS"],
                searchCriteria={
                    "maxFlightOffers": 100,
                    "additionalInformation": {
                        "chargeableCheckedBags": True
                    }
                },
                currencyCode=currency_code,
                travelClass=travel_class
            )
            
            return response.data
            
        except ResponseError as error:
            logger.error(f"Amadeus API error in multi-city search: {error}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error with Amadeus API in multi-city search: {str(e)}")
            return None