# from django.contrib import admin
# from django.utils.html import format_html
# from .models import Passenger, Booking

# @admin.register(Passenger)
# class PassengerAdmin(admin.ModelAdmin):
#     list_display = ('first_name', 'last_name', 'passenger_type', 'gender', 'date_of_birth', 'passport_number')
#     list_filter = ('passenger_type', 'gender')
#     search_fields = ('first_name', 'last_name', 'passport_number')
#     ordering = ('last_name', 'first_name')
#     fieldsets = (
#         ('Informations personnelles', {
#             'fields': ('first_name', 'last_name', 'date_of_birth', 'gender')
#         }),
#         ('Détails du voyage', {
#             'fields': ('passenger_type', 'passport_number')
#         }),
#     )

# class PassengerInline(admin.TabularInline):
#     model = Booking.passengers.through
#     extra = 0
#     verbose_name = "Passager"
#     verbose_name_plural = "Passagers"

# @admin.register(Booking)
# class BookingAdmin(admin.ModelAdmin):
#     list_display = ('reference', 'user_email', 'status', 'formatted_total_price', 'payment_method', 'created_at')
#     list_filter = ('status', 'payment_method', 'created_at')
#     search_fields = ('reference', 'user__email', 'contact_email', 'contact_phone')
#     readonly_fields = ('reference', 'created_at', 'updated_at')
#     date_hierarchy = 'created_at'
#     inlines = [PassengerInline]
#     exclude = ('passengers',)  # On exclut ce champ car il est géré par l'inline
    
#     fieldsets = (
#         ('Informations de réservation', {
#             'fields': ('reference', 'user', 'flight_offer', 'status')
#         }),
#         ('Détails financiers', {
#             'fields': ('total_price', 'currency', 'payment_method')
#         }),
#         ('Coordonnées', {
#             'fields': ('contact_email', 'contact_phone')
#         }),
#         ('Rendez-vous en agence', {
#             'fields': ('office_appointment_date',),
#             'classes': ('collapse',),
#             'description': 'Date et heure du rendez-vous si paiement en agence'
#         }),
#         ('Données techniques', {
#             'fields': ('amadeus_booking_id', 'raw_booking_data', 'created_at', 'updated_at'),
#             'classes': ('collapse',),
#         }),
#     )
    
#     def user_email(self, obj):
#         return obj.user.email
#     user_email.short_description = 'Utilisateur'
    
#     def formatted_total_price(self, obj):
#         return format_html('{} <span style="color: #666;">{}</span>', obj.total_price, obj.currency)
#     formatted_total_price.short_description = 'Montant'