from django.urls import path

from .views import (
    AdminBookingCancelView,
    AdminBookingCheckInView,
    AdminBookingConfirmView,
    AdminBookingDetailView,
    AdminBookingListView,
    AdminBookingRescheduleView,
    AdminBusDetailView,
    AdminBusListView,
    AdminBusSeatCreateView,
    AdminLoginView,
    AdminLogListView,
    AdminPassengerDetailView,
    AdminPassengerListView,
    AdminPassengerResetPasswordView,
    AdminPasswordChangeView,
    AdminProfileView,
    AdminRouteDetailView,
    AdminRouteListView,
    AdminSeatDetailView,
    AdminStatsView,
)

urlpatterns = [
    path('login/', AdminLoginView.as_view(), name='admin-login'),
    path('logs/', AdminLogListView.as_view(), name='admin-logs'),
    path('stats/', AdminStatsView.as_view(), name='admin-stats'),

    path('bookings/', AdminBookingListView.as_view(), name='admin-booking-list'),
    path('bookings/<int:pk>/', AdminBookingDetailView.as_view(), name='admin-booking-detail'),
    path('bookings/<int:pk>/reschedule/', AdminBookingRescheduleView.as_view(), name='admin-booking-reschedule'),
    path('bookings/<int:pk>/confirm/', AdminBookingConfirmView.as_view(), name='admin-booking-confirm'),
    path('bookings/<int:pk>/check-in/', AdminBookingCheckInView.as_view(), name='admin-booking-check-in'),
    path('bookings/<int:pk>/cancel/', AdminBookingCancelView.as_view(), name='admin-booking-cancel'),

    path('passengers/', AdminPassengerListView.as_view(), name='admin-passenger-list'),
    path('passengers/<int:pk>/', AdminPassengerDetailView.as_view(), name='admin-passenger-detail'),
    path('passengers/<int:pk>/reset-password/', AdminPassengerResetPasswordView.as_view(), name='admin-passenger-reset-password'),

    path('buses/', AdminBusListView.as_view(), name='admin-bus-list'),
    path('buses/<int:pk>/', AdminBusDetailView.as_view(), name='admin-bus-detail'),
    path('buses/<int:pk>/seats/', AdminBusSeatCreateView.as_view(), name='admin-bus-seats'),
    path('seats/<int:pk>/', AdminSeatDetailView.as_view(), name='admin-seat-detail'),

    path('routes/', AdminRouteListView.as_view(), name='admin-route-list'),
    path('routes/<int:pk>/', AdminRouteDetailView.as_view(), name='admin-route-detail'),

    path('profile/', AdminProfileView.as_view(), name='admin-profile'),
    path('profile/password/', AdminPasswordChangeView.as_view(), name='admin-password-change'),
]