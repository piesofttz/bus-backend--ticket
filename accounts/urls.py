from django.urls import path

from .views import (
    BookingCreateView,
    BookingDetailView,
    BookingListView,
    BookingReceiptPDFView,
    BusListView,
    RouteListView,
    SeatListView,
    login_view,
    logout_view,
    register_view,
    user_view,
)

urlpatterns = [
    path('login/', login_view, name='login'),
    path('logout/', logout_view, name='logout'),
    path('register/', register_view, name='register'),
    path('user/', user_view, name='user'),
    path('routes/', RouteListView.as_view(), name='route-list'),
    path('routes/<int:route_id>/buses/', BusListView.as_view(), name='bus-list'),
    path('buses/<int:bus_id>/seats/', SeatListView.as_view(), name='seat-list'),
    path('bookings/', BookingListView.as_view(), name='booking-list'),
    path('bookings/create/', BookingCreateView.as_view(), name='booking-create'),
    path('bookings/<int:pk>/', BookingDetailView.as_view(), name='booking-detail'),
    path('bookings/<int:pk>/receipt/', BookingReceiptPDFView.as_view(), name='booking-receipt'),
]
