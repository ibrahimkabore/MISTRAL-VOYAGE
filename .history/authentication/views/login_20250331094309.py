from rest_framework import status, generics, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from authentication.models import CustomUser, OTPCode
from authentication.serializers import UserSerializer, RegisterSerializer, LoginSerializer, ResendOTPSerializer, ResetPasswordSerializer
from authentication.utils import send_otp_email
from rest_framework.decorators import api_view

from django.contrib.auth import authenticate
from rest_framework.response import Response
from rest_framework import status, permissions
from rest_framework.views import APIView
from authentication.models import CustomUser
from authentication.serializers import LoginSerializer
from authentication.utils import send_otp_email
from django.core.exceptions import ObjectDoesNotExist

class LoginInitiateView(APIView):
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        
        if serializer.is_valid():
            identifier = serializer.validated_data['username']  # Peut être email ou username
            password = serializer.validated_data['password']
            
            # Vérifier si c'est un email ou un username
            user = None
            if "@" in identifier:
                try:
                    user = CustomUser.objects.get(email=identifier)
                except ObjectDoesNotExist:
                    return Response({"error": "Utilisateur introuvable."}, status=status.HTTP_404_NOT_FOUND)
            else:
                try:
                    user = CustomUser.objects.get(username=identifier)
                except ObjectDoesNotExist:
                    return Response({"error": "Utilisateur introuvable."}, status=status.HTTP_404_NOT_FOUND)
            
            # Authentification avec username (Django ne supporte pas directement l'email)
            user = authenticate(username=user.username, password=password)

            if user is not None:
                # Vérifier si l'email est vérifié
                if not user.is_email_verified:
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
            profile = CustomUser.objects.get(username=user)
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


@api_view(['GET'])
def test(request):

    return Response({"message": "Test"}, status=status.HTTP_200_OK)