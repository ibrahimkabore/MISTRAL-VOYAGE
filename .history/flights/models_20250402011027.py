from django.db import models

# Create your models here.


class Airport(models.Model):
    code = models.CharField(max_length=3, primary_key=True)
    name = models.CharField(max_length=255)
    city = models.CharField(max_length=255)
    country = models.CharField(max_length=255)
    
    def __str__(self):
        return f"{self.code} - {self.name} ({self.city}, {self.country})"

