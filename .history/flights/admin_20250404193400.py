from django.contrib import admin
from .models import FlightOffer, Airport, PopularRoute, FeaturedDestination
# Register your models here.
admin.site.register(FlightOffer)
admin.site.register(Airport)
admin.site.register(PopularRoute)
admin.site.register(FeaturedDestination)
 