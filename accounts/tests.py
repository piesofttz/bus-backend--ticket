from django.contrib.auth.models import User
from django.test import TestCase
from rest_framework.test import APIClient

from .models import Bus, Profile, Route, Seat
from .utils import normalize_phone_number


class PhoneNormalizationTests(TestCase):
    def test_nine_digits(self):
        self.assertEqual(normalize_phone_number('674303431'), '+255674303431')

    def test_with_country_code(self):
        self.assertEqual(normalize_phone_number('+255674303431'), '+255674303431')

    def test_with_local_code(self):
        self.assertEqual(normalize_phone_number('255674303431'), '+255674303431')

    def test_with_leading_zero(self):
        self.assertEqual(normalize_phone_number('0674303431'), '+255674303431')

    def test_invalid_short(self):
        self.assertIsNone(normalize_phone_number('12345'))

    def test_invalid_wrong_country(self):
        self.assertIsNone(normalize_phone_number('+254674303431'))


class LoginTests(TestCase):
    def setUp(self):
        self.client = APIClient()
        self.user = User.objects.create_user(
            username='user_674303431',
            password='testpass',
            email='a@b.com',
        )
        profile = self.user.profile
        profile.phone_number = '+255674303431'
        profile.save()

    def test_login_with_phone_only(self):
        resp = self.client.post('/api/auth/login/', {
            'phone_number': '674303431',
        }, format='json')
        self.assertEqual(resp.status_code, 200)
        self.assertIn('access_token', resp.data)
        self.assertEqual(resp.data['user']['username'], self.user.username)

    def test_login_with_full_phone(self):
        resp = self.client.post('/api/auth/login/', {
            'phone_number': '+255674303431',
        }, format='json')
        self.assertEqual(resp.status_code, 200)

    def test_login_unregistered_phone(self):
        resp = self.client.post('/api/auth/login/', {
            'phone_number': '777303431',
        }, format='json')
        self.assertEqual(resp.status_code, 400)
        self.assertIn('not registered', str(resp.data))

    def test_login_invalid_phone(self):
        resp = self.client.post('/api/auth/login/', {
            'phone_number': '123',
        }, format='json')
        self.assertEqual(resp.status_code, 400)


class RegisterTests(TestCase):
    def setUp(self):
        self.client = APIClient()

    def test_register_with_phone(self):
        resp = self.client.post('/api/auth/register/', {
            'phone_number': '754234512',
            'email': 'c@d.com',
        }, format='json')
        self.assertEqual(resp.status_code, 201)
        self.assertIn('access_token', resp.data)
        self.assertTrue(
            Profile.objects.filter(phone_number='+255754234512').exists()
        )

    def test_register_requested_payload(self):
        resp = self.client.post('/api/auth/register/', {
            'phone_number': '674303431',
            'email': 'user@example.com',
            'first_name': 'John',
            'last_name': 'Doe',
            'location': 'Dar es Salaam',
            'nida_number': '19920101-12345-00123',
        }, format='json')
        self.assertEqual(resp.status_code, 201)
        self.assertEqual(resp.data['user']['first_name'], 'John')
        self.assertEqual(resp.data['user']['last_name'], 'Doe')
        profile = Profile.objects.get(phone_number='+255674303431')
        self.assertEqual(profile.location, 'Dar es Salaam')
        self.assertEqual(profile.nida_number, '19920101-12345-00123')

    def test_register_duplicate_phone(self):
        user = User.objects.create_user(username='user_754234512', password='p')
        profile = user.profile
        profile.phone_number = '+255754234512'
        profile.save()

        resp = self.client.post('/api/auth/register/', {
            'phone_number': '754234512',
        }, format='json')
        self.assertEqual(resp.status_code, 400)
        self.assertIn('already registered', str(resp.data))

    def test_register_invalid_phone(self):
        resp = self.client.post('/api/auth/register/', {
            'phone_number': '12',
        }, format='json')
        self.assertEqual(resp.status_code, 400)


class SeatOrderingTests(TestCase):
    def test_seats_ordered_chronologically(self):
        route = Route.objects.create(
            origin='Mwanza', destination='Dar es Salaam',
            price=35000, duration_hours=10, duration_minutes=0,
        )
        bus = Bus.objects.create(
            route=route, bus_number='BUS-TEST', operator='Test Coach',
            total_seats=53, departure_time='06:00', arrival_time='16:00',
        )
        for i in range(1, 54):
            Seat.objects.create(bus=bus, seat_number=str(i), position=i)

        seats = list(Seat.objects.filter(bus=bus))
        self.assertEqual(len(seats), 53)
        self.assertEqual([s.seat_number for s in seats], [str(n) for n in range(1, 54)])