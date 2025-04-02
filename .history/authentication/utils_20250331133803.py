from django.core.mail import send_mail
from django.conf import settings
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from .models import OTPCode
import random
import string

def send_otp_email(user, purpose):
    """
    Génère un code OTP et l'envoie par email à l'utilisateur avec un template HTML stylisé.
    purpose: 'register', 'login', ou 'reset'
    """
    # Générer un code OTP
    otp = OTPCode.generate_code(user, purpose)
    
    # Préparer le contexte pour le template
    context = {
        'username': user.username,
        'code': otp.code,
        'company_name': 'MISTRAL VOYAGE',
        'company_address': '123 Avenue des Voyages,  vallon',
        'company_email': 'contact@mistralvoyage.com',
        'company_website': 'www.mistralvoyage.com'
    }
    
    # Sélectionner le template et le sujet selon le type d'email
    if purpose == 'register':
        template_name = 'templates/emails/registration-email.html'
        subject = 'Bienvenue sur MISTRAL VOYAGE'
    elif purpose == 'login':
        template_name = 'templates/emails/login-email.html'
        subject = 'Connexion à votre compte MISTRAL VOYAGE'
    else:  # reset
        template_name = 'templates/emails/reset-password-email.html'
        subject = 'Réinitialisation de votre mot de passe MISTRAL VOYAGE'
    
    # Rendre le template HTML
    html_message = render_to_string(template_name, context)
    # Créer une version texte brut pour les clients de messagerie qui ne prennent pas en charge le HTML
    plain_message = strip_tags(html_message)
    
    # Envoyer l'email
    send_mail(
        subject,
        plain_message,
        settings.EMAIL_HOST_USER,
        [user.email],
        fail_silently=False,
        html_message=html_message,
    )
    
    return otp.code