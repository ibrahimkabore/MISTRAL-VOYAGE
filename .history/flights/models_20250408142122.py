from django.db import models
import uuid
# Create your models here.


class Airport(models.Model):
    code = models.CharField(max_length=3, primary_key=True)
    name = models.CharField(max_length=255)
    city = models.CharField(max_length=255)
    country = models.CharField(max_length=255)
    
    def __str__(self):
        return f"{self.code} - {self.name} ({self.city}, {self.country})"

class FlightOffer(models.Model):
    amadeus_id = models.CharField(max_length=255, unique=True)    
    origin = models.ForeignKey(Airport, on_delete=models.CASCADE, related_name='departures')
    destination = models.ForeignKey(Airport, on_delete=models.CASCADE, related_name='arrivals')
    departure_date = models.DateTimeField()
    arrival_date = models.DateTimeField()
    return_departure_date = models.DateTimeField(null=True, blank=True)
    return_arrival_date = models.DateTimeField(null=True, blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=3, default='ANY')
    flight_number = models.CharField(max_length=10)
    airline = models.CharField(max_length=255)
    travel_class = models.CharField(max_length=20, default='ECONOMY')
    is_round_trip = models.BooleanField(default=False)
    available_seats = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    raw_data = models.JSONField()  # Stockage de la réponse brute de l'API
    duration = models.DurationField(null=True, blank=True)
    segments = models.JSONField(null=True, blank=True)
    
    def __str__(self):
        return f"{self.origin.code} to {self.destination.code} on {self.departure_date.strftime('%Y-%m-%d')}"

class FeaturedDestination(models.Model):
    airport = models.ForeignKey(Airport, on_delete=models.CASCADE)
    description = models.TextField()
    image = models.ImageField(upload_to='destinations/')
    price_from = models.DecimalField(max_digits=10, decimal_places=2)
    is_active = models.BooleanField(default=True)
    
    def __str__(self):
        return f"Featured: {self.airport.city}, {self.airport.country}"

# In models.py
class PopularRoute(models.Model):
    origin = models.ForeignKey(Airport, on_delete=models.CASCADE, related_name='origin_routes')
    destination = models.ForeignKey(Airport, on_delete=models.CASCADE, related_name='destination_routes')
    image_url = models.URLField()
    is_active = models.BooleanField(default=True)
    
    class Meta:
        unique_together = ('origin', 'destination')
    
    def __str__(self):
        return f"{self.origin.code} to {self.destination.code}"