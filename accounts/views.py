from django.contrib.auth import login, logout
from django.contrib.auth.models import User
from django.http import HttpResponse
from django.template.loader import render_to_string
from drf_spectacular.utils import OpenApiParameter, extend_schema
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken
from xhtml2pdf import pisa

from .models import Booking, Bus, Route, Seat
from .serializers import (
    BookingSerializer,
    BusSerializer,
    LoginSerializer,
    RouteSerializer,
    SeatSerializer,
    UserSerializer,
)


@extend_schema(
    summary='Login',
    description='Login with username and password. Returns JWT access + refresh tokens.',
    request=LoginSerializer,
    responses={200: {'type': 'object', 'properties': {
        'access_token': {'type': 'string', 'description': 'Access token (expires in 3 minutes)'},
        'refresh_token': {'type': 'string', 'description': 'Refresh token (expires in 7 days)'},
        'user': {'$ref': '#/components/schemas/User'},
        'message': {'type': 'string'},
    }}},
    tags=['Auth'],
)
@api_view(['POST'])
@permission_classes([AllowAny])
def login_view(request):
    serializer = LoginSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    user = serializer.validated_data['user']
    login(request, user)
    refresh = RefreshToken.for_user(user)
    return Response({
        'access_token': str(refresh.access_token),
        'refresh_token': str(refresh),
        'user': UserSerializer(user).data,
        'message': 'Login successful.',
    }, status=status.HTTP_200_OK)


@extend_schema(
    summary='Logout',
    description='Blacklist the refresh token so the user must login again to get new tokens.',
    request={
        'application/json': {
            'type': 'object',
            'properties': {
                'refresh_token': {'type': 'string', 'description': 'The refresh token to blacklist'},
            },
            'required': ['refresh_token'],
        }
    },
    responses={200: {'type': 'object', 'properties': {'message': {'type': 'string'}}}},
    tags=['Auth'],
)
@api_view(['POST'])
@permission_classes([IsAuthenticated])
def logout_view(request):
    try:
        refresh_token = request.data.get('refresh_token')
        token = RefreshToken(refresh_token)
        token.blacklist()
    except Exception:
        pass
    logout(request)
    return Response({'message': 'Logout successful.'}, status=status.HTTP_200_OK)


@extend_schema(
    summary='Get Current User',
    description='Get logged-in user profile',
    responses={200: UserSerializer},
    tags=['Auth'],
)
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def user_view(request):
    return Response(UserSerializer(request.user).data)


@extend_schema(
    summary='Register',
    description='Register a new user with profile info',
    request={
        'application/json': {
            'type': 'object',
            'properties': {
                'username': {'type': 'string', 'description': 'Login username'},
                'password': {'type': 'string', 'description': 'Password'},
                'email': {'type': 'string', 'description': 'Email address'},
                'first_name': {'type': 'string', 'description': 'First name'},
                'last_name': {'type': 'string', 'description': 'Last name'},
                'phone_number': {'type': 'string', 'description': 'Phone number'},
                'location': {'type': 'string', 'description': 'Location/address'},
                'nida_number': {'type': 'string', 'description': 'NIDA national ID'},
            },
            'required': ['username', 'password'],
        }
    },
    responses={201: UserSerializer, 400: {'type': 'object', 'properties': {'error': {'type': 'string'}}}},
    tags=['Auth'],
)
@api_view(['POST'])
@permission_classes([AllowAny])
def register_view(request):
    username = request.data.get('username')
    password = request.data.get('password')
    email = request.data.get('email', '')
    first_name = request.data.get('first_name', '')
    last_name = request.data.get('last_name', '')
    phone_number = request.data.get('phone_number', '')
    location = request.data.get('location', '')
    nida_number = request.data.get('nida_number', '')

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

    profile = user.profile
    profile.phone_number = phone_number
    profile.location = location
    profile.nida_number = nida_number
    profile.save()

    login(request, user)
    refresh = RefreshToken.for_user(user)
    return Response({
        'access_token': str(refresh.access_token),
        'refresh_token': str(refresh),
        'user': UserSerializer(user).data,
        'message': 'Registration successful.',
    }, status=status.HTTP_201_CREATED)


class RouteListView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary='Search Routes',
        description='Search all bus routes by origin or destination. Pass ?search=mwanza to filter.',
        parameters=[
            OpenApiParameter(name='search', type=str, description='Search by origin or destination city'),
        ],
        responses={200: RouteSerializer(many=True)},
        tags=['Routes'],
    )
    def get(self, request):
        search = request.query_params.get('search', '').strip()
        routes = Route.objects.all()
        if search:
            routes = routes.filter(
                origin__icontains=search
            ) | routes.filter(
                destination__icontains=search
            )
        serializer = RouteSerializer(routes, many=True)
        return Response(serializer.data)


class AllBusListView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary='Get All Buses',
        description='Get all available buses. Optional filters: route_id, search, origin, destination.',
        parameters=[
            OpenApiParameter(name='route_id', type=int, description='Filter by route ID', required=False),
            OpenApiParameter(name='search', type=str, description='Search by bus number or operator', required=False),
            OpenApiParameter(name='origin', type=str, description='Filter by origin city', required=False),
            OpenApiParameter(name='destination', type=str, description='Filter by destination city', required=False),
        ],
        responses={200: BusSerializer(many=True)},
        tags=['Buses'],
    )
    def get(self, request):
        buses = Bus.objects.filter(is_active=True)
        route_id = request.query_params.get('route_id')
        search = request.query_params.get('search', '').strip()
        origin = request.query_params.get('origin', '').strip()
        destination = request.query_params.get('destination', '').strip()

        if route_id:
            buses = buses.filter(route_id=route_id)
        if search:
            buses = buses.filter(
                bus_number__icontains=search
            ) | buses.filter(
                operator__icontains=search
            )
        if origin:
            buses = buses.filter(route__origin__icontains=origin)
        if destination:
            buses = buses.filter(route__destination__icontains=destination)

        serializer = BusSerializer(buses, many=True)
        return Response(serializer.data)


class BusListView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary='Get Buses for Route',
        description='Get all available buses for a specific route',
        responses={200: BusSerializer(many=True), 404: {'type': 'object', 'properties': {'error': {'type': 'string'}}}},
        tags=['Buses'],
    )
    def get(self, request, route_id):
        try:
            route = Route.objects.get(pk=route_id)
        except Route.DoesNotExist:
            return Response(
                {'error': 'Route not found.'},
                status=status.HTTP_404_NOT_FOUND,
            )
        buses = Bus.objects.filter(route=route, is_active=True)
        serializer = BusSerializer(buses, many=True)
        return Response(serializer.data)


class SeatListView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary='Get Seats for Bus',
        description='Get all seats for a specific bus with availability status',
        responses={200: SeatSerializer(many=True), 404: {'type': 'object', 'properties': {'error': {'type': 'string'}}}},
        tags=['Seats'],
    )
    def get(self, request, bus_id):
        try:
            bus = Bus.objects.get(pk=bus_id)
        except Bus.DoesNotExist:
            return Response(
                {'error': 'Bus not found.'},
                status=status.HTTP_404_NOT_FOUND,
            )
        seats = Seat.objects.filter(bus=bus)
        serializer = SeatSerializer(seats, many=True)
        return Response(serializer.data)


class BookingCreateView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary='Book a Ticket',
        description='Create a new booking. Agent provides full_name, phone_number, bus ID, seat ID, travel_date, travel_time. Ticket number is auto-generated.',
        request={
            'application/json': {
                'type': 'object',
                'properties': {
                    'full_name': {'type': 'string', 'description': 'Client full name'},
                    'phone_number': {'type': 'string', 'description': 'Client phone number'},
                    'bus': {'type': 'integer', 'description': 'Bus ID'},
                    'seat': {'type': 'integer', 'description': 'Seat ID'},
                    'travel_date': {'type': 'string', 'format': 'date', 'description': 'Travel date (YYYY-MM-DD)'},
                    'travel_time': {'type': 'string', 'format': 'time', 'description': 'Travel time (HH:MM)'},
                },
                'required': ['full_name', 'phone_number', 'bus', 'seat', 'travel_date', 'travel_time'],
            }
        },
        responses={201: BookingSerializer, 400: {'type': 'object', 'properties': {'error': {'type': 'string'}}}},
        tags=['Bookings'],
    )
    def post(self, request):
        data = request.data.copy()
        data['user'] = request.user.id
        serializer = BookingSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        serializer.save(user=request.user)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class BookingListView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary='List My Bookings',
        description='Get all bookings made by the current user',
        responses={200: BookingSerializer(many=True)},
        tags=['Bookings'],
    )
    def get(self, request):
        bookings = Booking.objects.filter(user=request.user)
        serializer = BookingSerializer(bookings, many=True)
        return Response(serializer.data)


class BookingDetailView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary='Get Booking Detail',
        description='Get a single booking by ID',
        responses={200: BookingSerializer, 404: {'type': 'object', 'properties': {'error': {'type': 'string'}}}},
        tags=['Bookings'],
    )
    def get(self, request, pk):
        try:
            booking = Booking.objects.get(pk=pk, user=request.user)
        except Booking.DoesNotExist:
            return Response(
                {'error': 'Booking not found.'},
                status=status.HTTP_404_NOT_FOUND,
            )
        serializer = BookingSerializer(booking)
        return Response(serializer.data)

    @extend_schema(
        summary='Cancel Booking',
        description='Cancel/delete a booking and free the seat',
        responses={200: {'type': 'object', 'properties': {'message': {'type': 'string'}}}, 404: {'type': 'object', 'properties': {'error': {'type': 'string'}}}},
        tags=['Bookings'],
    )
    def delete(self, request, pk):
        try:
            booking = Booking.objects.get(pk=pk, user=request.user)
        except Booking.DoesNotExist:
            return Response(
                {'error': 'Booking not found.'},
                status=status.HTTP_404_NOT_FOUND,
            )
        booking.status = 'cancelled'
        booking.delete()
        return Response(
            {'message': 'Booking cancelled successfully.'},
            status=status.HTTP_200_OK,
        )


class BookingReceiptPDFView(APIView):
    permission_classes = [IsAuthenticated]

    @extend_schema(
        summary='Download PDF Receipt',
        description='Download a PDF receipt for a booking',
        responses={200: {'description': 'PDF file'}, 404: {'type': 'object', 'properties': {'error': {'type': 'string'}}}},
        tags=['Bookings'],
    )
    def get(self, request, pk):
        try:
            booking = Booking.objects.get(pk=pk, user=request.user)
        except Booking.DoesNotExist:
            return Response(
                {'error': 'Booking not found.'},
                status=status.HTTP_404_NOT_FOUND,
            )

        html_string = render_to_string('accounts/receipt.html', {'booking': booking})

        response = HttpResponse(content_type='application/pdf')
        response['Content-Disposition'] = (
            f'attachment; filename="receipt_{booking.ticket_number}.pdf"'
        )

        pisa_status = pisa.CreatePDF(html_string, dest=response)
        if pisa_status.err:
            return Response(
                {'error': 'Failed to generate PDF.'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
        return response
