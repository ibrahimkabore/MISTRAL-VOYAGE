from rest_framework import serializers
from .models import CustomUser, OTPCode
from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password

class UserSerializer(serializers.ModelSerializer):
    email = serializers.EmailField()

    class Meta:
        model = CustomUser
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'phone', 'gender', 'photos']
        read_only_fields=('id')


class RegisterSerializer(serializers.ModelSerializer):
    email=serializers.EmailField(required=True)
    password=serializers.CharField(required=True, write_only=True, validators=[validate_password])
    password2=serializers.CharField(required=True, write_only=True)

    class Meta:
        model = CustomUser
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'phone', 'gender', 'photos', 'password', 'password2']
        read_only_fields=('id')
    
    def validate(self,attrs):
        if attrs['password'] != attrs['password2']:
            raise serializers.ValidationError({"password": "Les mots de passe ne correspondent pas."})
        
        if CustomUser.objects.filter(email=attrs['email']).exists():
            raise serializers.ValidationError({"email": "Un utilisateur avec cet email existe déjà."})

        return attrs

    def create(self,validated_data):
        user=CustomUser.objects.create_user(
            username=validated_data['username'],
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

        CustomUser.objects.create(user=user)

        return user


class LoginSerializer(serializers.ModelSerializer):
    username=serializers.CharField(required=True)
    password=serializers.CharField(required=True, write_only=True)