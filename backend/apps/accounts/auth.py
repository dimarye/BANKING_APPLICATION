from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework import serializers
from django.contrib.auth.models import User
from django.contrib.auth import authenticate


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """Custom JWT serializer that uses email instead of username"""
    
    def validate(self, attrs):
        # Convert email to username for Django's auth system
        email = attrs.get("email", "")
        password = attrs.get("password", "")
        
        if email and password:
            # Find user by email
            try:
                user = User.objects.get(email=email)
                # Replace email with username for parent validation
                attrs['username'] = user.username
            except User.DoesNotExist:
                raise serializers.ValidationError("No account found with this email.")
        
        return super().validate(attrs)
