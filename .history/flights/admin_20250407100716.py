from django.contrib import admin
from .models import Airport, FlightOffer, FeaturedDestination, PopularRoute

# Personnalisation de l'affichage pour le modèle Airport
class AirportAdmin(admin.ModelAdmin):
    list_display = ('code', 'name', 'city', 'country')
    search_fields = ('code', 'name', 'city', 'country')
    list_filter = ('country',)

admin.site.register(Airport, AirportAdmin)

# Personnalisation de l'affichage pour le modèle FlightOffer
class FlightOfferAdmin(admin.ModelAdmin):
    list_display = ('amadeus_id', 'origin', 'destination', 'departure_date', 'arrival_date', 'price', 'airline', 'is_round_trip', 'available_seats', 'created_at')
    search_fields = ('amadeus_id', 'origin__code', 'destination__code', 'airline', 'flight_number')
    list_filter = ('is_round_trip', 'airline', 'currency', 'departure_date', 'destination__city')
    date_hierarchy = 'departure_date'

admin.site.register(FlightOffer, FlightOfferAdmin)

# Personnalisation de l'affichage pour le modèle FeaturedDestination
class FeaturedDestinationAdmin(admin.ModelAdmin):
    list_display = ('airport', 'price_from', 'is_active')
    search_fields = ('airport__name', 'airport__city', 'airport__country')
    list_filter = ('is_active',)

admin.site.register(FeaturedDestination, FeaturedDestinationAdmin)

# Personnalisation de l'affichage pour le modèle PopularRoute
class PopularRouteAdmin(admin.ModelAdmin):
    list_display = ('origin', 'destination', 'image_url', 'is_active')
    search_fields = ('origin__code', 'destination__code', 'image_url')
    list_filter = ('is_active',)

admin.site.register(PopularRoute, PopularRouteAdmin)
