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