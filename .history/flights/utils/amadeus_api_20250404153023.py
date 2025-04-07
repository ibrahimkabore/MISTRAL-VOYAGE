import logging
import requests
from amadeus import Client, ResponseError
from django.conf import settings
from forex_python.converter import CurrencyRates

logger = logging.getLogger(__name__)

class AmadeusAPI:
    def __init__(self):
        self.client = Client(
            client_id=settings.AMADEUS_CLIENT_ID,
            client_secret=settings.AMADEUS_CLIENT_SECRET
        )
        self.currency_rates = CurrencyRates()
    
    def get_currency_from_ip(self, ip_address):
        """
        Obtient la devise locale en fonction de l'adresse IP
        """
        try:
            # Utilisation d'un service de géolocalisation IP (exemple avec ipapi.co)
            response = requests.get(f"https://ipapi.co/{ip_address}/json/")
            data = response.json()
            
            if 'currency' in data:
                return data['currency']
            return 'XOF'  # Devise par défaut
        except Exception as e:
            logger.error(f"Erreur lors de la détection de la devise: {str(e)}")
            return 'XOF'  # Devise par défaut en cas d'erreur
    
    def convert_price(self, amount, from_currency, to_currency):
        """
        Convertit un montant d'une devise à une autre
        """
        try:
            if from_currency == to_currency:
                return amount
                
            rate = self.currency_rates.get_rate(from_currency, to_currency)
            converted_amount = float(amount) * rate
            return round(converted_amount, 2)
        except Exception as e:
            logger.error(f"Erreur lors de la conversion de devise: {str(e)}")
            return amount  # Retourne le montant original en cas d'erreur
    
    def search_flights(self, origin, destination, departure_date, return_date=None, adults=2, children=2, infants=0, 
                        travel_class='ECONOMY', base_currency='XOF', user_ip=None, user_currency=None):
        """
        Recherche des vols et convertit les prix selon la devise de l'utilisateur
        """
        try:
            # Déterminer la devise de l'utilisateur
            target_currency = base_currency
            
            if user_currency:
                # Utiliser la devise spécifiée manuellement
                target_currency = user_currency
            elif user_ip:
                # Détecter la devise basée sur l'IP
                target_currency = self.get_currency_from_ip(user_ip)
            
            # Paramètres communs pour les deux types de requêtes
            params = {
                'originLocationCode': origin,
                'destinationLocationCode': destination,
                'departureDate': departure_date,
                'adults': adults,
                'children': children,
                'infants': infants,
                'travelClass': travel_class,
                'currencyCode': base_currency,  # Toujours demander en devise de base
                'max': 50
            }
            
            # Ajout du paramètre returnDate pour un aller-retour
            if return_date:
                params['returnDate'] = return_date
                
            # Exécution de la requête avec les paramètres
            response = self.client.shopping.flight_offers_search.get(**params)
            
            # Convertir les prix si nécessaire
            if base_currency != target_currency:
                for flight in response.data:
                    original_price = float(flight['price']['total'])
                    converted_price = self.convert_price(original_price, base_currency, target_currency)
                    
                    # Stocker les deux valeurs
                    flight['price']['original'] = {
                        'amount': original_price,
                        'currency': base_currency
                    }
                    flight['price']['converted'] = {
                        'amount': converted_price,
                        'currency': target_currency
                    }
                    flight['price']['total'] = str(converted_price)
                    flight['price']['currency'] = target_currency
            
            return response.data
        
        except ResponseError as error:
            logger.error(f"Amadeus API error: {error}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error with Amadeus API: {str(e)}")
            return None