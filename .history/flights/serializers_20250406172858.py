from rest_framework import serializers
from .models import Airport, FlightOffer, FeaturedDestination, PopularRoute

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

    currency_code = serializers.CharField(max_length=3, default='EUR', help_text="Code de la devise (ex: EUR, USD)")
    
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