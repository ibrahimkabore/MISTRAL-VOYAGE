from rest_framework import serializers
from .models import Booking, Passenger
from flights.serializers import FlightOfferSerializer
from flights.models import FlightOffer
from authentication.models import CustomUser
import datetime
from authentication.serializers import UserSerializer

class PassengerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Passenger
        fields = '__all__'

class BookingCreateSerializer(serializers.ModelSerializer):
    passengers = PassengerSerializer(many=True)
    flight_offer_id = serializers.PrimaryKeyRelatedField(
        queryset=FlightOffer.objects.all(),
        source='flight_offer'
    )
    payment_method = serializers.CharField(required=True)
    
    class Meta:
        model = Booking
        fields = [
            'currency',
            'flight_offer', 'passengers', 'payment_method',
            'contact_email', 'contact_phone'
        ]
        
    def validate_payment_method(self, value):
        if value not in [choice[0] for choice in Booking.PAYMENT_METHOD_CHOICES]:
            raise serializers.ValidationError("Méthode de paiement non valide.")
        return value
    
    def create(self, validated_data):
        passengers_data = validated_data.pop('passengers')
        user = self.context['request'].user
        flight_offer = validated_data['flight_offer']
        
        # Calculer le prix total en fonction du nombre de passagers
        adults = sum(1 for p in passengers_data if p['passenger_type'] == 'ADULT')
        children = sum(1 for p in passengers_data if p['passenger_type'] == 'CHILD')
        infants = sum(1 for p in passengers_data if p['passenger_type'] == 'INFANT')
        
        # Prix simple pour cet exemple (à ajuster selon le modèle de tarification réel)
        total_price = flight_offer.price * adults + (flight_offer.price * 0.75) * children + (flight_offer.price * 0.1) * infants
        
        # Si paiement en agence, programmer un rendez-vous
        if validated_data['payment_method'] == 'OFFICE':
            # Rendez-vous le lendemain à 10h00 (exemple simple)
            today = datetime.date.today()
            tomorrow = today + datetime.timedelta(days=1)
            appointment_time = datetime.time(10, 0)
            appointment_datetime = datetime.datetime.combine(tomorrow, appointment_time)
        else:
            appointment_datetime = None
        
        # Créer la réservation
        booking = Booking.objects.create(
            user=user,
            flight_offer=flight_offer,
            total_price=total_price,
            payment_method=validated_data['payment_method'],
            contact_email=validated_data['contact_email'],
            contact_phone=validated_data['contact_phone'],
            office_appointment_date=appointment_datetime,
            status='PENDING',
            currency=validated_data['currency']
        )
        
        # Créer les passagers et les lier à la réservation
        for passenger_data in passengers_data:
            passenger = Passenger.objects.create(**passenger_data)
            booking.passengers.add(passenger)
        
        return booking

class BookingDetailSerializer(serializers.ModelSerializer):
    passengers = PassengerSerializer(many=True, read_only=True)
    flight_offer = FlightOfferSerializer(read_only=True)
    user = UserSerializer(read_only=True)
    
    class Meta:
        model = Booking
        fields = '__all__'