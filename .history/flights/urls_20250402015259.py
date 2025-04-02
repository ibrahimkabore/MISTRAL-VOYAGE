from django.urls import path
from .views import (
    AirportListView, FeaturedDestinationsView, RandomDestinationsView,
    FlightSearchView, MultiCityFlightSearchView, PopularRoutesView,
    HomeView, FlightSearchView, AirportSearchView, BookFlightView,
    ConfirmBookingView, BookingConfirmationView, MyBookingsView,
    CancelReservationView
)

# urlpatterns = [
#     path('airports/', AirportListView.as_view(), name='airport-list'),
#     path('featured-destinations/', FeaturedDestinationsView.as_view(), name='featured-destinations'),
#     path('random-destinations/', RandomDestinationsView.as_view(), name='random-destinations'),
#     path('search/', FlightSearchView.as_view(), name='flight-search'),
#     path('multi-city-search/', MultiCityFlightSearchView.as_view(), name='multi-city-search'),
#     path('popular-routes/', PopularRoutesView.as_view(), name='popular-routes'),
# ]

from django.urls import path
from . import views

urlpatterns = [
    # Vues combinant API et rendu HTML
    path('', views.HomeView.as_view(), name='home'),
    path('search/', views.FlightSearchView.as_view(), name='search_flights'),
    path('airports/search/', views.AirportSearchView.as_view(), name='search_airports'),
    path('booking/new/', views.BookFlightView.as_view(), name='book_flight'),
    path('booking/confirm/', views.ConfirmBookingView.as_view(), name='confirm_booking'),
    path('booking/<int:reservation_id>/', views.BookingConfirmationView.as_view(), name='booking_confirmation'),
    path('bookings/', views.MyBookingsView.as_view(), name='my_bookings'),
    path('booking/<int:reservation_id>/cancel/', views.CancelReservationView.as_view(), name='cancel_reservation'),
    
    # API uniquement
    path('api/destinations/random/', views.RandomDestinationsView.as_view(), name='random_destinations'),
    
    # # Vous pouvez également ajouter ces vues issues du premier fichier
    # path('api/airports/', views.AirportListView.as_view(), name='airport_list'),
    # path('api/destinations/featured/', views.FeaturedDestinationsView.as_view(), name='featured_destinations'),
    # path('api/routes/popular/', views.PopularRoutesView.as_view(), name='popular_routes'),
    # path('api/flights/multi-city/', views.MultiCityFlightSearchView.as_view(), name='multi_city_flight_search'),
]