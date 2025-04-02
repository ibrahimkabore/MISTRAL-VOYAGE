from rest_framework import status, generics, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from django.utils import timezone
from authentication.models import CustomUser, OTPCode
from authentication.serializers import (
    UserSerializer, RegisterSerializer, LoginSerializer, 
    VerifyOTPSerializer, EmailSerializer, ResetPasswordSerializer
)