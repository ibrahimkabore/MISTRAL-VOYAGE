from rest_framework import status, generics, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from django.utils import timezone
from authentication.models import CustomUser, OTPCode
from authentication.serializers import ResendOTPSerializer, ResetPasswordSerializer
from authentication.utils import send_otp_email


class ResendOTPView(APIView):
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        serializer = ResendOTPSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data['email']
            purpose = serializer.validated_data['purpose']
            
            try:
                user = CustomUser.objects.get(email=email)
                
                # Vérifier si le dernier code est encore valide
                last_otp = OTPCode.objects.filter(
                    user=user, 
                    purpose=purpose, 
                    is_used=False
                ).order_by('-created_at').first()
                
                if last_otp and last_otp.is_valid():
                    time_left = 900 - int((timezone.now() - last_otp.created_at).total_seconds())
                    return Response({
                        "error": f"Le code précédent est encore valide. Veuillez attendre {time_left} secondes avant de demander un nouveau code."
                    }, status=status.HTTP_400_BAD_REQUEST)
                
                # Générer un nouveau code OTP
                send_otp_email(user, purpose)
                
                return Response({
                    "message": "Un nouveau code de vérification a été envoyé à votre email."
                }, status=status.HTTP_200_OK)
                
            except User.DoesNotExist:
                return Response({
                    "error": "Aucun compte n'est associé à cet email."
                }, status=status.HTTP_404_NOT_FOUND)
                
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)



class ResetPasswordView(APIView):
    permission_classes = [permissions.AllowAny]
    
    def post(self, request):
        serializer = ResetPasswordSerializer(data=request.data)
        if serializer.is_valid():
            email = serializer.validated_data['email']
            code = serializer.validated_data['code']
            password = serializer.validated_data['password']
            
            try:
                user = CustomUser.objects.get(email=email)
                otp = OTPCode.objects.filter(user=user, purpose='reset', code=code).order_by('-created_at').first()
                
                if not otp or not otp.is_valid():
                    return Response({
                        "error": "Code invalide ou expiré."
                    }, status=status.HTTP_400_BAD_REQUEST)
                
                # Changer le mot de passe
                user.set_password(password)
                user.save()
                
                # Marquer le code comme utilisé
                otp.is_used = True
                otp.save()
                
                return Response({
                    "message": "Mot de passe réinitialisé avec succès."
                }, status=status.HTTP_200_OK)
                
            except User.DoesNotExist:
                return Response({
                    "error": "Utilisateur non trouvé."
                }, status=status.HTTP_404_NOT_FOUND)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)