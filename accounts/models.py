import uuid

from django.conf import settings
from django.contrib.auth.models import User
from django.db import models
from django.db.models.signals import post_save
from django.dispatch import receiver


class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    phone_number = models.CharField(max_length=20, blank=True, default='')
    location = models.CharField(max_length=200, blank=True, default='')
    nida_number = models.CharField(max_length=50, blank=True, default='')

    def __str__(self):
        return f"Profile of {self.user.username}"


@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance)


@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    instance.profile.save()


class Route(models.Model):
    origin = models.CharField(max_length=100)
    destination = models.CharField(max_length=100)
    price = models.DecimalField(max_digits=10, decimal_places=2)
    duration_hours = models.PositiveIntegerField(default=0)
    duration_minutes = models.PositiveIntegerField(default=0)

    class Meta:
        unique_together = ['origin', 'destination']
        ordering = ['origin']

    def __str__(self):
        return f"{self.origin} to {self.destination}"


class Bus(models.Model):
    route = models.ForeignKey(Route, on_delete=models.CASCADE, related_name='buses')
    bus_number = models.CharField(max_length=20)
    operator = models.CharField(max_length=100)
    total_seats = models.PositiveIntegerField(default=49)
    departure_time = models.TimeField()
    arrival_time = models.TimeField()
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['departure_time']

    def __str__(self):
        return f"{self.bus_number} ({self.operator}) - {self.route}"


class Seat(models.Model):
    bus = models.ForeignKey(Bus, on_delete=models.CASCADE, related_name='seats')
    seat_number = models.CharField(max_length=10)
    is_available = models.BooleanField(default=True)

    class Meta:
        unique_together = ['bus', 'seat_number']
        ordering = ['seat_number']

    def __str__(self):
        return f"{self.bus.bus_number} - Seat {self.seat_number}"


class Booking(models.Model):
    STATUS_CHOICES = [
        ('confirmed', 'Confirmed'),
        ('cancelled', 'Cancelled'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='bookings')
    bus = models.ForeignKey(Bus, on_delete=models.CASCADE, related_name='bookings')
    seat = models.OneToOneField(Seat, on_delete=models.CASCADE, related_name='booking')
    ticket_number = models.CharField(max_length=20, unique=True, editable=False)
    full_name = models.CharField(max_length=200)
    phone_number = models.CharField(max_length=20)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='confirmed')
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.ticket_number} - {self.full_name}"

    def save(self, *args, **kwargs):
        if not self.ticket_number:
            self.ticket_number = self.generate_ticket_number()
        super().save(*args, **kwargs)

    def delete(self, *args, **kwargs):
        seat = self.seat
        super().delete(*args, **kwargs)
        seat.is_available = True
        seat.save()

    @staticmethod
    def generate_ticket_number():
        while True:
            ref = uuid.uuid4().hex[:8].upper()
            ticket_number = f"BUS-{ref}"
            if not Booking.objects.filter(ticket_number=ticket_number).exists():
                return ticket_number
