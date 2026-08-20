from django.contrib.auth import login, logout
from django.contrib.auth.models import User
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from .serializers import LoginSerializer, UserSerializer


@api_view(['POST'])
@permission_classes([AllowAny])
def login_view(request):
    serializer = LoginSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    user = serializer.validated_data['user']
    login(request, user)
    return Response({
        'user': UserSerializer(user).data,
        'message': 'Login successful.',
    }, status=status.HTTP_200_OK)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def logout_view(request):
    logout(request)
    return Response({'message': 'Logout successful.'}, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def user_view(request):
    return Response(UserSerializer(request.user).data)


@api_view(['POST'])
@permission_classes([AllowAny])
def register_view(request):
    username = request.data.get('username')
    password = request.data.get('password')
    email = request.data.get('email', '')
    first_name = request.data.get('first_name', '')
    last_name = request.data.get('last_name', '')

    if not username or not password:
        return Response(
            {'error': 'Username and password are required.'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    if User.objects.filter(username=username).exists():
        return Response(
            {'error': 'Username already exists.'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    user = User.objects.create_user(
        username=username,
        password=password,
        email=email,
        first_name=first_name,
        last_name=last_name,
    )

    login(request, user)
    return Response({
        'user': UserSerializer(user).data,
        'message': 'Registration successful.',
    }, status=status.HTTP_201_CREATED)
