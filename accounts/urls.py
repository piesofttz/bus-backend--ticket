from django.urls import path

from .views import (
    TicketDetailView,
    TicketListCreateView,
    TicketReceiptPDFView,
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
    path('tickets/', TicketListCreateView.as_view(), name='ticket-list-create'),
    path('tickets/<int:pk>/', TicketDetailView.as_view(), name='ticket-detail'),
    path('tickets/<int:pk>/receipt/', TicketReceiptPDFView.as_view(), name='ticket-receipt'),
]
