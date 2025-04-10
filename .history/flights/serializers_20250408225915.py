from rest_framework import serializers
from .models import Airport, FlightOffer, FeaturedDestination, PopularRoute
from bookings.models import Booking, Passenger

class AirportSerializer(serializers.ModelSerializer):
    class Meta:
        model = Airport
        fields = '__all__'

class FlightOfferSerializer(serializers.ModelSerializer):
    origin_details = AirportSerializer(source='origin', read_only=True)
    destination_details = AirportSerializer(source='destination', read_only=True)
    
    class Meta:
        model = FlightOffer
        fields = '__all__'

class FeaturedDestinationSerializer(serializers.ModelSerializer):
    airport_details = AirportSerializer(source='airport', read_only=True)
    
    class Meta:
        model = FeaturedDestination
        fields = '__all__'

class FlightSearchSerializer(serializers.Serializer):
    currency_code = serializers.CharField(max_length=3, default='XOF')
    origin = serializers.CharField(max_length=3)
    destination = serializers.CharField(max_length=3)
    departure_date = serializers.DateField()
    return_date = serializers.DateField(required=False, allow_null=True)
    adults = serializers.IntegerField(min_value=1, max_value=9, default=1)
    children = serializers.IntegerField(min_value=0, max_value=9, default=0)
    infants = serializers.IntegerField(min_value=0, max_value=9, default=0)
    travel_class = serializers.ChoiceField(
        choices=[('ECONOMY', 'Economy'), ('PREMIUM_ECONOMY', 'Premium Economy'), ('BUSINESS', 'Business'), ('FIRST', 'First')],
        default='ECONOMY',
        help_text="Classe de voyage"
    )

from rest_framework import serializers

class FlightSegmentSerializer(serializers.Serializer):
    origin = serializers.CharField(max_length=3, help_text="Code IATA de l'aéroport d'origine (ex: CDG, ORY)")
    destination = serializers.CharField(max_length=3, help_text="Code IATA de l'aéroport de destination (ex: JFK, LAX)")
    departure_date = serializers.DateField(format='%Y-%m-%d', help_text="Date de départ au format YYYY-MM-DD")

class MultiCityFlightSearchSerializer(serializers.Serializer):
    currency_code = serializers.CharField(max_length=3, default='XOF')
    segments = serializers.ListField(
        child=FlightSegmentSerializer(),
        min_length=2,
        max_length=6,
        help_text="Liste des segments de vol (minimum 2, maximum 6)"
    )
    adults = serializers.IntegerField(min_value=1, max_value=9, default=1, help_text="Nombre d'adultes")
    children = serializers.IntegerField(min_value=0, max_value=9, default=0, help_text="Nombre d'enfants (2-11 ans)")
    infants = serializers.IntegerField(min_value=0, max_value=9, default=0, help_text="Nombre de bébés (moins de 2 ans)")
    travel_class = serializers.ChoiceField(
        choices=[('ECONOMY', 'Economy'), ('PREMIUM_ECONOMY', 'Premium Economy'), ('BUSINESS', 'Business'), ('FIRST', 'First')],
        default='ECONOMY',
        help_text="Classe de voyage"
    )
    
    def validate(self, data):
        # Vérifier que le nombre total de passagers ne dépasse pas 9
        total_passengers = data.get('adults', 1) + data.get('children', 0) + data.get('infants', 0)
        if total_passengers > 9:
            raise serializers.ValidationError("Le nombre total de passagers ne peut pas dépasser 9.")
        
        # Vérifier que le nombre de bébés ne dépasse pas le nombre d'adultes
        if data.get('infants', 0) > data.get('adults', 1):
            raise serializers.ValidationError("Le nombre de bébés ne peut pas dépasser le nombre d'adultes.")
        
        return data


class PopularRouteSerializer(serializers.ModelSerializer):
    origin_city = serializers.CharField(source='origin.city', read_only=True)
    destination_city = serializers.CharField(source='destination.city', read_only=True)
    origin_code = serializers.CharField(source='origin.code', read_only=True)
    destination_code = serializers.CharField(source='destination.code', read_only=True)
    
    class Meta:
        model = PopularRoute
        fields = ['id', 'origin_code', 'destination_code', 'origin_city', 
                 'destination_city', 'image_url']


class FlightSearchSerializer(serializers.Serializer):
    origin = serializers.CharField(max_length=3, help_text="Code IATA de l'aéroport d'origine (ex: CDG, ORY)")
    destination = serializers.CharField(max_length=3, help_text="Code IATA de l'aéroport de destination (ex: JFK, LAX)")
    departure_date = serializers.DateField(format='%Y-%m-%d', help_text="Date de départ au format YYYY-MM-DD")
    return_date = serializers.DateField(required=False, allow_null=True, help_text="Date de retour au format YYYY-MM-DD")
    adults = serializers.IntegerField(min_value=1, default=1, help_text="Nombre d'adultes")
    children = serializers.IntegerField(min_value=0, default=0, help_text="Nombre d'enfants (2-11 ans)")
    infants = serializers.IntegerField(min_value=0, default=0)
    travel_class = serializers.ChoiceField(
        choices=['ECONOMY', 'PREMIUM_ECONOMY', 'BUSINESS', 'FIRST'],
        default='ECONOMY'
    )
    currency_code = serializers.CharField(max_length=3, default='XOF')


class SegmentSerializer(serializers.Serializer):
    origin = serializers.CharField(max_length=3)
    destination = serializers.CharField(max_length=3)
    departure_date = serializers.DateField()


class MultiCityFlightSearchSerializer(serializers.Serializer):
    segments = SegmentSerializer(many=True)
    adults = serializers.IntegerField(min_value=1, default=1)
    children = serializers.IntegerField(min_value=0, default=0)
    infants = serializers.IntegerField(min_value=0, default=0)
    travel_class = serializers.ChoiceField(
        choices=['ECONOMY', 'PREMIUM_ECONOMY', 'BUSINESS', 'FIRST'],
        default='ECONOMY'
    )
    currency_code = serializers.CharField(max_length=3, default='EUR')


class PassengerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Passenger
        fields = [
            'id', 'first_name', 'last_name', 'date_of_birth', 
            'gender', 'passport_number', 'passenger_type'
        ]


class FlightOfferSerializer(serializers.ModelSerializer):
    class Meta:
        model = FlightOffer
        fields = [
            'id', 'origin', 'destination', 
            'departure_date', 'arrival_date', 'return_departure_date', 
            'return_arrival_date', 'price', 'currency', 'flight_number', 
            'airline', 'travel_class', 'is_round_trip', 'available_seats',
            'duration', 'segments'
        ]


class BookingSerializer(serializers.ModelSerializer):
    passengers = PassengerSerializer(many=True, read_only=True)
    flight_offer = FlightOfferSerializer(read_only=True)
    
    class Meta:
        model = Booking
        fields = [
            'id', 'booking_reference', 'user', 'flight_offer', 
            'status', 'booking_date', 'payment_method', 
            'payment_status', 'payment_date', 'total_price', 
            'contact_email', 'contact_phone', 'passengers',
            'office_appointment_date'
        ]
        read_only_fields = ['id', 'booking_reference', 'booking_date', 'payment_date']