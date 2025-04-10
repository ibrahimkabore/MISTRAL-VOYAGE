from django.contrib import admin
from .models import Passenger, Booking
from django.utils.translation import gettext_lazy as _

class PassengerAdmin(admin.ModelAdmin):
    list_display = ('first_name', 'last_name', 'date_of_birth', 'gender', 'passenger_type')
    list_filter = ('gender', 'passenger_type')
    search_fields = ('first_name', 'last_name', 'passport_number')
    list_per_page = 20

    fieldsets = (
        (None, {
            'fields': ('first_name', 'last_name', 'date_of_birth', 'gender', 'passport_number', 'passenger_type')
        }),
    )

class BookingAdmin(admin.ModelAdmin):
    list_display = ('booking_reference', 'user', 'flight_offer', 'status', 'total_price', 'payment_status', 'booking_date')
    list_filter = ('status', 'payment_status', 'payment_method', 'flight_offer')
    search_fields = ('booking_reference', 'user__email', 'contact_email', 'contact_phone')
    list_per_page = 20
    ordering = ('-booking_date',)
    
    fieldsets = (
        (_('Booking Information'), {
            'fields': ('user', 'flight_offer', 'booking_reference', 'status', 'total_price', 'payment_status', 'payment_date')
        }),
        (_('Contact Details'), {
            'fields': ('contact_email', 'contact_phone', 'office_appointment_date')
        }),
        (_('Payment Information'), {
            'fields': ('payment_method',)  # Assurez-vous que chaque champ n'est mentionné qu'une seule fois
        }),
        (_('Passengers'), {
            'fields': ('passengers',)
        }),
    )
    
    # Pour ajouter un bouton pour générer une référence de réservation manuellement
    actions = ['generate_booking_reference']

    def generate_booking_reference(self, request, queryset):
        for booking in queryset:
            booking.save()  # Appelle la méthode save pour générer une nouvelle référence
        self.message_user(request, _("Références de réservation générées avec succès."))
    generate_booking_reference.short_description = _("Générer les références de réservation")

admin.site.register(Passenger, PassengerAdmin)
admin.site.register(Booking, BookingAdmin)
