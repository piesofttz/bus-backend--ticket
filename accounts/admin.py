from django.contrib import admin
from django.contrib.auth.models import User

from .models import Booking, Bus, Profile, Route, Seat


class ProfileInline(admin.StackedInline):
    model = Profile
    can_delete = False


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ['id', 'user', 'phone_number', 'location', 'nida_number']
    search_fields = ['user__username', 'phone_number', 'nida_number', 'location']


admin.site.unregister(User)


@admin.register(User)
class CustomUserAdmin(admin.ModelAdmin):
    inlines = [ProfileInline]
    list_display = ['id', 'username', 'email', 'is_staff', 'is_active']
    search_fields = ['username', 'email']


@admin.register(Route)
class RouteAdmin(admin.ModelAdmin):
    list_display = ['id', 'origin', 'destination', 'price', 'duration_hours', 'duration_minutes']
    search_fields = ['origin', 'destination']
    list_filter = ['origin', 'destination']


@admin.register(Bus)
class BusAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'bus_number', 'operator', 'route', 'total_seats',
        'departure_time', 'arrival_time', 'is_active',
    ]
    search_fields = ['bus_number', 'operator']
    list_filter = ['operator', 'route', 'is_active']


@admin.register(Seat)
class SeatAdmin(admin.ModelAdmin):
    list_display = ['id', 'bus', 'seat_number', 'is_available']
    search_fields = ['bus__bus_number', 'seat_number']
    list_filter = ['bus', 'is_available']


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'ticket_number', 'user', 'full_name', 'phone_number',
        'bus', 'seat', 'travel_date', 'travel_time', 'status', 'created_at',
    ]
    search_fields = ['ticket_number', 'full_name', 'phone_number', 'user__username']
    list_filter = ['status', 'travel_date', 'bus']
    readonly_fields = ['ticket_number']
