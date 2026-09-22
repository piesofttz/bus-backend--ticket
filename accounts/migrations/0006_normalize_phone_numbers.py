from django.db import migrations

from accounts.utils import normalize_phone_number


def normalize_existing_phones(apps, schema_editor):
    Profile = apps.get_model('accounts', 'Profile')
    for profile in Profile.objects.all():
        if not profile.phone_number:
            continue
        normalized = normalize_phone_number(profile.phone_number)
        if normalized:
            if not Profile.objects.filter(phone_number=normalized).exclude(pk=profile.pk).exists():
                profile.phone_number = normalized
                profile.save()


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0005_booking_checked_in_at_alter_booking_status'),
    ]

    operations = [
        migrations.RunPython(normalize_existing_phones, migrations.RunPython.noop),
    ]