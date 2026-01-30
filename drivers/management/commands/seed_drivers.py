from django.core.management.base import BaseCommand
from django.contrib.auth.models import User
from drivers.models import Driver, DriverLocation
from decimal import Decimal


class Command(BaseCommand):
    help = 'Seed database with test drivers and locations'

    def handle(self, *args, **kwargs):
        self.stdout.write('🌱 Seeding drivers...')

        # Create test drivers
        drivers_data = [
            {
                'username': 'driver1',
                'email': 'driver1@careconnect.com',
                'first_name': 'John',
                'last_name': 'Doe',
                'phone': '+27123456789',
                'license': 'DL123456',
                'vehicle_reg': 'CA 123 GP',
                'vehicle_type': 'sedan',
                'lat': -26.2041,
                'lon': 28.0473,
            },
            {
                'username': 'driver2',
                'email': 'driver2@careconnect.com',
                'first_name': 'Jane',
                'last_name': 'Smith',
                'phone': '+27123456790',
                'license': 'DL123457',
                'vehicle_reg': 'CA 456 GP',
                'vehicle_type': 'suv',
                'lat': -26.1041,
                'lon': 28.1473,
            },
            {
                'username': 'driver3',
                'email': 'driver3@careconnect.com',
                'first_name': 'Mike',
                'last_name': 'Johnson',
                'phone': '+27123456791',
                'license': 'DL123458',
                'vehicle_reg': 'CA 789 GP',
                'vehicle_type': 'wheelchair_accessible',
                'lat': -25.7479,
                'lon': 28.2293,
            },
        ]

        for driver_data in drivers_data:
            # Create or get user
            user, created = User.objects.get_or_create(
                username=driver_data['username'],
                defaults={
                    'email': driver_data['email'],
                    'first_name': driver_data['first_name'],
                    'last_name': driver_data['last_name'],
                }
            )
            if created:
                user.set_password('password123')
                user.save()
                self.stdout.write(f'  ✅ Created user: {user.username}')

            # Create or update driver
            driver, created = Driver.objects.update_or_create(
                user=user,
                defaults={
                    'phone_number': driver_data['phone'],
                    'license_number': driver_data['license'],
                    'vehicle_registration': driver_data['vehicle_reg'],
                    'vehicle_type': driver_data['vehicle_type'],
                    'status': 'available',
                    'rating': Decimal('4.80'),
                    'total_rides': 150,
                    'is_verified': True,
                }
            )
            if created:
                self.stdout.write(f'  ✅ Created driver: {driver}')
            else:
                self.stdout.write(f'  ℹ️  Updated driver: {driver}')

            # Create or update driver location
            location, created = DriverLocation.objects.update_or_create(
                driver=driver,
                defaults={
                    'latitude': Decimal(str(driver_data['lat'])),
                    'longitude': Decimal(str(driver_data['lon'])),
                    'heading': Decimal('0.00'),
                    'speed': Decimal('0.00'),
                }
            )
            if created:
                self.stdout.write(f'    📍 Created location: ({location.latitude}, {location.longitude})')
            else:
                self.stdout.write(f'    📍 Updated location: ({location.latitude}, {location.longitude})')

        self.stdout.write(self.style.SUCCESS('\n✅ Seeding completed successfully!'))
