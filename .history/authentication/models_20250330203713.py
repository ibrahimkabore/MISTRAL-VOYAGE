from django.db import models
from django.contrib.auth.models import AbstractUser
from safedelete.models import SafeDeleteModel
import uuid
from safedelete.models import SOFT_DELETE_CASCADE
from django.utils.translation import gettext_lazy as _
from simple_history.models import HistoricalRecords
from django.core.files.storage import FileSystemStorage
from django.conf import settings

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

    def __str__(self):
        return f"{self.username}"
    