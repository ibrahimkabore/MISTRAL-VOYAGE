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
    - `country`: Associated country of the user (auto-detected).
    - `city`: Associated city of the user (auto-detected).
    - `currency`: Currency based on user's country (auto-detected).
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
    photos = models.ImageField(
        "Photo", 
        upload_to='user_photos/', 
        blank=True, 
        null=True
    )
   
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
        _("Devise"),
        max_length=100,
        blank=True
    )
    
    def __str__(self):
        return f"{self.username}"
    
    def save(self, *args, **kwargs):
        """
        Surcharge de la méthode save pour récupérer automatiquement
        les informations de géolocalisation si elles sont manquantes.
        """
        # D'abord sauvegarder pour avoir un ID
        super().save(*args, **kwargs)
        
        # Si les champs de géolocalisation sont vides, essayer de les récupérer
        if not self.pays or not self.ville or not self.currency:
            self.update_geolocation_from_ip()
    
    def update_geolocation_from_ip(self, ip_address=None):
        """
        Met à jour les informations de géolocalisation à partir d'une IP spécifique
        ou de l'IP actuelle si aucune IP n'est fournie.
        
        Args:
            ip_address (str, optional): Adresse IP à utiliser. Si non fournie,
                                       l'API détectera l'IP du serveur.
        
        Returns:
            bool: True si la mise à jour a réussi, False sinon.
        """
        try:
            # Construire l'URL avec ou sans IP spécifique
            url = f'http://ip-api.com/json/{ip_address if ip_address else ""}'
            
            # Appeler l'API
            response = requests.get(url)
            
            # Vérifier si la requête a réussi
            if response.status_code == 200:
                data = response.json()
                
                # Vérifier si l'API a renvoyé un statut de succès
                if data.get('status') == 'success':
                    # Mise à jour des champs
                    update_fields = []
                    
                    if not self.pays:
                        self.pays = data.get('country', '')
                        update_fields.append('pays')
                        
                    if not self.ville:
                        self.ville = data.get('city', '')
                        update_fields.append('ville')
                        
                    if not self.currency:
                        country_code = data.get('countryCode', '')
                        self.currency = self._get_currency_from_country_code(country_code)
                        update_fields.append('currency')
                    
                    # Sauvegarder les modifications sans rappeler cette méthode
                    if update_fields:
                        super().save(update_fields=update_fields)
                    
                    return True
            
            return False
        except Exception as e:
            print(f"Erreur lors de la récupération des données de géolocalisation: {str(e)}")
            return False
    
    def _get_currency_from_country_code(self, country_code):
        """
        Convertit un code pays en code devise.
        
        Args:
            country_code (str): Code pays à deux lettres (ISO 3166-1 alpha-2)
            
        Returns:
            str: Code devise correspondant ou chaîne vide si non trouvé
        """
        country_currency_map = {
            'US': 'USD',  # États-Unis
            'CA': 'CAD',  # Canada
            'GB': 'GBP',  # Royaume-Uni
            'FR': 'EUR',  # France
            'DE': 'EUR',  # Allemagne
            'IT': 'EUR',  # Italie
            'ES': 'EUR',  # Espagne
            'JP': 'JPY',  # Japon
            'CN': 'CNY',  # Chine
            'AU': 'AUD',  # Australie
            'CH': 'CHF',  # Suisse
            'RU': 'RUB',  # Russie
            'BR': 'BRL',  # Brésil
            'IN': 'INR',  # Inde
            'ZA': 'ZAR',  # Afrique du Sud
            'MX': 'MXN',  # Mexique
            'SG': 'SGD',  # Singapour
            'HK': 'HKD',  # Hong Kong
            'SE': 'SEK',  # Suède
            'NO': 'NOK',  # Norvège
            'DK': 'DKK',  # Danemark
            # Ajouter d'autres mappages selon les besoins
        }
        
        return country_currency_map.get(country_code, '')


# Fonction utilitaire à utiliser dans les vues pour récupérer l'IP client
def get_client_ip(request):
    """
    Récupère l'adresse IP du client en tenant compte des proxys.
    
    Args:
        request (HttpRequest): Objet request Django
        
    Returns:
        str: L'adresse IP du client
    """
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0].strip()
    else:
        ip = request.META.get('REMOTE_ADDR')
    return ip

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