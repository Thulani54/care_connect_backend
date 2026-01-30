import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.utils import timezone


class DriverConsumer(AsyncWebsocketConsumer):
    """WebSocket consumer for drivers to receive ride requests"""

    async def connect(self):
        self.driver_id = self.scope['url_route']['kwargs']['driver_id']
        self.driver_group_name = f'driver_{self.driver_id}'

        # Join driver group
        await self.channel_layer.group_add(
            self.driver_group_name,
            self.channel_name
        )

        await self.accept()
        print(f'✅ Driver WebSocket connected: {self.driver_id}')

        # Send initial connection message
        await self.send(text_data=json.dumps({
            'type': 'connection_established',
            'message': f'Connected to driver service',
            'driver_id': self.driver_id
        }))

    async def disconnect(self, close_code):
        # Leave driver group
        await self.channel_layer.group_discard(
            self.driver_group_name,
            self.channel_name
        )
        print(f'❌ Driver WebSocket disconnected: {self.driver_id}')

    async def receive(self, text_data):
        """Handle incoming WebSocket messages from driver"""
        data = json.loads(text_data)
        message_type = data.get('type')

        if message_type == 'ping':
            # Respond to ping
            await self.send(text_data=json.dumps({
                'type': 'pong',
                'timestamp': timezone.now().isoformat()
            }))

        elif message_type == 'accept_ride':
            # Driver accepted the ride
            ride_id = data.get('ride_id')
            print(f'✅ Driver {self.driver_id} accepted ride: {ride_id}')
            await self.accept_ride(ride_id)

        elif message_type == 'decline_ride':
            # Driver declined the ride
            ride_id = data.get('ride_id')
            print(f'❌ Driver {self.driver_id} declined ride: {ride_id}')
            await self.decline_ride(ride_id)

        elif message_type == 'location_update':
            # Driver location update
            latitude = data.get('latitude')
            longitude = data.get('longitude')
            await self.update_driver_location(latitude, longitude)

    async def ride_request(self, event):
        """Send ride request notification to driver"""
        # Forward ride request to driver
        await self.send(text_data=json.dumps(event['data']))

    @database_sync_to_async
    def accept_ride(self, ride_id):
        """Accept a ride request"""
        from bookings.models import Booking
        from drivers.models import Driver

        try:
            booking = Booking.objects.get(id=ride_id)
            driver = Driver.objects.get(user__phone_number=self.driver_id)

            # Update booking with driver
            booking.driver = driver
            booking.status = 'accepted'
            booking.accepted_at = timezone.now()
            booking.save()

            # Update driver status
            driver.status = 'busy'
            driver.save()

            print(f'✅ Ride {ride_id} accepted by driver {driver.id}')

            # Notify passenger via ride group
            from channels.layers import get_channel_layer
            import asyncio

            channel_layer = get_channel_layer()
            ride_group_name = f'ride_{ride_id}'

            asyncio.create_task(channel_layer.group_send(
                ride_group_name,
                {
                    'type': 'driver_assigned',
                    'ride_id': str(ride_id),
                    'driver_id': str(driver.id),
                    'driver_name': driver.user.get_full_name(),
                    'driver_phone': driver.user.phone_number,
                    'driver_rating': float(driver.rating) if driver.rating else 0.0,
                    'vehicle_type': driver.vehicle_type,
                    'vehicle_registration': driver.vehicle_registration,
                }
            ))

            return True
        except Exception as e:
            print(f'❌ Error accepting ride: {e}')
            return False

    @database_sync_to_async
    def decline_ride(self, ride_id):
        """Decline a ride request"""
        # Just log for now, booking stays available for other drivers
        print(f'Driver {self.driver_id} declined ride {ride_id}')
        return True

    @database_sync_to_async
    def update_driver_location(self, latitude, longitude):
        """Update driver's current location"""
        from drivers.models import Driver, DriverLocation
        from decimal import Decimal

        try:
            driver = Driver.objects.get(user__phone_number=self.driver_id)

            # Update or create driver location
            DriverLocation.objects.update_or_create(
                driver=driver,
                defaults={
                    'latitude': Decimal(str(latitude)),
                    'longitude': Decimal(str(longitude)),
                    'updated_at': timezone.now(),
                }
            )

            return True
        except Exception as e:
            print(f'❌ Error updating driver location: {e}')
            return False
