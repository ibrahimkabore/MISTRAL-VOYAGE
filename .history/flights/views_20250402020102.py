from django.shortcuts import render, redirect
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required
from rest_framework import views, status, permissions
from rest_framework.response import Response
from rest_framework.renderers import TemplateHTMLRenderer, JSONRenderer
from datetime import datetime, timedelta
import json

from .models import FeaturedDestination
from .serializers import FeaturedDestinationSerializer
from .utils.amadeus_api import AmadeusAPI


class HomeView(views.APIView):
    """
    Vue pour la page d'accueil qui combine API et rendu HTML
    """
    permission_classes = [permissions.AllowAny]
    renderer_classes = [TemplateHTMLRenderer, JSONRenderer]
    
    def get(self, request, format=None):
        tomorrow = (datetime.now() + timedelta(days=1)).strftime('%Y-%m-%d')
        
        # Définir les routes populaires
        popular_routes = [
            {
                'origin': 'CDG',  # Paris Charles de Gaulle
                'destination': 'JFK',  # New York JFK
                'origin_city': 'Paris',
                'destination_city': 'New York',
                'image_url': 'https://images.unsplash.com/photo-1496442226666-8d4d0e62e6e9?w=500',
            },
            {
                'origin': 'CDG',  # Paris
                'destination': 'DXB',  # Dubai
                'origin_city': 'Paris',
                'destination_city': 'Dubai',
                'image_url': 'https://images.unsplash.com/photo-1512453979798-5ea266f8880c?w=500',
            },
            {
                'origin': 'CDG',  # Paris
                'destination': 'BCN',  # Barcelona
                'origin_city': 'Paris',
                'destination_city': 'Barcelone',
                'image_url': 'https://images.unsplash.com/photo-1583422409516-2895a77efded?w=500',
            },
            {
                'origin': 'CDG',  # Paris
                'destination': 'LHR',  # London Heathrow
                'origin_city': 'Paris',
                'destination_city': 'Londres',
                'image_url': 'https://images.unsplash.com/photo-1513635269975-59663e0ac1ad?w=500',
            },
        ]
        
        # Récupérer les prix pour chaque route
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
            except Exception as e:
                route['price'] = None
                route['currency'] = None
        
        # Selon le format demandé, renvoyer HTML ou JSON
        if request.accepted_renderer.format == 'html':
            return Response({'popular_routes': popular_routes, 'tomorrow': tomorrow})
        return Response(popular_routes)

 