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

class Booking(models.Model):
    STATUS_CHOICES = [
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
    
    user = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='bookings'
    )
    flight_offer = models.ForeignKey(
        FlightOffer,
        on_delete=models.PROTECT,
        related_name='bookings'
    )
    booking_reference = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    status = models.CharField(max_length=10, choices=STATUS_CHOICES, default='PENDING')
    booking_date = models.DateTimeField(auto_now_add=True)
    payment_method = models.CharField(max_length=10, choices=PAYMENT_METHOD_CHOICES, blank=True, null=True)
    payment_status = models.BooleanField(default=False)
    payment_date = models.DateTimeField(blank=True, null=True)
    total_price = models.DecimalField(max_digits=10, decimal_places=2)
    contact_email = models.EmailField()
    contact_phone = models.CharField(max_length=20)
    passengers = models.ManyToManyField(Passenger, related_name='bookings')
    office_appointment_date = models.DateTimeField(blank=True, null=True)
    
    def __str__(self):
        return f"Booking {self.booking_reference} - {self.user.email}"
    
    def save(self, *args, **kwargs):
        if not self.booking_reference:
            # Génération d'un numéro de référence unique
            import random
            import string
            
            while True:
                reference = ''.join(random.choices(string.ascii_uppercase + string.digits, k=8))
                if not Booking.objects.filter(booking_reference=reference).exists():
                    self.booking_reference = reference
                    break
        
        super().save(*args, **kwargs)