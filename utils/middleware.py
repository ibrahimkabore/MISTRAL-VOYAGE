# utils/middleware.py

import logging
from .currency_utils import get_client_ip, get_currency_from_ip

logger = logging.getLogger(__name__)

class CurrencyMiddleware:
    """
    Middleware qui détecte la devise de l'utilisateur en fonction de son adresse IP
    et l'ajoute à la requête pour une utilisation ultérieure.
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        # Obtenir l'adresse IP du client
        ip_address = get_client_ip(request)
        
        # Déterminer la devise en fonction de l'adresse IP
        currency = get_currency_from_ip(ip_address)
        
        # Ajouter la devise à la requête pour une utilisation ultérieure
        request.currency = currency
        
        # Continuer le traitement de la requête
        response = self.get_response(request)
        
        return response