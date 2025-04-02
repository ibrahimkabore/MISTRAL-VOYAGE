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

class LoginInitiateView(APIView):
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        if serializer.is_valid():
            identifier = serializer.validated_data['username']  # Récupérer le champ 'username' ou 'email'
            password = serializer.validated_data['password']
            
            # Vérifier si l'identifiant est un nom d'utilisateur ou un email
            if "@" in identifier:  # Si l'identifiant contient un '@', c'est un email
                try:
                    user = User.objects.get(email=identifier)
                except User.DoesNotExist:
                    return Response({
                        "error": "Identifiants invalides."
                    }, status=status.HTTP_401_UNAUTHORIZED)
            else:
                # Sinon, c'est un nom d'utilisateur
                user = authenticate(username=identifier, password=password)
                
                if user is None:
                    return Response({
                        "error": "Identifiants invalides."
                    }, status=status.HTTP_401_UNAUTHORIZED)
            
            # Vérifier si l'utilisateur est trouvé et ses informations
            profile = CustomUser.objects.get(user=user)
                
            if not profile.is_email_verified:
                return Response({
                    "error": "Email non vérifié. Veuillez vérifier votre email."
                }, status=status.HTTP_400_BAD_REQUEST)
                
            # Envoyer un code OTP pour la connexion
            send_otp_email(user, 'login')  # L'email envoyé contient l'information de l'utilisateur
                
            return Response({
                "message": "Un code de vérification a été envoyé à votre email."
            }, status=status.HTTP_200_OK)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)




class LoginCompleteView(APIView):
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        try:
            username = request.data.get('username')
            code = request.data.get('code')
            
            if not username or not code:
                return Response({
                    "error": "Nom d'utilisateur et code sont requis."
                }, status=status.HTTP_400_BAD_REQUEST)
            
            user = CustomUser.objects.get(username=username)
            otp = OTPCode.objects.filter(user=user, purpose='login', code=code).order_by('-created_at').first()
            
            if not otp or not otp.is_valid():
                return Response({
                    "error": "Code invalide ou expiré."
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Marquer le code comme utilisé
            otp.is_used = True
            otp.save()
            
            # Générer des tokens JWT
            refresh = RefreshToken.for_user(user)
            
            return Response({
                "refresh": str(refresh),
                "access": str(refresh.access_token),
                "user": UserSerializer(user).data
            }, status=status.HTTP_200_OK)
            
        except CustomUser.DoesNotExist:
            return Response({
                "error": "Utilisateur non trouvé."
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({
                "error": str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

 


