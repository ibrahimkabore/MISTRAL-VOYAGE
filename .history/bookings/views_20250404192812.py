from django.shortcuts import get_object_or_404
from rest_framework import generics, permissions, status, views
from rest_framework.response import Response
from .models import Booking, Passenger
from .serializers import BookingCreateSerializer, BookingDetailSerializer

class BookingCreateView(generics.CreateAPIView):
    serializer_class = BookingCreateSerializer
    #permission_classes = [permissions.IsAuthenticated]
    
    def get_serializer_context(self):
        context = super().get_serializer_context()
        return context

class BookingDetailView(generics.RetrieveAPIView):
    serializer_class = BookingDetailSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return Booking.objects.filter(user=self.request.user)

class BookingListView(generics.ListAPIView):
    serializer_class = BookingDetailSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return Booking.objects.filter(user=self.request.user)

class BookingCancelView(generics.UpdateAPIView):
    serializer_class = BookingDetailSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return Booking.objects.filter(user=self.request.user)
    
    def update(self, request, *args, **kwargs):
        booking = self.get_object()
        if booking.status in ['PAID', 'COMPLETED']:
            return Response(
                {"error": "Impossible d'annuler une réservation déjà payée ou terminée."},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        booking.status = 'CANCELLED'
        booking.save()
        
        serializer = self.get_serializer(booking)
        return Response(serializer.data)