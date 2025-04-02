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