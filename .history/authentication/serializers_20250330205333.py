from rest_framework import serializers
from .models import CustomUser, OTPCode
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password


