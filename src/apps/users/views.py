from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError
from drf_spectacular.utils import extend_schema, OpenApiResponse

from apps.users.serializers import (
    LoginSerializer,
    LoginResponseSerializer,
    RefreshTokenSerializer,
    RefreshTokenResponseSerializer
)


@extend_schema(
    request=LoginSerializer,
    responses={
        200: LoginResponseSerializer,
        400: OpenApiResponse(description='Invalid credentials')
    },
    summary='User login',
    description='Authenticate user and return JWT access and refresh tokens'
)
@api_view(['POST'])
@permission_classes([AllowAny])
def login_view(request):
    """
    User login endpoint
    """
    serializer = LoginSerializer(data=request.data)
    
    if serializer.is_valid():
        user = serializer.validated_data['user']
        
        # Generate JWT tokens
        refresh = RefreshToken.for_user(user)
        
        return Response({
            'access': str(refresh.access_token),
            'refresh': str(refresh),
            'user_id': user.id,
            'username': user.username,
            'email': user.email,
            'is_superuser': user.is_superuser,
        }, status=status.HTTP_200_OK)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@extend_schema(
    request=RefreshTokenSerializer,
    responses={
        200: RefreshTokenResponseSerializer,
        400: OpenApiResponse(description='Invalid or expired refresh token')
    },
    summary='Refresh access token',
    description='Get new access token using refresh token'
)
@api_view(['POST'])
@permission_classes([AllowAny])
def refresh_token_view(request):
    """
    Refresh access token endpoint
    """
    refresh_token = request.data.get('refresh')
    
    if not refresh_token:
        return Response(
            {'error': 'Refresh token is required'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    try:
        refresh = RefreshToken(refresh_token)
        access_token = refresh.access_token
        
        return Response({
            'access': str(access_token),
        }, status=status.HTTP_200_OK)
    
    except TokenError as e:
        return Response(
            {'error': 'Invalid or expired refresh token'},
            status=status.HTTP_400_BAD_REQUEST
        )
