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

    def search_flights(self, origin, destination, departure_date, return_date=None, adults=2, children=2, infants=0, travel_class='ECONOMY'):
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
                    currencyCode='XOF',
                    max=50
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
                    currencyCode='XOF',
                    max=50
                )
            
            return response.data
        
        except ResponseError as error:
            logger.error(f"Amadeus API error: {error}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error with Amadeus API: {str(e)}")
            return None