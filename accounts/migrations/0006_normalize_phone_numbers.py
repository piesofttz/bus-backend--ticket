from django.db import migrations

from accounts.utils import normalize_phone_number


def normalize_existing_phones(apps, schema_editor):
    Profile = apps.get_model('accounts', 'Profile')
    seen = set()
    for profile in Profile.objects.all().order_by('id'):
        if not profile.phone_number:
            continue
        normalized = normalize_phone_number(profile.phone_number)
        if normalized and normalized not in seen:
            profile.phone_number = normalized
            profile.save()
            seen.add(normalized)
        elif normalized:
            # Duplicate number after normalization: keep the first account,
            # clear the phone on later duplicates so the unique index can be created.
            profile.phone_number = None
            profile.save()


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0005_booking_checked_in_at_alter_booking_status'),
    ]

    operations = [
        migrations.RunPython(normalize_existing_phones, migrations.RunPython.noop),
    ]