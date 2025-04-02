from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import CustomUser
from simple_history.admin import SimpleHistoryAdmin

class CustomUserAdmin(SimpleHistoryAdmin, UserAdmin):
    """
    Custom user admin class to manage our CustomUser model in the Django admin panel.
    This custom admin interface allows us to show the additional fields and history tracking.
    """

    # Define the fields to be displayed in the list view
    list_display = ('username', 'email', 'first_name', 'last_name', 'phone', 'gender', 'created_at', 'updated_at')
    
    # Fields to be displayed in the user creation form
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
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')
        }),
        ('Important dates', {
            'fields': ('last_login', 'date_joined')
        }),
        ('History', {
            'fields': ('created_at', 'updated_at')
        }),
    )

    # Specify ordering of the list view
    ordering = ('username',)

    # Display the history in the admin interface
    history_list_display = ['history_user', 'history_change_reason', 'history_date']

# Register the custom user admin
admin.site.register(CustomUser, CustomUserAdmin)
