from datetime import time

from django.core.management.base import BaseCommand

from accounts.models import Bus, Route, Seat


ROUTES = [
    ('Mwanza', 'Dar es Salaam', 35000, 10, 0),
    ('Dar es Salaam', 'Mwanza', 35000, 10, 0),
    ('Dar es Salaam', 'Kigoma', 40000, 12, 0),
    ('Kigoma', 'Dar es Salaam', 40000, 12, 0),
    ('Tanga', 'Arusha', 25000, 7, 0),
    ('Arusha', 'Tanga', 25000, 7, 0),
    ('Dar es Salaam', 'Dodoma', 20000, 6, 0),
    ('Dodoma', 'Dar es Salaam', 20000, 6, 0),
    ('Dar es Salaam', 'Arusha', 30000, 8, 30),
    ('Arusha', 'Dar es Salaam', 30000, 8, 30),
]

BUSES = [
    ('BUS-001', 'H wrongful Coach', time(6, 0), time(16, 0), 49),
    ('BUS-002', 'H wrongful Coach', time(8, 0), time(18, 0), 49),
    ('BUS-003', 'Quick Bus', time(7, 0), time(17, 0), 45),
    ('BUS-004', 'Quick Bus', time(9, 0), time(19, 0), 45),
    ('BUS-005', 'City Line', time(6, 30), time(16, 30), 52),
    ('BUS-006', 'City Line', time(10, 0), time(20, 0), 52),
    ('BUS-007', 'TranStar', time(5, 30), time(15, 30), 49),
    ('BUS-008', 'TranStar', time(11, 0), time(21, 0), 49),
]


class Command(BaseCommand):
    help = 'Seed the database with routes, buses, and seats'

    def handle(self, *args, **options):
        self.stdout.write('Seeding routes...')
        for origin, dest, price, h, m in ROUTES:
            Route.objects.get_or_create(
                origin=origin,
                destination=dest,
                defaults={'price': price, 'duration_hours': h, 'duration_minutes': m},
            )

        self.stdout.write('Seeding buses and seats...')
        routes = list(Route.objects.all())
        for i, (bus_num, operator, dep, arr, seats_count) in enumerate(BUSES):
            route = routes[i % len(routes)]
            bus, created = Bus.objects.get_or_create(
                bus_number=bus_num,
                route=route,
                defaults={
                    'operator': operator,
                    'departure_time': dep,
                    'arrival_time': arr,
                    'total_seats': seats_count,
                },
            )
            if created:
                for s in range(1, seats_count + 1):
                    Seat.objects.create(bus=bus, seat_number=str(s))

        self.stdout.write(self.style.SUCCESS(
            f'Done! {Route.objects.count()} routes, '
            f'{Bus.objects.count()} buses, '
            f'{Seat.objects.count()} seats created.'
        ))
