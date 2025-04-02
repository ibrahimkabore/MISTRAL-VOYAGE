from rest_framework import status, generics, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from django.utils import timezone
from authentication.models import CustomUser
from authentication.serializers import UserSerializer
from authentication.utils import send_otp_email

class UserInfoView(APIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer = UserSerializer(request.user)
    def get(self, request):
        
        return Response(serializer.data)