from rest_framework import status, generics, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth.models import User
from django.contrib.auth import authenticate
from django.utils import timezone
from authentication.models import CustomUser, OTPCode
from authentication.serializers import  RegisterSerializer, EmailVerificationSerializer,UserSerializer
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




class VerifyEmailView(APIView):
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        try:
            email = request.data.get('email')
            code = request.data.get('code')
            
            if not email or not code:
                return Response({
                    "error": "Email et code sont requis."
                }, status=status.HTTP_400_BAD_REQUEST)
            
            user = CustomUser.objects.get(email=email)
            otp = OTPCode.objects.filter(user='last_name', purpose='register', code=code).order_by('-created_at').first()
            
            if not otp or not otp.is_valid():
                return Response({
                    "error": "Code invalide ou expiré."
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Marquer l'email comme vérifié
            profile = CustomUser.objects.get(user=user)
            profile.is_email_verified = True
            profile.save()
            
            # Marquer le code comme utilisé
            otp.is_used = True
            otp.save()
            
            # Générer des tokens JWT
            refresh = RefreshToken.for_user(user)
            
            return Response({
                "message": "Email vérifié avec succès.",
                "refresh": str(refresh),
                "access": str(refresh.access_token),
                "user": UserSerializer(user).data
            }, status=status.HTTP_200_OK)
            
        except User.DoesNotExist:
            return Response({
                "error": "Utilisateur non trouvé."
            }, status=status.HTTP_404_NOT_FOUND)
        except Exception as e:
            return Response({
                "error": str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)