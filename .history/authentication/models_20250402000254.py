from django.db import models
from django.contrib.auth.models import AbstractUser
from safedelete.models import SafeDeleteModel
import uuid
from safedelete.models import SOFT_DELETE_CASCADE
from django.utils.translation import gettext_lazy as _
from simple_history.models import HistoricalRecords
from django.core.files.storage import FileSystemStorage
from django.conf import settings
import os
import random
import string
from django.utils import timezone


imageFs = FileSystemStorage(location=os.path.join(str(settings.BASE_DIR),
                                                 '/medias/'))
#### models User  personaliser ########
class CustomUser(AbstractUser, SafeDeleteModel):
    """
    Customized user model inheriting from Django's AbstractUser.
    - `phone`: User's phone number.
    - `gender`: Gender with predefined choices (Male, Female, Other).
    - `country`: Associated country of the user (optional).
    - `city`: Associated city of the user (optional).
    - History tracking and login/logout signals to manage online status.
    - `created_at`: Timestamp of when the user was created.
    - `updated_at`: Timestamp of the last update to the user.
    - `safedelete_policy`: Policy for soft deletion.
    - `history`: Historical records of the user.
    """
    """Modèle d'utilisateur personnalisé avec UUID comme identifiant"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    GENDER_CHOICES = [
        ('H', 'Homme'),
        ('F', 'Femme'),
        ('A', 'Autre')
    ]
    phone = models.CharField(
        _("Phone Number"),
        max_length=15,
        blank=True
    )
    gender = models.CharField(
        _("Gender"),
        max_length=1,
        choices=GENDER_CHOICES,
        blank=True
    )
    photos = models.ImageField("Photo", upload_to='user_photos/', blank=True, null=True)
   
    created_at = models.DateTimeField(
        _("Creation Timestamp"),
        auto_now_add=True
    )
    updated_at = models.DateTimeField(
        _("Last Update Timestamp"),
        auto_now=True
    )
    safedelete_policy = SOFT_DELETE_CASCADE
   
    history = HistoricalRecords(table_name='CustomUser_history', history_id_field=models.UUIDField(default=uuid.uuid4))
    is_email_verified = models.BooleanField(default=False)
   
    pays = models.CharField(
        _("Pays"),
        max_length=100,
        blank=True
    )
    ville = models.CharField(
        _("Ville"),
        max_length=100,
        blank=True
    )
    currency = models.CharField(
        _("Currency"),
        max_length=100,
        blank=True
    )
    
    def __str__(self):
        return f"{self.username}"
    
    def get_geolocation_info(self, ip_address):
        """
        Fetch geolocation information from IP-API and update user fields.
        
        Args:
            ip_address (str): The IP address to lookup
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            # Call IP-API endpoint
            response = requests.get(f'http://ip-api.com/json/{ip_address}')
            
            # Check if request was successful
            if response.status_code == 200:
                data = response.json()
                
                # Check if the request was successful according to IP-API
                if data.get('status') == 'success':
                    # Update user fields
                    self.pays = data.get('country', '')
                    self.ville = data.get('city', '')
                    
                    # For currency, IP-API returns countryCode, which we need to map to currency
                    country_code = data.get('countryCode', '')
                    self.currency = self.get_currency_from_country_code(country_code)
                    
                    # Save the user object
                    self.save()
                    return True
            
            return False
        except Exception as e:
            # Log error and return False
            print(f"Error fetching geolocation data: {str(e)}")
            return False
    
    def get_currency_from_country_code(self, country_code):
        """
        Map country code to currency code.
        This is a simplified mapping - in a real application, you might want to use a more complete mapping.
        
        Args:
            country_code (str): The two-letter country code
            
        Returns:
            str: The currency code or empty string if not found
        """
        # Common country to currency mappings
        country_currency_map = {
            'US': 'USD',  # United States
            'CA': 'CAD',  # Canada
            'GB': 'GBP',  # United Kingdom
            'EU': 'EUR',  # European Union
            'FR': 'EUR',  # France
            'DE': 'EUR',  # Germany
            'JP': 'JPY',  # Japan
            'CN': 'CNY',  # China
            'AU': 'AUD',  # Australia
            'CH': 'CHF',  # Switzerland
            # Add more mappings as needed
        }
        
        return country_currency_map.get(country_code, '')

class OTPCode(models.Model):
    """Modèle pour les codes OTP de vérification"""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='otp_codes')
    code = models.CharField(max_length=6)
    created_at = models.DateTimeField(auto_now_add=True)
    purpose = models.CharField(max_length=20, choices=[
        ('register', 'Registration'),
        ('login', 'Login'),
        ('reset', 'Password Reset')
    ])
    is_used = models.BooleanField(default=False)
    
    def __str__(self):
        return f"{self.user.email} - {self.code}"
    
    def is_valid(self):
        # Le code est valide pendant 1 minute
        return not self.is_used and (timezone.now() - self.created_at).total_seconds() < 900
    
    @classmethod
    def generate_code(cls, user, purpose):
        # Générer un code OTP à 6 chiffres
        code = ''.join(random.choices(string.digits, k=6))
        
        # Supprimer les anciens codes pour cet utilisateur avec le même but
        cls.objects.filter(user=user, purpose=purpose).delete()
        
        # Créer un nouveau code
        otp = cls.objects.create(user=user, code=code, purpose=purpose)
        return otp