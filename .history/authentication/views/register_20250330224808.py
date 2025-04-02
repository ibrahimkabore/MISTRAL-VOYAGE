from rest_framework import status, generics, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from django.utils import timezone
from authentication.models import CustomUser, OTPCode
from authentication.serializers import UserSerializer, RegisterSerializer, LoginSerializer, ResendOTPSerializer, ResetPasswordSerializer, EmailVerificationSerializer
from authentication.utils import send_otp_email

class RegisterView(APIView):
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            
            # Envoyer un code OTP pour vérifier l'email
            send_otp_email(user, 'register')
            
            return Response({
                "message": "Utilisateur créé avec succès. Un code de vérification a été envoyé à votre email."
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)




class RequestPasswordResetView(APIView):
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        serializer = EmailVerificationSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data['email']
            
            try:
                user = CustomUser.objects.get(email=email)
                
                # Envoyer un code OTP pour la réinitialisation
                send_otp_email(user, 'reset')
                
                return Response({
                    "message": "Un code de réinitialisation a été envoyé à votre email."
                }, status=status.HTTP_200_OK)
                
            except CustomUser.DoesNotExist:
                return Response({
                    "error": "Aucun compte n'est associé à cet email."
                }, status=status.HTTP_404_NOT_FOUND)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
