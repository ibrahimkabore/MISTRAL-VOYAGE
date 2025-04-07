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
        default='ECONOMY'
    )

class MultiCityFlightSearchSerializer(serializers.Serializer):
    segments = FlightSearchSerializer(many=True)
    adults = serializers.IntegerField(min_value=1, max_value=9, default=1)
    children = serializers.IntegerField(min_value=0, max_value=9, default=0)
    infants = serializers.IntegerField(min_value=0, max_value=9, default=0)
    travel_class = serializers.ChoiceField(
        choices=[('ECONOMY', 'Economy'), ('PREMIUM_ECONOMY', 'Premium Economy'), ('BUSINESS', 'Business'), ('FIRST', 'First')],
        default='ECONOMY'
    )


class PopularRouteSerializer(serializers.ModelSerializer):
    origin_city = serializers.CharField(source='origin.city', read_only=True)
    destination_city = serializers.CharField(source='destination.city', read_only=True)
    origin_code = serializers.CharField(source='origin.code', read_only=True)
    destination_code = serializers.CharField(source='destination.code', read_only=True)
    
    class Meta:
        model = PopularRoute
        fields = ['id', 'origin_code', 'destination_code', 'origin_city', 
                 'destination_city', 'image_url']