from django.urls import path
from .views import (
    AirportListView, FeaturedDestinationsView, RandomDestinationsView,
    FlightSearchView, MultiCityFlightSearchView
)

urlpatterns = [
    path('airports/', AirportListView.as_view(), name='airport-list'),
    path('featured-destinations/', FeaturedDestinationsView.as_view(), name='featured-destinations'),
    path('random-destinations/', RandomDestinationsView.as_view(), name='random-destinations'),
    path('search/', FlightSearchView.as_view(), name='flight-search'),
    path('multi-city-search/', MultiCityFlightSearchView.as_view(), name='multi-city-search'),
]