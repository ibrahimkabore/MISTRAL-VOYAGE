from django.db import models
from django.contrib.auth.models import AbstractUser
from safedelete.models import SafeDeleteModel

class Utilisateur(AbstractUser,SafeDeleteModel):

