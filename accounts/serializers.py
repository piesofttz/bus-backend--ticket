from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from rest_framework import serializers

from .models import Ticket


class LoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        username = attrs.get('username')
        password = attrs.get('password')
        user = authenticate(username=username, password=password)
        if not user:
            raise serializers.ValidationError('Invalid username or password.')
        if not user.is_active:
            raise serializers.ValidationError('User account is disabled.')
        attrs['user'] = user
        return attrs


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name']


class TicketSerializer(serializers.ModelSerializer):
    ticket_number = serializers.CharField(read_only=True)
    user = serializers.CharField(source='user.username', read_only=True)
    route_display = serializers.CharField(source='get_route_display', read_only=True)

    class Meta:
        model = Ticket
        fields = [
            'id',
            'user',
            'ticket_number',
            'full_name',
            'phone_number',
            'route',
            'route_display',
            'seat_number',
            'travel_date',
            'created_at',
        ]
        read_only_fields = ['id', 'user', 'ticket_number', 'created_at']
