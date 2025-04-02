from django.core.mail import send_mail
from django.conf import settings
from .models import OTPCode
import random
import string

def send_otp_email(user, purpose):
    """
    Génère un code OTP et l'envoie par email à l'utilisateur.
    purpose: 'register', 'login', ou 'reset'
    """
    # Générer un code OTP
    otp = OTPCode.generate_code(user, purpose)
    
    # Préparer le sujet et le message selon le but
    if purpose == 'register':
        username = f"{user.username}"  # ou récupérez-le depuis l'utilisateur créé
        message = f'Bienvenue sur MISTRAL VOYAGE !\n\nVotre code de vérification est : {otp.code}\n\nVotre nom d\'utilisateur est : {username}'
    elif purpose == 'login':
        subject = 'Connexion à votre compte MISTRAL VOYAGE'
        message = f'Votre code de connexion à MISTRAL VOYAGE est : {otp.code}'
    else:  # reset
        subject = 'Réinitialisation de votre mot de passe MISTRAL VOYAGE'
        message = f'Votre code de réinitialisation de mot de passe est : {otp.code}'
    
    # Envoyer l'email
    send_mail(
        subject,
        message,
        settings.EMAIL_HOST_USER,
        [user.email],
        fail_silently=False,
    )
    
    return otp.code