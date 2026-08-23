from django.contrib.auth import login, logout
from django.contrib.auth.models import User
from django.http import HttpResponse
from django.template.loader import render_to_string
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
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
    name = request.data.get('name')
    password = request.data.get('password')
    email = request.data.get('email', '')
    first_name = request.data.get('first_name', '')
    last_name = request.data.get('last_name', '')
    phone_number = request.data.get('phone_number', '')
    location = request.data.get('location', '')
    nida_number = request.data.get('nida_number', '')

    if not name or not password:
        return Response(
            {'error': 'Name and password are required.'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    if User.objects.filter(username=name).exists():
        return Response(
            {'error': 'Name already exists.'},
            status=status.HTTP_400_BAD_REQUEST,
        )

    user = User.objects.create_user(
        username=name,
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
    return Response({
        'user': UserSerializer(user).data,
        'message': 'Registration successful.',
    }, status=status.HTTP_201_CREATED)


class RouteListView(APIView):
    permission_classes = [IsAuthenticated]

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


class BusListView(APIView):
    permission_classes = [IsAuthenticated]

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

    def post(self, request):
        data = request.data.copy()
        data['user'] = request.user.id
        serializer = BookingSerializer(data=data)
        serializer.is_valid(raise_exception=True)
        serializer.save(user=request.user)
        return Response(serializer.data, status=status.HTTP_201_CREATED)


class BookingListView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        bookings = Booking.objects.filter(user=request.user)
        serializer = BookingSerializer(bookings, many=True)
        return Response(serializer.data)


class BookingDetailView(APIView):
    permission_classes = [IsAuthenticated]

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
