from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser, OTPCode
from simple_history.admin import SimpleHistoryAdmin

class CustomUserAdmin(SimpleHistoryAdmin, UserAdmin):
    """
    Custom user admin class to manage our CustomUser model in the Django admin panel.
    This custom admin interface allows us to show the additional fields and history tracking.
    """

    # Define the fields to be displayed in the list view
    list_display = ('username', 'email', 'first_name', 'last_name', 'phone', 'gender', 'created_at', 'updated_at')
    
    # Fields to be displayed in the user creation form (excluding non-editable fields like created_at, updated_at)
    add_fieldsets = (
        (None, {
            'fields': ('username', 'password1', 'password2', 'email', 'phone', 'gender', 'photos')
        }),
    )
    
    # Fields to be displayed in the user change form
    fieldsets = (
        (None, {
            'fields': ('username', 'password')
        }),
        ('Personal info', {
            'fields': ('first_name', 'last_name', 'email', 'phone', 'gender', 'photos')
        }),
        ('Permissions', {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions', 'is_email_verified')
        }),
        ('Important dates', {
            'fields': ('last_login', 'date_joined')
        }),
        # Do not include 'created_at' or 'updated_at' in fieldsets for editing
    )

    # Exclude 'created_at' and 'updated_at' from the admin form as they should not be edited
    exclude = ('created_at', 'updated_at')

    # Specify ordering of the list view
    ordering = ('username',)

    # Display the history in the admin interface
    history_list_display = ['history_user', 'history_change_reason', 'history_date']

# Register the custom user admin
admin.site.register(CustomUser, CustomUserAdmin)


@admin.register(OTPCode)
class OTPCodeAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'code', 'purpose', 'created_at', 'is_used')
    list_filter = ('purpose', 'is_used')
    search_fields = ('user__email', 'user__username', 'code')
    readonly_fields = ('id',)