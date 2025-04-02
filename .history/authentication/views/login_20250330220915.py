from rest_framework import status, generics, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from django.utils import timezone
from authentication.models import CustomUser, OTPCode
from authentication.serializers import LoginSerializer


class LoginInitiateView(APIView):
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        if serializer.is_valid():
            username = serializer.validated_data['username']
            password = serializer.validated_data['password']
            
            user = authenticate(username=username, password=password)
            
            if user is not None:
                profile = CustomUser.objects.get(user=user)
                
                if not profile.is_email_verified:
                    return Response({
                        "error": "Email non vérifié. Veuillez vérifier votre email."
                    }, status=status.HTTP_400_BAD_REQUEST)
                
                # Envoyer un code OTP pour la connexion
                send_otp_email(user, 'login')
                
                return Response({
                    "message": "Un code de vérification a été envoyé à votre email."
                }, status=status.HTTP_200_OK)
            else:
                return Response({
                    "error": "Identifiants invalides."
                }, status=status.HTTP_401_UNAUTHORIZED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)