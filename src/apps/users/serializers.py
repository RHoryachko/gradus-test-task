from rest_framework import serializers
from django.contrib.auth import authenticate
from django.contrib.auth.models import User


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField(required=True)
    password = serializers.CharField(required=True, write_only=True)
    
    def validate(self, attrs):
        username = attrs.get('username')
        password = attrs.get('password')
        
        if username and password:
            user = authenticate(username=username, password=password)
            
            if not user:
                raise serializers.ValidationError(
                    'Unable to log in with provided credentials.'
                )
            
            if not user.is_active:
                raise serializers.ValidationError('User account is disabled.')
            
            attrs['user'] = user
        else:
            raise serializers.ValidationError('Must include "username" and "password".')
        
        return attrs


class LoginResponseSerializer(serializers.Serializer):
    access = serializers.CharField()
    refresh = serializers.CharField()
    user_id = serializers.IntegerField()
    username = serializers.CharField()
    email = serializers.EmailField(allow_null=True)
    is_superuser = serializers.BooleanField()


class RefreshTokenSerializer(serializers.Serializer):
    refresh = serializers.CharField(required=True)


class RefreshTokenResponseSerializer(serializers.Serializer):
    access = serializers.CharField()
