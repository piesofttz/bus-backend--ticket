from django.contrib.auth import login
from django.contrib.auth.models import User
from django.db import models
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

from accounts.models import Booking, Bus, Route, Seat
from accounts.serializers import LoginSerializer, UserSerializer

from .models import AdminLog
from .permissions import IsAdminUser
from .serializers import (
    AdminBookingEditSerializer,
    AdminBookingSerializer,
    AdminBusSerializer,
    AdminLogSerializer,
    AdminPassengerCreateSerializer,
    AdminPassengerEditSerializer,
    AdminPassengerSerializer,
    AdminProfileEditSerializer,
    AdminResetPasswordSerializer,
    AdminRouteCreateSerializer,
    AdminSeatCreateSerializer,
    AdminPasswordChangeSerializer,
)
from .utils import log_admin_action


class AdminLoginView(APIView):
    permission_classes = []

    @extend_schema(
        summary='Admin Login',
        description='Login as a staff/superuser. Creates an admin log entry. Returns JWT tokens.',
        request=LoginSerializer,
        responses={200: UserSerializer},
        tags=['Admin'],
    )
    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        if not (user.is_staff or user.is_superuser):
            return Response(
                {'error': 'This account is not an admin.'},
                status=status.HTTP_403_FORBIDDEN,
            )
        login(request, user)
        refresh = RefreshToken.for_user(user)
        log_admin_action(user, 'login', 'Admin logged in', request)
        return Response({
            'access_token': str(refresh.access_token),
            'refresh_token': str(refresh),
            'user': UserSerializer(user).data,
            'message': 'Admin login successful.',
        }, status=status.HTTP_200_OK)


class AdminLogListView(APIView):
    permission_classes = [IsAdminUser]

    @extend_schema(
        summary='List Admin Logs',
        description='Get all admin activity logs. Optional filters: search (username), action, start_date, end_date.',
        parameters=[
            OpenApiParameter(name='search', type=str, description='Search by username', required=False),
            OpenApiParameter(name='action', type=str, description='Filter by action (login, logout, create, update, delete, reset_password, check_in, confirm)', required=False),
            OpenApiParameter(name='start_date', type=str, description='Filter by created_at >= date (YYYY-MM-DD)', required=False),
            OpenApiParameter(name='end_date', type=str, description='Filter by created_at <= date (YYYY-MM-DD)', required=False),
        ],
        responses={200: AdminLogSerializer(many=True)},
        tags=['Admin'],
    )
    def get(self, request):
        logs = AdminLog.objects.all()
        search = request.query_params.get('search', '').strip()
        action = request.query_params.get('action', '').strip()
        start_date = request.query_params.get('start_date', '').strip()
        end_date = request.query_params.get('end_date', '').strip()

        if search:
            logs = logs.filter(user__username__icontains=search)
        if action:
            logs = logs.filter(action=action)
        if start_date:
            logs = logs.filter(created_at__date__gte=start_date)
        if end_date:
            logs = logs.filter(created_at__date__lte=end_date)

        serializer = AdminLogSerializer(logs, many=True)
        return Response(serializer.data)


class AdminStatsView(APIView):
    permission_classes = [IsAdminUser]

    @extend_schema(
        summary='Dashboard Stats',
        description='Get dashboard summary counts for the admin panel.',
        responses={200: {'type': 'object', 'properties': {
            'total_passengers': {'type': 'integer'},
            'total_bookings': {'type': 'integer'},
            'confirmed_bookings': {'type': 'integer'},
            'pending_bookings': {'type': 'integer'},
            'checked_in_bookings': {'type': 'integer'},
            'cancelled_bookings': {'type': 'integer'},
            'total_routes': {'type': 'integer'},
            'total_buses': {'type': 'integer'},
            'total_seats': {'type': 'integer'},
            'total_revenue': {'type': 'number'},
        }}},
        tags=['Admin'],
    )
    def get(self, request):
        from decimal import Decimal
        from django.db.models import Sum

        revenue = Booking.objects.exclude(status='cancelled').aggregate(
            total=Sum('bus__route__price')
        )['total'] or Decimal('0.00')

        return Response({
            'total_passengers': User.objects.filter(is_staff=False).count(),
            'total_bookings': Booking.objects.count(),
            'confirmed_bookings': Booking.objects.filter(status='confirmed').count(),
            'pending_bookings': Booking.objects.filter(status='pending').count(),
            'checked_in_bookings': Booking.objects.filter(status='checked_in').count(),
            'cancelled_bookings': Booking.objects.filter(status='cancelled').count(),
            'total_routes': Route.objects.count(),
            'total_buses': Bus.objects.count(),
            'total_seats': Seat.objects.count(),
            'total_revenue': revenue,
        })


class AdminBookingListView(APIView):
    permission_classes = [IsAdminUser]

    @extend_schema(
        summary='List All Bookings',
        description='Get all bookings (agent + admin). Optional filters: search (ticket/user/name/phone), status, route_id, bus_id, start_date, end_date.',
        parameters=[
            OpenApiParameter(name='search', type=str, description='Search by ticket number, username, full name or phone', required=False),
            OpenApiParameter(name='status', type=str, description='Filter by status (pending, confirmed, checked_in, cancelled)', required=False),
            OpenApiParameter(name='route_id', type=int, description='Filter by route ID', required=False),
            OpenApiParameter(name='bus_id', type=int, description='Filter by bus ID', required=False),
            OpenApiParameter(name='start_date', type=str, description='Travel date >= date (YYYY-MM-DD)', required=False),
            OpenApiParameter(name='end_date', type=str, description='Travel date <= date (YYYY-MM-DD)', required=False),
        ],
        responses={200: AdminBookingSerializer(many=True)},
        tags=['Admin Bookings'],
    )
    def get(self, request):
        bookings = Booking.objects.all()
        search = request.query_params.get('search', '').strip()
        booking_status = request.query_params.get('status', '').strip()
        route_id = request.query_params.get('route_id')
        bus_id = request.query_params.get('bus_id')
        start_date = request.query_params.get('start_date', '').strip()
        end_date = request.query_params.get('end_date', '').strip()

        if search:
            bookings = bookings.filter(
                ticket_number__icontains=search
            ) | bookings.filter(
                user__username__icontains=search
            ) | bookings.filter(
                full_name__icontains=search
            ) | bookings.filter(
                phone_number__icontains=search
            )
        if booking_status:
            bookings = bookings.filter(status=booking_status)
        if route_id:
            bookings = bookings.filter(bus__route_id=route_id)
        if bus_id:
            bookings = bookings.filter(bus_id=bus_id)
        if start_date:
            bookings = bookings.filter(travel_date__gte=start_date)
        if end_date:
            bookings = bookings.filter(travel_date__lte=end_date)

        serializer = AdminBookingSerializer(bookings, many=True)
        return Response(serializer.data)


class AdminBookingDetailView(APIView):
    permission_classes = [IsAdminUser]

    @extend_schema(
        summary='Get Booking Detail',
        description='Get a single booking by ID.',
        responses={200: AdminBookingSerializer, 404: {'type': 'object', 'properties': {'error': {'type': 'string'}}}},
        tags=['Admin Bookings'],
    )
    def get(self, request, pk):
        try:
            booking = Booking.objects.get(pk=pk)
        except Booking.DoesNotExist:
            return Response({'error': 'Booking not found.'}, status=status.HTTP_404_NOT_FOUND)
        return Response(AdminBookingSerializer(booking).data)

    @extend_schema(
        summary='Edit Booking',
        description='Edit a booking. Supported fields: full_name, phone_number, bus, seat, travel_date, travel_time, status.',
        request=AdminBookingEditSerializer,
        responses={200: AdminBookingSerializer, 404: {'type': 'object', 'properties': {'error': {'type': 'string'}}}},
        tags=['Admin Bookings'],
    )
    def patch(self, request, pk):
        try:
            booking = Booking.objects.get(pk=pk)
        except Booking.DoesNotExist:
            return Response({'error': 'Booking not found.'}, status=status.HTTP_404_NOT_FOUND)
        serializer = AdminBookingEditSerializer(booking, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        log_admin_action(request.user, 'update', f'Updated booking {booking.ticket_number}', request)
        return Response(AdminBookingSerializer(booking).data)


class AdminBookingRescheduleView(APIView):
    permission_classes = [IsAdminUser]

    @extend_schema(
        summary='Reschedule Booking',
        description='Change the travel date/time and optionally the seat of a booking. New seat must be available.',
        request={
            'application/json': {
                'type': 'object',
                'properties': {
                    'travel_date': {'type': 'string', 'format': 'date', 'description': 'New travel date'},
                    'travel_time': {'type': 'string', 'format': 'time', 'description': 'New travel time'},
                    'seat': {'type': 'integer', 'description': 'New seat ID (optional)'},
                },
                'required': ['travel_date', 'travel_time'],
            }
        },
        responses={200: AdminBookingSerializer, 404: {'type': 'object', 'properties': {'error': {'type': 'string'}}}},
        tags=['Admin Bookings'],
    )
    def post(self, request, pk):
        try:
            booking = Booking.objects.get(pk=pk)
        except Booking.DoesNotExist:
            return Response({'error': 'Booking not found.'}, status=status.HTTP_404_NOT_FOUND)

        travel_date = request.data.get('travel_date')
        travel_time = request.data.get('travel_time')
        new_seat_id = request.data.get('seat')

        if not travel_date or not travel_time:
            return Response(
                {'error': 'travel_date and travel_time are required.'},
                status=status.HTTP_400_BAD_REQUEST,
            )

        if new_seat_id:
            try:
                new_seat = Seat.objects.get(pk=new_seat_id)
            except Seat.DoesNotExist:
                return Response({'error': 'Seat not found.'}, status=status.HTTP_404_NOT_FOUND)
            if new_seat.bus_id != booking.bus_id:
                return Response(
                    {'error': 'Seat does not belong to the booking bus.'},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            if new_seat != booking.seat:
                if not new_seat.is_available:
                    return Response(
                        {'error': 'New seat is already booked.'},
                        status=status.HTTP_400_BAD_REQUEST,
                    )
                old_seat = booking.seat
                old_seat.is_available = True
                old_seat.save()
                booking.seat = new_seat
                new_seat.is_available = False
                new_seat.save()

        booking.travel_date = travel_date
        booking.travel_time = travel_time
        booking.save()
        log_admin_action(request.user, 'update', f'Rescheduled booking {booking.ticket_number}', request)
        return Response(AdminBookingSerializer(booking).data)


class AdminBookingStatusMixin:
    permission_classes = [IsAdminUser]

    def get_booking(self, pk):
        try:
            return Booking.objects.get(pk=pk)
        except Booking.DoesNotExist:
            return None


class AdminBookingConfirmView(AdminBookingStatusMixin, APIView):
    @extend_schema(
        summary='Confirm Booking',
        description='Mark a booking as confirmed.',
        request=None,
        responses={200: AdminBookingSerializer, 404: {'type': 'object', 'properties': {'error': {'type': 'string'}}}},
        tags=['Admin Bookings'],
    )
    def post(self, request, pk):
        booking = self.get_booking(pk)
        if not booking:
            return Response({'error': 'Booking not found.'}, status=status.HTTP_404_NOT_FOUND)
        booking.status = 'confirmed'
        booking.save()
        log_admin_action(request.user, 'confirm', f'Confirmed booking {booking.ticket_number}', request)
        return Response(AdminBookingSerializer(booking).data)


class AdminBookingCheckInView(AdminBookingStatusMixin, APIView):
    @extend_schema(
        summary='Check-in Booking',
        description='Mark a booking as checked-in (passenger boarded). Records checked_in_at timestamp.',
        request=None,
        responses={200: AdminBookingSerializer, 404: {'type': 'object', 'properties': {'error': {'type': 'string'}}}},
        tags=['Admin Bookings'],
    )
    def post(self, request, pk):
        booking = self.get_booking(pk)
        if not booking:
            return Response({'error': 'Booking not found.'}, status=status.HTTP_404_NOT_FOUND)
        booking.status = 'checked_in'
        from django.utils import timezone
        booking.checked_in_at = timezone.now()
        booking.save()
        log_admin_action(request.user, 'check_in', f'Checked-in booking {booking.ticket_number}', request)
        return Response(AdminBookingSerializer(booking).data)


class AdminBookingCancelView(AdminBookingStatusMixin, APIView):
    @extend_schema(
        summary='Cancel Booking',
        description='Cancel a booking and free its seat.',
        request=None,
        responses={200: AdminBookingSerializer, 404: {'type': 'object', 'properties': {'error': {'type': 'string'}}}},
        tags=['Admin Bookings'],
    )
    def post(self, request, pk):
        booking = self.get_booking(pk)
        if not booking:
            return Response({'error': 'Booking not found.'}, status=status.HTTP_404_NOT_FOUND)
        if booking.status == 'cancelled':
            return Response({'error': 'Booking is already cancelled.'}, status=status.HTTP_400_BAD_REQUEST)
        booking.status = 'cancelled'
        booking.save()
        seat = booking.seat
        seat.is_available = True
        seat.save()
        log_admin_action(request.user, 'update', f'Cancelled booking {booking.ticket_number}', request)
        return Response(AdminBookingSerializer(booking).data)


class AdminPassengerListView(APIView):
    permission_classes = [IsAdminUser]

    @extend_schema(
        summary='List All Passengers',
        description='Get all registered passengers/users. Optional filters: search (username, name, phone, email).',
        parameters=[
            OpenApiParameter(name='search', type=str, description='Search by username, first/last name, phone or email', required=False),
        ],
        responses={200: AdminPassengerSerializer(many=True)},
        tags=['Admin Passengers'],
    )
    def get(self, request):
        users = User.objects.filter(is_staff=False)
        search = request.query_params.get('search', '').strip()
        if search:
            users = users.filter(
                username__icontains=search
            ) | users.filter(
                first_name__icontains=search
            ) | users.filter(
                last_name__icontains=search
            ) | users.filter(
                email__icontains=search
            ) | users.filter(
                profile__phone_number__icontains=search
            )
        serializer = AdminPassengerSerializer(users, many=True)
        return Response(serializer.data)

    @extend_schema(
        summary='Create Passenger',
        description='Create a new passenger user with profile info.',
        request=AdminPassengerCreateSerializer,
        responses={201: AdminPassengerSerializer, 400: {'type': 'object', 'properties': {'error': {'type': 'string'}}}},
        tags=['Admin Passengers'],
    )
    def post(self, request):
        serializer = AdminPassengerCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        log_admin_action(request.user, 'create', f'Created passenger {user.username}', request)
        return Response(AdminPassengerSerializer(user).data, status=status.HTTP_201_CREATED)


class AdminPassengerDetailView(APIView):
    permission_classes = [IsAdminUser]

    @extend_schema(
        summary='Get Passenger Detail',
        description='Get a single passenger with their profile and bookings.',
        responses={200: AdminPassengerSerializer, 404: {'type': 'object', 'properties': {'error': {'type': 'string'}}}},
        tags=['Admin Passengers'],
    )
    def get(self, request, pk):
        try:
            user = User.objects.get(pk=pk)
        except User.DoesNotExist:
            return Response({'error': 'Passenger not found.'}, status=status.HTTP_404_NOT_FOUND)
        data = AdminPassengerSerializer(user).data
        bookings = Booking.objects.filter(user=user)
        data['bookings'] = AdminBookingSerializer(bookings, many=True).data
        return Response(data)

    @extend_schema(
        summary='Edit Passenger',
        description='Edit a passenger profile. Fields: username, email, first_name, last_name, phone_number, location, nida_number, is_active.',
        request=AdminPassengerEditSerializer,
        responses={200: AdminPassengerSerializer, 404: {'type': 'object', 'properties': {'error': {'type': 'string'}}}},
        tags=['Admin Passengers'],
    )
    def patch(self, request, pk):
        try:
            user = User.objects.get(pk=pk)
        except User.DoesNotExist:
            return Response({'error': 'Passenger not found.'}, status=status.HTTP_404_NOT_FOUND)
        serializer = AdminPassengerEditSerializer(user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        log_admin_action(request.user, 'update', f'Updated passenger {user.username}', request)
        return Response(AdminPassengerSerializer(user).data)

    @extend_schema(
        summary='Delete Passenger',
        description='Delete a passenger user.',
        responses={200: {'type': 'object', 'properties': {'message': {'type': 'string'}}}, 404: {'type': 'object', 'properties': {'error': {'type': 'string'}}}},
        tags=['Admin Passengers'],
    )
    def delete(self, request, pk):
        try:
            user = User.objects.get(pk=pk)
        except User.DoesNotExist:
            return Response({'error': 'Passenger not found.'}, status=status.HTTP_404_NOT_FOUND)
        username = user.username
        user.delete()
        log_admin_action(request.user, 'delete', f'Deleted passenger {username}', request)
        return Response({'message': 'Passenger deleted successfully.'})


class AdminPassengerResetPasswordView(APIView):
    permission_classes = [IsAdminUser]

    @extend_schema(
        summary='Reset Passenger Password',
        description='Set a new password for a passenger.',
        request=AdminResetPasswordSerializer,
        responses={200: {'type': 'object', 'properties': {'message': {'type': 'string'}}}, 404: {'type': 'object', 'properties': {'error': {'type': 'string'}}}},
        tags=['Admin Passengers'],
    )
    def post(self, request, pk):
        try:
            user = User.objects.get(pk=pk)
        except User.DoesNotExist:
            return Response({'error': 'Passenger not found.'}, status=status.HTTP_404_NOT_FOUND)
        serializer = AdminResetPasswordSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user.set_password(serializer.validated_data['new_password'])
        user.save()
        log_admin_action(request.user, 'reset_password', f'Reset password for {user.username}', request)
        return Response({'message': 'Password reset successfully.'})


class AdminBusListView(APIView):
    permission_classes = [IsAdminUser]

    @extend_schema(
        summary='List All Buses (Admin)',
        description='Get all buses including inactive. Optional filters: search, route_id, origin, destination.',
        parameters=[
            OpenApiParameter(name='search', type=str, description='Search by bus number or operator', required=False),
            OpenApiParameter(name='route_id', type=int, description='Filter by route ID', required=False),
            OpenApiParameter(name='origin', type=str, description='Filter by origin city', required=False),
            OpenApiParameter(name='destination', type=str, description='Filter by destination city', required=False),
        ],
        responses={200: AdminBusSerializer(many=True)},
        tags=['Admin Buses'],
    )
    def get(self, request):
        buses = Bus.objects.all()
        search = request.query_params.get('search', '').strip()
        route_id = request.query_params.get('route_id')
        origin = request.query_params.get('origin', '').strip()
        destination = request.query_params.get('destination', '').strip()

        if search:
            buses = buses.filter(
                bus_number__icontains=search
            ) | buses.filter(
                operator__icontains=search
            )
        if route_id:
            buses = buses.filter(route_id=route_id)
        if origin:
            buses = buses.filter(route__origin__icontains=origin)
        if destination:
            buses = buses.filter(route__destination__icontains=destination)

        return Response(AdminBusSerializer(buses, many=True).data)

    @extend_schema(
        summary='Create Bus',
        description='Create a new bus. Optionally pass `create_seats: true` to auto-create seat records based on total_seats.',
        request=AdminBusSerializer,
        responses={201: AdminBusSerializer, 400: {'type': 'object', 'properties': {'error': {'type': 'string'}}}},
        tags=['Admin Buses'],
    )
    def post(self, request):
        serializer = AdminBusSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        bus = serializer.save()
        create_seats = request.data.get('create_seats', False)
        if create_seats:
            for i in range(1, bus.total_seats + 1):
                Seat.objects.get_or_create(
                    bus=bus,
                    seat_number=str(i),
                    defaults={'is_available': True, 'position': i},
                )
        log_admin_action(request.user, 'create', f'Created bus {bus.bus_number}', request)
        return Response(AdminBusSerializer(bus).data, status=status.HTTP_201_CREATED)


class AdminBusDetailView(APIView):
    permission_classes = [IsAdminUser]

    def _get_bus(self, pk):
        try:
            return Bus.objects.get(pk=pk)
        except Bus.DoesNotExist:
            return None

    @extend_schema(
        summary='Get Bus Detail',
        description='Get a single bus with its seats.',
        responses={200: AdminBusSerializer, 404: {'type': 'object', 'properties': {'error': {'type': 'string'}}}},
        tags=['Admin Buses'],
    )
    def get(self, request, pk):
        bus = self._get_bus(pk)
        if not bus:
            return Response({'error': 'Bus not found.'}, status=status.HTTP_404_NOT_FOUND)
        data = AdminBusSerializer(bus).data
        data['seats'] = list(bus.seats.values('id', 'seat_number', 'is_available'))
        return Response(data)

    @extend_schema(
        summary='Edit Bus',
        description='Edit bus details. Fields: bus_number, operator, route, total_seats, departure_time, arrival_time, is_active.',
        request=AdminBusSerializer,
        responses={200: AdminBusSerializer, 404: {'type': 'object', 'properties': {'error': {'type': 'string'}}}},
        tags=['Admin Buses'],
    )
    def patch(self, request, pk):
        bus = self._get_bus(pk)
        if not bus:
            return Response({'error': 'Bus not found.'}, status=status.HTTP_404_NOT_FOUND)
        serializer = AdminBusSerializer(bus, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        log_admin_action(request.user, 'update', f'Updated bus {bus.bus_number}', request)
        return Response(AdminBusSerializer(bus).data)

    @extend_schema(
        summary='Delete Bus',
        description='Delete a bus.',
        responses={200: {'type': 'object', 'properties': {'message': {'type': 'string'}}}, 404: {'type': 'object', 'properties': {'error': {'type': 'string'}}}},
        tags=['Admin Buses'],
    )
    def delete(self, request, pk):
        bus = self._get_bus(pk)
        if not bus:
            return Response({'error': 'Bus not found.'}, status=status.HTTP_404_NOT_FOUND)
        bus_number = bus.bus_number
        bus.delete()
        log_admin_action(request.user, 'delete', f'Deleted bus {bus_number}', request)
        return Response({'message': 'Bus deleted successfully.'})


class AdminBusSeatCreateView(APIView):
    permission_classes = [IsAdminUser]

    @extend_schema(
        summary='Add Seats to Bus',
        description='Bulk create seats for a bus. Body: {"seat_numbers": ["1A", "1B", ...], "is_available": true}',
        request=AdminSeatCreateSerializer,
        responses={201: AdminBusSerializer, 404: {'type': 'object', 'properties': {'error': {'type': 'string'}}}},
        tags=['Admin Buses'],
    )
    def post(self, request, pk):
        try:
            bus = Bus.objects.get(pk=pk)
        except Bus.DoesNotExist:
            return Response({'error': 'Bus not found.'}, status=status.HTTP_404_NOT_FOUND)
        serializer = AdminSeatCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        created = []
        next_position = bus.seats.aggregate(models.Max('position'))['position__max'] or 0
        for seat_number in serializer.validated_data['seat_numbers']:
            next_position += 1
            seat, was_created = Seat.objects.get_or_create(
                bus=bus,
                seat_number=seat_number,
                defaults={'is_available': serializer.validated_data['is_available'], 'position': next_position},
            )
            created.append({'seat_number': seat.seat_number, 'created': was_created})
        bus.total_seats = bus.seats.count()
        bus.save()
        log_admin_action(request.user, 'create', f'Added seats to bus {bus.bus_number}', request)
        return Response({'seats': created}, status=status.HTTP_201_CREATED)


class AdminSeatDetailView(APIView):
    permission_classes = [IsAdminUser]

    @extend_schema(
        summary='Edit Seat',
        description='Edit a seat (seat_number, is_available).',
        request=AdminSeatCreateSerializer,
        responses={200: AdminBusSerializer, 404: {'type': 'object', 'properties': {'error': {'type': 'string'}}}},
        tags=['Admin Buses'],
    )
    def patch(self, request, pk):
        try:
            seat = Seat.objects.get(pk=pk)
        except Seat.DoesNotExist:
            return Response({'error': 'Seat not found.'}, status=status.HTTP_404_NOT_FOUND)
        seat_number = request.data.get('seat_number', seat.seat_number)
        is_available = request.data.get('is_available', seat.is_available)
        if Booking.objects.filter(seat=seat).exclude(status='cancelled').exists() and request.data.get('is_available') is True:
            return Response(
                {'error': 'This seat has an active booking.'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        seat.seat_number = seat_number
        seat.is_available = is_available
        seat.save()
        log_admin_action(request.user, 'update', f'Updated seat {seat.seat_number} on bus {seat.bus.bus_number}', request)
        return Response({'id': seat.id, 'seat_number': seat.seat_number, 'is_available': seat.is_available})

    @extend_schema(
        summary='Delete Seat',
        description='Delete a seat.',
        responses={200: {'type': 'object', 'properties': {'message': {'type': 'string'}}}, 404: {'type': 'object', 'properties': {'error': {'type': 'string'}}}},
        tags=['Admin Buses'],
    )
    def delete(self, request, pk):
        try:
            seat = Seat.objects.get(pk=pk)
        except Seat.DoesNotExist:
            return Response({'error': 'Seat not found.'}, status=status.HTTP_404_NOT_FOUND)
        seat_number = seat.seat_number
        bus = seat.bus
        seat.delete()
        bus.total_seats = bus.seats.count()
        bus.save()
        log_admin_action(request.user, 'delete', f'Deleted seat {seat_number} on bus {bus.bus_number}', request)
        return Response({'message': 'Seat deleted successfully.'})


class AdminRouteListView(APIView):
    permission_classes = [IsAdminUser]

    @extend_schema(
        summary='List All Routes (Admin)',
        description='Get all routes.',
        responses={200: AdminRouteCreateSerializer(many=True)},
        tags=['Admin Routes'],
    )
    def get(self, request):
        routes = Route.objects.all()
        return Response(AdminRouteCreateSerializer(routes, many=True).data)

    @extend_schema(
        summary='Create Route',
        description='Create a new route. Fields: origin, destination, price, duration_hours, duration_minutes.',
        request=AdminRouteCreateSerializer,
        responses={201: AdminRouteCreateSerializer, 400: {'type': 'object', 'properties': {'error': {'type': 'string'}}}},
        tags=['Admin Routes'],
    )
    def post(self, request):
        serializer = AdminRouteCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        route = serializer.save()
        log_admin_action(request.user, 'create', f'Created route {route.origin} to {route.destination}', request)
        return Response(AdminRouteCreateSerializer(route).data, status=status.HTTP_201_CREATED)


class AdminRouteDetailView(APIView):
    permission_classes = [IsAdminUser]

    def _get_route(self, pk):
        try:
            return Route.objects.get(pk=pk)
        except Route.DoesNotExist:
            return None

    @extend_schema(
        summary='Get Route Detail',
        description='Get a single route.',
        responses={200: AdminRouteCreateSerializer, 404: {'type': 'object', 'properties': {'error': {'type': 'string'}}}},
        tags=['Admin Routes'],
    )
    def get(self, request, pk):
        route = self._get_route(pk)
        if not route:
            return Response({'error': 'Route not found.'}, status=status.HTTP_404_NOT_FOUND)
        return Response(AdminRouteCreateSerializer(route).data)

    @extend_schema(
        summary='Edit Route',
        description='Edit route details.',
        request=AdminRouteCreateSerializer,
        responses={200: AdminRouteCreateSerializer, 404: {'type': 'object', 'properties': {'error': {'type': 'string'}}}},
        tags=['Admin Routes'],
    )
    def patch(self, request, pk):
        route = self._get_route(pk)
        if not route:
            return Response({'error': 'Route not found.'}, status=status.HTTP_404_NOT_FOUND)
        serializer = AdminRouteCreateSerializer(route, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        log_admin_action(request.user, 'update', f'Updated route {route.origin} to {route.destination}', request)
        return Response(AdminRouteCreateSerializer(route).data)

    @extend_schema(
        summary='Delete Route',
        description='Delete a route.',
        responses={200: {'type': 'object', 'properties': {'message': {'type': 'string'}}}, 404: {'type': 'object', 'properties': {'error': {'type': 'string'}}}},
        tags=['Admin Routes'],
    )
    def delete(self, request, pk):
        route = self._get_route(pk)
        if not route:
            return Response({'error': 'Route not found.'}, status=status.HTTP_404_NOT_FOUND)
        origin = route.origin
        destination = route.destination
        route.delete()
        log_admin_action(request.user, 'delete', f'Deleted route {origin} to {destination}', request)
        return Response({'message': 'Route deleted successfully.'})


class AdminProfileView(APIView):
    permission_classes = [IsAdminUser]

    @extend_schema(
        summary='Get Admin Profile',
        description='Get the logged-in admin profile.',
        responses={200: AdminProfileEditSerializer},
        tags=['Admin Profile'],
    )
    def get(self, request):
        return Response(AdminProfileEditSerializer(request.user).data)

    @extend_schema(
        summary='Edit Admin Profile',
        description='Edit own profile. Fields: email, first_name, last_name, phone_number, location, nida_number.',
        request=AdminProfileEditSerializer,
        responses={200: AdminProfileEditSerializer},
        tags=['Admin Profile'],
    )
    def patch(self, request):
        serializer = AdminProfileEditSerializer(request.user, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        log_admin_action(request.user, 'update', 'Updated own profile', request)
        return Response(AdminProfileEditSerializer(request.user).data)


class AdminPasswordChangeView(APIView):
    permission_classes = [IsAdminUser]

    @extend_schema(
        summary='Change Own Password',
        description='Change the logged-in admin password. Body: {"current_password": "...", "new_password": "..."}',
        request=AdminPasswordChangeSerializer,
        responses={200: {'type': 'object', 'properties': {'message': {'type': 'string'}}}},
        tags=['Admin Profile'],
    )
    def post(self, request):
        serializer = AdminPasswordChangeSerializer(data=request.data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        request.user.set_password(serializer.validated_data['new_password'])
        request.user.save()
        log_admin_action(request.user, 'reset_password', 'Changed own password', request)
        return Response({'message': 'Password changed successfully.'})