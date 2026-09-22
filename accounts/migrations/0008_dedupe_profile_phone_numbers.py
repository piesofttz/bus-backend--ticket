from django.db import migrations


def dedupe_existing_phones(apps, schema_editor):
    Profile = apps.get_model('accounts', 'Profile')
    seen = set()
    for profile in Profile.objects.all().order_by('id'):
        phone = profile.phone_number
        if not phone:
            continue
        if phone in seen:
            profile.phone_number = None
            profile.save()
        else:
            seen.add(phone)


def reverse(apps, schema_editor):
    pass


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0007_alter_profile_phone_number'),
    ]

    operations = [
        migrations.RunPython(dedupe_existing_phones, reverse),
    ]