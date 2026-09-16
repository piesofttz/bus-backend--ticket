from django.contrib.auth.models import User
from rest_framework import serializers

from accounts.models import Booking, Bus, Route, Seat

from .models import AdminLog


class AdminLoginSerializer(serializers.Serializer):
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)


class AdminLogSerializer(serializers.ModelSerializer):
    username = serializers.CharField(source='user.username', read_only=True)

    class Meta:
        model = AdminLog
        fields = [
            'id', 'user', 'username', 'action', 'description',
            'ip_address', 'created_at',
        ]


class AdminBookingSerializer(serializers.ModelSerializer):
    user = serializers.CharField(source='user.username', read_only=True)
    user_id = serializers.IntegerField(source='user.id', read_only=True)
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
            'id', 'user', 'user_id', 'ticket_number', 'full_name', 'phone_number',
            'travel_date', 'travel_time',
            'bus', 'bus_number', 'operator', 'route_display',
            'seat', 'seat_number', 'price',
            'departure_time', 'arrival_time',
            'status', 'checked_in_at', 'created_at',
        ]
        read_only_fields = ['id', 'user', 'ticket_number', 'created_at']


class AdminBookingEditSerializer(serializers.ModelSerializer):
    class Meta:
        model = Booking
        fields = ['full_name', 'phone_number', 'bus', 'seat', 'travel_date', 'travel_time', 'status']
        extra_kwargs = {
            'bus': {'required': False},
            'seat': {'required': False},
        }

    def validate(self, attrs):
        bus = attrs.get('bus')
        seat = attrs.get('seat')
        if seat and not bus:
            bus = self.instance.bus if self.instance else None
        if bus and seat:
            if seat.bus_id != bus.id:
                raise serializers.ValidationError('Seat does not belong to this bus.')
        return attrs

    def update(self, instance, validated_data):
        old_seat = instance.seat
        seat = validated_data.get('seat')
        if seat and seat != old_seat:
            if Booking.objects.filter(seat=seat, status='cancelled').exists():
                pass
            if not seat.is_available:
                raise serializers.ValidationError('New seat is already booked.')
            old_seat.is_available = True
            old_seat.save()
            instance.seat = seat
            seat.is_available = False
            seat.save()
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        return instance


class AdminPassengerSerializer(serializers.ModelSerializer):
    total_bookings = serializers.SerializerMethodField()
    date_joined = serializers.DateTimeField(source='date_joined', read_only=True)

    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name',
            'is_staff', 'is_active', 'date_joined', 'total_bookings',
        ]

    def get_total_bookings(self, obj):
        return obj.bookings.count()

    def to_representation(self, instance):
        data = super().to_representation(instance)
        profile = instance.profile
        data['phone_number'] = profile.phone_number
        data['location'] = profile.location
        data['nida_number'] = profile.nida_number
        return data


class AdminPassengerCreateSerializer(serializers.ModelSerializer):
    phone_number = serializers.CharField(required=False, allow_blank=True, default='')
    location = serializers.CharField(required=False, allow_blank=True, default='')
    nida_number = serializers.CharField(required=False, allow_blank=True, default='')
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = [
            'username', 'password', 'email', 'first_name', 'last_name',
            'phone_number', 'location', 'nida_number',
        ]

    def create(self, validated_data):
        password = validated_data.pop('password')
        phone_number = validated_data.pop('phone_number', '')
        location = validated_data.pop('location', '')
        nida_number = validated_data.pop('nida_number', '')
        user = User.objects.create_user(**validated_data, password=password)
        user.profile.phone_number = phone_number
        user.profile.location = location
        user.profile.nida_number = nida_number
        user.profile.save()
        return user


class AdminPassengerEditSerializer(serializers.ModelSerializer):
    phone_number = serializers.CharField(required=False, allow_blank=True, default='')
    location = serializers.CharField(required=False, allow_blank=True, default='')
    nida_number = serializers.CharField(required=False, allow_blank=True, default='')
    is_active = serializers.BooleanField(required=False)

    class Meta:
        model = User
        fields = [
            'username', 'email', 'first_name', 'last_name',
            'phone_number', 'location', 'nida_number',
            'is_active',
        ]

    def update(self, instance, validated_data):
        phone_number = validated_data.pop('phone_number', None)
        location = validated_data.pop('location', None)
        nida_number = validated_data.pop('nida_number', None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        profile = instance.profile
        if phone_number is not None:
            profile.phone_number = phone_number
        if location is not None:
            profile.location = location
        if nida_number is not None:
            profile.nida_number = nida_number
        profile.save()
        return instance


class AdminBusSerializer(serializers.ModelSerializer):
    route_display = serializers.CharField(source='route.__str__', read_only=True)
    available_seats = serializers.SerializerMethodField()
    total_seat_count = serializers.SerializerMethodField()

    class Meta:
        model = Bus
        fields = [
            'id', 'bus_number', 'operator', 'route', 'route_display',
            'total_seats', 'departure_time', 'arrival_time',
            'is_active', 'available_seats', 'total_seat_count',
        ]

    def get_available_seats(self, obj):
        return obj.seats.filter(is_available=True).count()

    def get_total_seat_count(self, obj):
        return obj.seats.count()


class AdminSeatCreateSerializer(serializers.Serializer):
    seat_numbers = serializers.ListField(
        child=serializers.CharField(max_length=10),
        allow_empty=False,
    )
    is_available = serializers.BooleanField(default=True)


class AdminRouteCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Route
        fields = ['id', 'origin', 'destination', 'price', 'duration_hours', 'duration_minutes']
        read_only_fields = ['id']


class AdminProfileEditSerializer(serializers.ModelSerializer):
    phone_number = serializers.CharField(required=False, allow_blank=True, default='')
    location = serializers.CharField(required=False, allow_blank=True, default='')
    nida_number = serializers.CharField(required=False, allow_blank=True, default='')

    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name', 'phone_number', 'location', 'nida_number']
        read_only_fields = ['username']

    def to_representation(self, instance):
        data = super().to_representation(instance)
        profile = instance.profile
        data['phone_number'] = profile.phone_number
        data['location'] = profile.location
        data['nida_number'] = profile.nida_number
        return data

    def update(self, instance, validated_data):
        phone_number = validated_data.pop('phone_number', None)
        location = validated_data.pop('location', None)
        nida_number = validated_data.pop('nida_number', None)
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        profile = instance.profile
        if phone_number is not None:
            profile.phone_number = phone_number
        if location is not None:
            profile.location = location
        if nida_number is not None:
            profile.nida_number = nida_number
        profile.save()
        return instance


class AdminPasswordChangeSerializer(serializers.Serializer):
    current_password = serializers.CharField(write_only=True)
    new_password = serializers.CharField(write_only=True, min_length=6)

    def validate_current_password(self, value):
        user = self.context['request'].user
        if not user.check_password(value):
            raise serializers.ValidationError('Current password is incorrect.')
        return value


class AdminResetPasswordSerializer(serializers.Serializer):
    new_password = serializers.CharField(write_only=True, min_length=6)