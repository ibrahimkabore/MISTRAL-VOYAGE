from rest_framework import serializers
from .models import CustomUser
from django.contrib.auth.password_validation import validate_password

class UserSerializer(serializers.ModelSerializer):
    email = serializers.EmailField()

    class Meta:
        model = CustomUser
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'phone', 'gender', 'photos']
        read_only_fields=['id']


class RegisterSerializer(serializers.ModelSerializer):
    email=serializers.EmailField(required=True)
    password=serializers.CharField(required=True, write_only=True, validators=[validate_password])
    password2=serializers.CharField(required=True, write_only=True)

    class Meta:
        model = CustomUser
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'phone', 'gender', 'photos', 'password', 'password2']
        read_only_fields=['id']
    
    def validate(self,attrs):
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError({"password": "Les mots de passe ne correspondent pas."})
        
        if CustomUser.objects.filter(email=attrs['email']).exists():
            raise serializers.ValidationError({"email": "Un utilisateur avec cet email existe déjà."})

        return attrs

    def create(self,validated_data):

        # Générer le username basé sur le prénom + deux chiffres aléatoires
        first_name = validated_data['first_name']
        random_digits = ''.join(random.choices(string.digits, k=2))  # Générer deux chiffres aléatoires
        username = f"{first_name}{random_digits}"

        # Assurez-vous que le username est unique
        while CustomUser.objects.filter(username=username).exists():
            random_digits = ''.join(random.choices(string.digits, k=2))
            username = f"{first_name}{random_digits}"

        user=CustomUser.objects.create_user(
            username=username,
            email=validated_data['email'],
            password=validated_data['password'],
            first_name=validated_data['first_name'],
            last_name=validated_data['last_name'],
            phone=validated_data['phone'],
            gender=validated_data['gender'],
            photos=validated_data['photos']
        )

        user.set_password(validated_data['password'])
        user.save()

        return user


class LoginSerializer(serializers.ModelSerializer):
    username=serializers.CharField(required=True)
    password=serializers.CharField(required=True, write_only=True)

   

class VerifyOTPCodeSerializer(serializers.ModelSerializer):
    code=serializers.CharField(required=True,max_length=6,min_length=6)



class EmailVerificationSerializer(serializers.Serializer):
    email=serializers.EmailField(required=True)

class ResetPasswordSerializer(serializers.Serializer):
    email=serializers.EmailField(required=True)
    code=serializers.CharField(required=True,max_length=6,min_length=6)
    password=serializers.CharField(required=True, write_only=True, validators=[validate_password])
    password2=serializers.CharField(required=True, write_only=True)

    def validate(self,attrs):
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError({"password": "Les mots de passe ne correspondent pas."})
        
        if CustomUser.objects.filter(email=attrs['email']).exists():
            raise serializers.ValidationError({"email": "Un utilisateur avec cet email existe déjà."})

        return attrs

class ResendOTPSerializer(serializers.Serializer):
    email = serializers.EmailField(required=True)
    purpose = serializers.ChoiceField(required=True, choices=['register', 'login', 'reset'])