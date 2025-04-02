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
            otp = OTPCode.objects.filter(user=user, purpose='register', code=code).order_by('-created_at').first()
            
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