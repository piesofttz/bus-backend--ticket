import string
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


ROUTE_CHOICES = [
    ('dar_to_mwanza', 'Dar es Salaam to Mwanza'),
    ('mwanza_to_dar', 'Mwanza to Dar es Salaam'),
    ('dodoma_to_dar', 'Dodoma to Dar es Salaam'),
]


class Ticket(models.Model):
    user = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='tickets',
    )
    ticket_number = models.CharField(max_length=20, unique=True, editable=False)
    full_name = models.CharField(max_length=200)
    phone_number = models.CharField(max_length=20)
    route = models.CharField(max_length=50, choices=ROUTE_CHOICES)
    seat_number = models.CharField(max_length=10)
    travel_date = models.DateField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.ticket_number} - {self.full_name}"

    def save(self, *args, **kwargs):
        if not self.ticket_number:
            self.ticket_number = self.generate_ticket_number()
        super().save(*args, **kwargs)

    @staticmethod
    def generate_ticket_number():
        while True:
            ref = uuid.uuid4().hex[:8].upper()
            ticket_number = f"BUS-{ref}"
            if not Ticket.objects.filter(ticket_number=ticket_number).exists():
                return ticket_number
