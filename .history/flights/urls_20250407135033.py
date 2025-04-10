# from django.urls import path
# from .views import (
#     FlightSearchView, 
#     MultiCityFlightSearchView,
#     FlightBookingView,
#     BookingDetailView,
#     UpdateBookingStatusView
# )

# urlpatterns = [
#     # URLs de recherche de vols
#     path('flights/search/', FlightSearchView.as_view(), name='flight_search'),
#     path('flights/multi-city-search/', MultiCityFlightSearchView.as_view(), name='multi_city_flight_search'),
    
#     # URLs de réservation
#     path('bookings/create/', FlightBookingView.as_view(), name='create_booking'),
#     path('bookings/<str:booking_reference>/', BookingDetailView.as_view(), name='booking_detail'),
#     path('bookings/<str:booking_reference>/update-status/', UpdateBookingStatusView.as_view(), name='update_booking_status'),
# ]



from django.urls import path
from .views import (
    FlightSearchView, 
    MultiCityFlightSearchView,
    FlightBookingView,
    BookingDetailView,
    UpdateBookingStatusView
)

urlpatterns = [
    # URLs de recherche de vols
    path('flights/search/', FlightSearchView.as_view(), name='flight_search'),
    path('flights/multi-city-search/', MultiCityFlightSearchView.as_view(), name='multi_city_flight_search'),
    
    # URLs de réservation
    path('bookings/create/', FlightBookingView.as_view(), name='create_booking'),
    path('bookings/<str:booking_reference>/', BookingDetailView.as_view(), name='booking_detail'),
    path('bookings/<str:booking_reference>/update-status/', UpdateBookingStatusView.as_view(), name='update_booking_status'),
]