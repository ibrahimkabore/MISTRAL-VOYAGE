from rest_framework import serializers
from .models import CustomUser, OTPCode
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password


class CustomUserSerializer(serializers.ModelSerializer):
    class Meta:
        model = CustomUser
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'phone', 'gender', 'photos']


class OTPCodeSerializer(serializers.ModelSerializer):
    class Meta:
        model = OTPCode
        fields = ['id', 'user', 'code', 'created_at', 'purpose', 'is_used']
