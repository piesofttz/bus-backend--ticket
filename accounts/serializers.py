from django.contrib.auth.models import User
from rest_framework import serializers

from .models import Booking, Bus, Profile, Route, Seat
from .utils import normalize_phone_number


class LoginSerializer(serializers.Serializer):
    phone_number = serializers.CharField()

    def validate(self, attrs):
        phone_number = attrs.get('phone_number')
        normalized = normalize_phone_number(phone_number)
        if not normalized:
            raise serializers.ValidationError(
                'Invalid phone number. Use the 9 digits after +255, e.g. 674303431.'
            )

        try:
            profile = Profile.objects.get(phone_number=normalized)
        except Profile.DoesNotExist:
            raise serializers.ValidationError('This phone number is not registered.')

        user = profile.user
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


class RouteSerializer(serializers.ModelSerializer):
    class Meta:
        model = Route
        fields = ['id', 'origin', 'destination', 'price', 'duration_hours', 'duration_minutes']


class SeatSerializer(serializers.ModelSerializer):
    class Meta:
        model = Seat
        fields = ['id', 'seat_number', 'position', 'is_available']


class BusSerializer(serializers.ModelSerializer):
    route_display = serializers.CharField(source='route.__str__', read_only=True)
    available_seats = serializers.SerializerMethodField()

    class Meta:
        model = Bus
        fields = [
            'id', 'bus_number', 'operator', 'route', 'route_display',
            'total_seats', 'departure_time', 'arrival_time',
            'is_active', 'available_seats',
        ]

    def get_available_seats(self, obj) -> int:
        return obj.seats.filter(is_available=True).count()


class BookingSerializer(serializers.ModelSerializer):
    ticket_number = serializers.CharField(read_only=True)
    user = serializers.CharField(source='user.username', read_only=True)
    bus_number = serializers.CharField(source='bus.bus_number', read_only=True)
    operator = serializers.CharField(source='bus.operator', read_only=True)
    route_display = serializers.CharField(source='bus.route.__str__', read_only=True)
    seat_number = serializers.CharField(source='seat.seat_number', read_only=True)
    price = serializers.DecimalField(
        source='bus.route.price', max_digits=10, decimal_places=2, read_only=True,
    )
    departure_time = serializers.TimeField(source='bus.departure_time', read_only=True)
    arrival_time = serializers.TimeField(source='bus.arrival_time', read_only=True)

    class Meta:
        model = Booking
        fields = [
            'id', 'user', 'ticket_number', 'full_name', 'phone_number',
            'travel_date', 'travel_time',
            'bus', 'bus_number', 'operator', 'route_display',
            'seat', 'seat_number', 'price',
            'departure_time', 'arrival_time',
            'status', 'checked_in_at', 'created_at',
        ]
        read_only_fields = [
            'id', 'user', 'ticket_number', 'status', 'checked_in_at', 'created_at',
        ]

    def validate(self, attrs):
        seat = attrs.get('seat')
        bus = attrs.get('bus')
        if seat and bus:
            if seat.bus_id != bus.id:
                raise serializers.ValidationError('Seat does not belong to this bus.')
            if not seat.is_available:
                raise serializers.ValidationError('Seat is already booked.')
        return attrs

    def create(self, validated_data):
        seat = validated_data['seat']
        seat.is_available = False
        seat.save()
        return super().create(validated_data)
