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
    _safedelete_policy = SOFT_DELETE_CASCADE
    

    history = HistoricalRecords(table_name='CustomUser_history', history_id_field=models.UUIDField(default=uuid.uuid4))

    is_email_verified = models.BooleanField(default=False)
    

    def __str__(self):
        return f"{self.username}"
    


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
        return not self.is_used and (timezone.now() - self.created_at).total_seconds() < 120
    
    @classmethod
    def generate_code(cls, user, purpose):
        # Générer un code OTP à 6 chiffres
        code = ''.join(random.choices(string.digits, k=6))
        
        # Supprimer les anciens codes pour cet utilisateur avec le même but
        cls.objects.filter(user=user, purpose=purpose).delete()
        
        # Créer un nouveau code
        otp = cls.objects.create(user=user, code=code, purpose=purpose)
        return otp