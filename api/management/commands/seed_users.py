from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from api.models import CaregiverRelationship
from drivers.models import Driver, DriverLocation
from decimal import Decimal

User = get_user_model()


class Command(BaseCommand):
    help = 'Seed database with test users (passenger, driver, caregiver)'

    def handle(self, *args, **kwargs):
        self.stdout.write('🌱 Seeding test users...')

        # Create Passenger User
        passenger, created = User.objects.get_or_create(
            phone_number='27821234567',
            defaults={
                'username': 'user_27821234567',
                'first_name': 'Sarah',
                'last_name': 'Johnson',
                'email': 'sarah@example.com',
                'user_type': 'passenger',
                'is_phone_verified': True,
            }
        )
        if created:
            self.stdout.write(f'  ✅ Created passenger: {passenger.get_full_name()} (+27821234567)')
        else:
            self.stdout.write(f'  ℹ️  Passenger already exists: {passenger.get_full_name()}')

        # Create Driver User
        driver_user, created = User.objects.get_or_create(
            phone_number='27821234568',
            defaults={
                'username': 'user_27821234568',
                'first_name': 'Michael',
                'last_name': 'Brown',
                'email': 'michael@example.com',
                'user_type': 'driver',
                'is_phone_verified': True,
            }
        )
        if created:
            self.stdout.write(f'  ✅ Created driver user: {driver_user.get_full_name()} (+27821234568)')
        else:
            self.stdout.write(f'  ℹ️  Driver user already exists: {driver_user.get_full_name()}')

        # Create Driver Profile
        driver_profile, created = Driver.objects.get_or_create(
            user=driver_user,
            defaults={
                'phone_number': '27821234568',
                'license_number': 'DL987654',
                'vehicle_registration': 'CA 999 GP',
                'vehicle_type': 'sedan',
                'status': 'available',
                'rating': Decimal('4.90'),
                'total_rides': 200,
                'is_verified': True,
            }
        )
        if created:
            self.stdout.write(f'    ✅ Created driver profile')

            # Create Driver Location
            DriverLocation.objects.create(
                driver=driver_profile,
                latitude=Decimal('-26.2041'),
                longitude=Decimal('28.0473'),
                heading=Decimal('0.00'),
                speed=Decimal('0.00'),
            )
            self.stdout.write(f'    📍 Created driver location')
        else:
            self.stdout.write(f'    ℹ️  Driver profile already exists')

        # Create Caregiver User
        caregiver, created = User.objects.get_or_create(
            phone_number='27821234569',
            defaults={
                'username': 'user_27821234569',
                'first_name': 'Emily',
                'last_name': 'Davis',
                'email': 'emily@example.com',
                'user_type': 'caregiver',
                'is_phone_verified': True,
            }
        )
        if created:
            self.stdout.write(f'  ✅ Created caregiver: {caregiver.get_full_name()} (+27821234569)')
        else:
            self.stdout.write(f'  ℹ️  Caregiver already exists: {caregiver.get_full_name()}')

        # Link Passenger to Caregiver
        relationship, created = CaregiverRelationship.objects.get_or_create(
            passenger=passenger,
            caregiver=caregiver,
            defaults={
                'relationship_type': 'family',
                'can_book_rides': True,
                'can_view_location': True,
                'can_receive_notifications': True,
                'notes': 'Primary caregiver - daughter',
            }
        )
        if created:
            self.stdout.write(f'  🔗 Linked passenger to caregiver')
        else:
            self.stdout.write(f'  ℹ️  Relationship already exists')

        self.stdout.write(self.style.SUCCESS('\n✅ Seeding completed successfully!'))
        self.stdout.write('\n📱 Test User Credentials:')
        self.stdout.write(f'  Passenger: +27821234567 (Sarah Johnson)')
        self.stdout.write(f'  Driver:    +27821234568 (Michael Brown)')
        self.stdout.write(f'  Caregiver: +27821234569 (Emily Davis)')
        self.stdout.write('\n💡 Use these phone numbers to test OTP login!')
