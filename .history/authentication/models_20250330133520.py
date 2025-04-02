from django.db import models
from django.contrib.auth.models import AbstractUser
from safedelete.models import SafeDeleteModel
import uuid

class Utilisateur(AbstractUser,SafeDeleteModel):

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
