from django.contrib.auth.models import User
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = 'Create or update admin user with username=admin, password=1'

    def handle(self, *args, **options):
        user, created = User.objects.get_or_create(username='admin')
        user.set_password('1')
        user.is_superuser = True
        user.is_staff = True
        user.is_active = True
        user.email = 'admin@bus.com'
        user.save()

        from accounts.models import Profile
        profile, _ = Profile.objects.get_or_create(user=user)
        profile.phone_number = '0712345678'
        profile.location = 'Dar es Salaam'
        profile.nida_number = '123456789'
        profile.save()

        self.stdout.write(self.style.SUCCESS(
            f'Admin user ready: username=admin, password=1 (created={created})'
        ))
