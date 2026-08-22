from django.contrib.auth import authenticate
from django.contrib.auth.models import User
from rest_framework import serializers

from .models import Profile, Ticket


class LoginSerializer(serializers.Serializer):
    name = serializers.CharField()
    password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        name = attrs.get('name')
        password = attrs.get('password')
        user = authenticate(username=name, password=password)
        if not user:
            raise serializers.ValidationError('Invalid name or password.')
        if not user.is_active:
            raise serializers.ValidationError('User account is disabled.')
        attrs['user'] = user
        return attrs


class ProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = Profile
        fields = ['phone_number', 'location', 'nida_number']


class UserSerializer(serializers.ModelSerializer):
    profile = ProfileSerializer(read_only=True)

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'profile']


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
