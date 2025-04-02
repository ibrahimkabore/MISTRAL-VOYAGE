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

class LoginCompleteView(APIView):
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        try:
            code = request.data.get('code')  # L'utilisateur soumet uniquement le code OTP
            
            if not code:
                return Response({
                    "error": "Code OTP est requis."
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Rechercher le code OTP dans la base de données
            otp = OTPCode.objects.filter(code=code, purpose='login').order_by('-created_at').first()
            
            if not otp or not otp.is_valid():
                return Response({
                    "error": "Code OTP invalide ou expiré."
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Récupérer l'utilisateur lié au code OTP
            user = otp.user
            
            # Marquer le code comme utilisé
            otp.is_used = True
            otp.save()
            
            # Vérifier si l'email de l'utilisateur est vérifié
            profile = CustomUser.objects.get(user=user)
            if not profile.is_email_verified:
                return Response({
                    "error": "Email non vérifié. Veuillez vérifier votre email."
                }, status=status.HTTP_400_BAD_REQUEST)
                
            # Générer des tokens JWT
            refresh = RefreshToken.for_user(user)
            
            return Response({
                "refresh": str(refresh),
                "access": str(refresh.access_token),
                "user": UserSerializer(user).data
            }, status=status.HTTP_200_OK)
            
        except OTPCode.DoesNotExist:
            return Response({
                "error": "Code OTP non trouvé."
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({
                "error": str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class LoginCompleteView(APIView):
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        try:
            code = request.data.get('code')  # L'utilisateur soumet uniquement le code OTP
            
            if not code:
                return Response({
                    "error": "Code OTP est requis."
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Rechercher le code OTP dans la base de données
            otp = OTPCode.objects.filter(code=code, purpose='login').order_by('-created_at').first()
            
            if not otp or not otp.is_valid():
                return Response({
                    "error": "Code OTP invalide ou expiré."
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Récupérer l'utilisateur lié au code OTP
            user = otp.user
            
            # Marquer le code comme utilisé
            otp.is_used = True
            otp.save()
            
            # Vérifier si l'email de l'utilisateur est vérifié
            profile = CustomUser.objects.get(user=user)
            if not profile.is_email_verified:
                return Response({
                    "error": "Email non vérifié. Veuillez vérifier votre email."
                }, status=status.HTTP_400_BAD_REQUEST)
                
            # Générer des tokens JWT
            refresh = RefreshToken.for_user(user)
            
            return Response({
                "refresh": str(refresh),
                "access": str(refresh.access_token),
                "user": UserSerializer(user).data
            }, status=status.HTTP_200_OK)
            
        except OTPCode.DoesNotExist:
            return Response({
                "error": "Code OTP non trouvé."
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({
                "error": str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
