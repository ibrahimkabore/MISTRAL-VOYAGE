from rest_framework import status, generics, permissions
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from django.utils import timezone
from authentication.models import CustomUser, OTPCode
from authentication.serializers import UserSerializer, ResendOTPSerializer
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
                    time_left = 60 - int((timezone.now() - last_otp.created_at).total_seconds())
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

