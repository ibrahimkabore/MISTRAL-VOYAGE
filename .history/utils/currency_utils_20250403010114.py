# utils/currency_utils.py

import os
import logging
import requests
import geoip2.database
from geoip2.errors import AddressNotFoundError
from django.conf import settings

logger = logging.getLogger(__name__)

# Mapping des pays vers leurs devises
COUNTRY_TO_CURRENCY = {
    'US': 'USD',  # États-Unis - Dollar américain
    'GB': 'GBP',  # Royaume-Uni - Livre sterling
    'JP': 'JPY',  # Japon - Yen
    'CN': 'CNY',  # Chine - Yuan
    'CH': 'CHF',  # Suisse - Franc suisse
    'CA': 'CAD',  # Canada - Dollar canadien
    'AU': 'AUD',  # Australie - Dollar australien
    'NZ': 'NZD',  # Nouvelle-Zélande - Dollar néo-zélandais
    'IN': 'INR',  # Inde - Roupie indienne
    'ZA': 'ZAR',  # Afrique du Sud - Rand
    'RU': 'RUB',  # Russie - Rouble
    'BR': 'BRL',  # Brésil - Real
    'MX': 'MXN',  # Mexique - Peso mexicain
    'KR': 'KRW',  # Corée du Sud - Won
    'SG': 'SGD',  # Singapour - Dollar de Singapour
    'HK': 'HKD',  # Hong Kong - Dollar de Hong Kong
    'SE': 'SEK',  # Suède - Couronne suédoise
    'NO': 'NOK',  # Norvège - Couronne norvégienne
    'DK': 'DKK',  # Danemark - Couronne danoise
    'CZ': 'CZK',  # République tchèque - Couronne tchèque
    'HU': 'HUF',  # Hongrie - Forint
    'PL': 'PLN',  # Pologne - Zloty
    'TH': 'THB',  # Thaïlande - Baht
    'ID': 'IDR',  # Indonésie - Roupie indonésienne
    'MY': 'MYR',  # Malaisie - Ringgit
    'PH': 'PHP',  # Philippines - Peso philippin
    'AE': 'AED',  # Émirats arabes unis - Dirham
    'IL': 'ILS',  # Israël - Shekel
    'EG': 'EGP',  # Égypte - Livre égyptienne
    'TR': 'TRY',  # Turquie - Livre turque
    'SA': 'SAR',  # Arabie saoudite - Riyal
    'NG': 'NGN',  # Nigeria - Naira
    'KE': 'KES',  # Kenya - Shilling kényan
    'GH': 'GHS',  # Ghana - Cedi
    'MA': 'MAD',  # Maroc - Dirham marocain
    'TN': 'TND',  # Tunisie - Dinar tunisien
    'SN': 'XOF',  # Sénégal - Franc CFA (UEMOA)
    'CI': 'XOF',  # Côte d'Ivoire - Franc CFA (UEMOA)
    'BJ': 'XOF',  # Bénin - Franc CFA (UEMOA)
    'BF': 'XOF',  # Burkina Faso - Franc CFA (UEMOA)
    'ML': 'XOF',  # Mali - Franc CFA (UEMOA)
    'NE': 'XOF',  # Niger - Franc CFA (UEMOA)
    'TG': 'XOF',  # Togo - Franc CFA (UEMOA)
    'GQ': 'XAF',  # Guinée équatoriale - Franc CFA (CEMAC)
    'GA': 'XAF',  # Gabon - Franc CFA (CEMAC)
    'CM': 'XAF',  # Cameroun - Franc CFA (CEMAC)
    'CF': 'XAF',  # République centrafricaine - Franc CFA (CEMAC)
    'TD': 'XAF',  # Tchad - Franc CFA (CEMAC)
    'CG': 'XAF',  # Congo-Brazzaville - Franc CFA (CEMAC)
    'CD': 'CDF',  # République démocratique du Congo - Franc congolais
}

# Pays par défaut où la plupart des devises africaines sont acceptées
DEFAULT_CURRENCY = 'XOF'  # Franc CFA

def get_currency_from_ip(ip_address):
    """
    Détermine la devise de l'utilisateur en fonction de son adresse IP.
    Utilise la base de données GeoLite2 pour localiser l'adresse IP.
    """
    try:
        # Vérifier si le chemin de la base de données GeoIP existe
        reader_path = os.path.join(settings.GEOIP_PATH, 'GeoLite2-Country.mmdb')
        if not os.path.exists(reader_path):
            logger.warning(f"GeoIP database file not found at {reader_path}")
            return DEFAULT_CURRENCY
        
        # Créer un lecteur pour la base de données GeoIP
        reader = geoip2.database.Reader(reader_path)
        
        # Obtenir le pays de l'adresse IP
        response = reader.country(ip_address)
        country_code = response.country.iso_code
        
        # Fermer le lecteur de base de données
        reader.close()
        
        # Obtenir la devise pour ce pays
        currency = COUNTRY_TO_CURRENCY.get(country_code, DEFAULT_CURRENCY)
        
        logger.info(f"IP {ip_address} is from {country_code}, using currency {currency}")
        return currency
    
    except FileNotFoundError:
        logger.error(f"GeoIP database file not found")
        return DEFAULT_CURRENCY
    except AddressNotFoundError:
        logger.warning(f"IP address {ip_address} not found in database")
        return DEFAULT_CURRENCY
    except Exception as e:
        logger.error(f"Error determining currency from IP: {str(e)}")
        return DEFAULT_CURRENCY

def get_exchange_rate(from_currency, to_currency):
    """
    Obtient le taux de change entre deux devises en utilisant une API externe.
    """
    if from_currency == to_currency:
        return 1.0
    
    try:
        # Utiliser l'API d'Exchange Rate pour obtenir le taux de change
        api_key = settings.EXCHANGE_RATE_API_KEY
        url = f"https://api.exchangerate-api.com/v4/latest/{from_currency}"
        
        response = requests.get(url)
        data = response.json()
        
        if response.status_code == 200 and 'rates' in data:
            return data['rates'].get(to_currency, 1.0)
        else:
            logger.error(f"Failed to get exchange rate: {response.status_code}")
            return 1.0
    
    except Exception as e:
        logger.error(f"Error getting exchange rate: {str(e)}")
        return 1.0

def convert_price(price, from_currency, to_currency):
    """
    Convertit un prix d'une devise à une autre.
    """
    if from_currency == to_currency:
        return price
    
    exchange_rate = get_exchange_rate(from_currency, to_currency)
    converted_price = price * exchange_rate
    
    logger.info(f"Converted {price} {from_currency} to {converted_price} {to_currency}")
    return converted_price

def get_client_ip(request):
    """
    Extrait l'adresse IP du client à partir de la requête HTTP.
    """
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0]
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip