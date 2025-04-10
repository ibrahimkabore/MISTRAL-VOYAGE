from django.db import models
from django.conf import settings
from flights.models import FlightOffer
from authentication.models import CustomUser
class Passenger(models.Model):
    GENDER_CHOICES = [
        ('M', 'Masculin'),
        ('F', 'Féminin'),
        ('O', 'Autre'),
    ]
    
    PASSENGER_TYPE_CHOICES = [
        ('ADULT', 'Adulte'),
        ('CHILD', 'Enfant'),
        ('INFANT', 'Bébé'),
    ]
    
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    date_of_birth = models.DateField()
    gender = models.CharField(max_length=1, choices=GENDER_CHOICES)
    passport_number = models.CharField(max_length=30, blank=True, null=True)
    passenger_type = models.CharField(max_length=10, choices=PASSENGER_TYPE_CHOICES, default='ADULT')
    
    def __str__(self):
        return f"{self.first_name} {self.last_name} ({self.get_passenger_type_display()})"

import random
import string
import time
from django.db import models

class Booking(models.Model):
    BOOKING_STATUS_CHOICES = [
        ('PENDING', 'En attente'),
        ('CONFIRMED', 'Confirmée'),
        ('PAID', 'Payée'),
        ('CANCELLED', 'Annulée'),
        ('COMPLETED', 'Terminée'),
    ]

    PAYMENT_METHOD_CHOICES = [
        ('OFFICE', 'Paiement en agence'),
        ('ORANGE', 'Orange Money'),
        ('MOOV', 'Moov Money'),
        ('WAVE', 'Wave'),
        ('VISA', 'Carte Visa'),
        ('PAYPAL', 'PayPal'),
        ('MTN', 'MTN Money'),
    ]
    
    user = models.ForeignKey('CustomUser', on_delete=models.CASCADE, related_name='bookings')
    flight_offer = models.ForeignKey('FlightOffer', on_delete=models.PROTECT, related_name='bookings')
    passengers = models.ManyToManyField('Passenger', related_name='bookings')

    reference = models.CharField(max_length=20, unique=True, blank=True)  # Référence unique générée
    amadeus_booking_id = models.CharField(max_length=50, blank=True, null=True)  # Pour intégration Amadeus

    status = models.CharField(max_length=20, choices=BOOKING_STATUS_CHOICES, default='PENDING')
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    currency = models.CharField(max_length=3, default='XOF')

    contact_email = models.EmailField()
    contact_phone = models.CharField(max_length=20, blank=True, null=True)

    payment_method = models.CharField(max_length=20, choices=PAYMENT_METHOD_CHOICES, blank=True, null=True)
    payment_status = models.BooleanField(default=False)
    payment_date = models.DateTimeField(blank=True, null=True)

    office_appointment_date = models.DateTimeField(blank=True, null=True)
    raw_booking_data = models.JSONField(blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def generate_reference(self):
        timestamp = int(time.time())
        random_num = random.randint(1000, 9999)
        return f"BK{timestamp}{random_num}"

    def save(self, *args, **kwargs):
        if not self.reference:
            self.reference = self.generate_reference()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"Booking {self.reference} - {self.user.email}"
