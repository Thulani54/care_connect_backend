import json
import asyncio
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth.models import User
from django.utils import timezone
from decimal import Decimal
import math

from .models import Booking
from drivers.models import Driver, DriverLocation


class RideMatchingConsumer(AsyncWebsocketConsumer):
    """WebSocket consumer for real-time ride matching"""

    async def connect(self):
        self.ride_id = self.scope['url_route']['kwargs']['ride_id']
        self.ride_group_name = f'ride_{self.ride_id}'

        # Join ride group
        await self.channel_layer.group_add(
            self.ride_group_name,
            self.channel_name
        )

        await self.accept()
        print(f'✅ WebSocket connected for ride: {self.ride_id}')

        # Send initial connection message
        await self.send(text_data=json.dumps({
            'type': 'connection_established',
            'message': 'Connected to ride matching service',
            'ride_id': self.ride_id
        }))

    async def disconnect(self, close_code):
        # Leave ride group
        await self.channel_layer.group_discard(
            self.ride_group_name,
            self.channel_name
        )
        print(f'❌ WebSocket disconnected for ride: {self.ride_id}')

    async def receive(self, text_data):
        """Handle incoming WebSocket messages"""
        data = json.loads(text_data)
        message_type = data.get('type')

        if message_type == 'ping':
            # Respond to ping
            await self.send(text_data=json.dumps({
                'type': 'pong',
                'timestamp': timezone.now().isoformat()
            }))

        elif message_type == 'find_driver':
            # Start finding a driver
            print(f'🔍 Finding driver for ride: {self.ride_id}')
            await self.find_nearest_driver(data)

        elif message_type == 'cancel_ride':
            # Cancel the ride
            await self.cancel_ride()

    async def find_nearest_driver(self, data):
        """Find the nearest available driver"""
        try:
            # Create booking in database
            booking = await self.create_booking(data)

            if not booking:
                await self.send(text_data=json.dumps({
                    'type': 'error',
                    'message': 'Failed to create booking'
                }))
                return

            # Send searching status
            await self.send(text_data=json.dumps({
                'type': 'searching',
                'message': 'Searching for available drivers...',
                'ride_id': self.ride_id
            }))

            # Find nearby drivers
            nearby_drivers = await self.get_nearby_drivers(
                float(data['pickup_latitude']),
                float(data['pickup_longitude'])
            )

            if not nearby_drivers:
                await self.send(text_data=json.dumps({
                    'type': 'no_drivers',
                    'message': 'No drivers available nearby'
                }))
                return

            # Notify drivers about the ride
            for driver in nearby_drivers[:5]:  # Notify top 5 closest drivers
                await self.notify_driver(driver, booking)

            # Simulate driver acceptance (for testing - remove in production)
            # In production, drivers will accept via their own WebSocket
            await asyncio.sleep(3)

            # For now, auto-assign the first driver
            await self.assign_driver(nearby_drivers[0], booking)

        except Exception as e:
            print(f'❌ Error finding driver: {e}')
            await self.send(text_data=json.dumps({
                'type': 'error',
                'message': str(e)
            }))

    @database_sync_to_async
    def create_booking(self, data):
        """Create a booking in the database"""
        try:
            # For testing, use first user (in production, use authenticated user)
            passenger = User.objects.first()

            booking = Booking.objects.create(
                passenger=passenger,
                passenger_phone=data.get('passenger_phone', ''),
                pickup_latitude=Decimal(str(data['pickup_latitude'])),
                pickup_longitude=Decimal(str(data['pickup_longitude'])),
                pickup_address=data['pickup_address'],
                dropoff_latitude=Decimal(str(data['dropoff_latitude'])),
                dropoff_longitude=Decimal(str(data['dropoff_longitude'])),
                dropoff_address=data['dropoff_address'],
                distance_km=Decimal(str(data.get('distance_km', 0))),
                estimated_duration_minutes=data.get('estimated_duration_minutes', 0),
                fare_amount=Decimal(str(data.get('fare_amount', 0))),
                status='pending'
            )
            print(f'✅ Booking created: #{booking.id}')
            return booking
        except Exception as e:
            print(f'❌ Error creating booking: {e}')
            return None

    @database_sync_to_async
    def get_nearby_drivers(self, pickup_lat, pickup_lon, radius_km=10):
        """Get available drivers within radius"""
        available_drivers = Driver.objects.filter(
            status='available',
            is_verified=True,
            location__isnull=False
        ).select_related('location')

        nearby = []
        for driver in available_drivers:
            distance = self.calculate_distance(
                pickup_lat,
                pickup_lon,
                float(driver.location.latitude),
                float(driver.location.longitude)
            )
            if distance <= radius_km:
                nearby.append({
                    'driver': driver,
                    'distance': distance
                })

        # Sort by distance
        nearby.sort(key=lambda x: x['distance'])
        return [item['driver'] for item in nearby]

    def calculate_distance(self, lat1, lon1, lat2, lon2):
        """Calculate distance between two points using Haversine formula"""
        lat1_rad = math.radians(lat1)
        lat2_rad = math.radians(lat2)
        lon1_rad = math.radians(lon1)
        lon2_rad = math.radians(lon2)

        dlon = lon2_rad - lon1_rad
        dlat = lat2_rad - lat1_rad
        a = math.sin(dlat / 2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon / 2)**2
        c = 2 * math.asin(math.sqrt(a))

        r = 6371  # Radius of earth in kilometers
        return c * r

    async def notify_driver(self, driver, booking):
        """Send ride request to driver's WebSocket channel"""
        print(f'📢 Notifying driver: {driver.user.get_full_name()} (Phone: {driver.user.phone_number})')

        # Send ride request to driver's WebSocket group
        driver_group_name = f'driver_{driver.user.phone_number}'

        await self.channel_layer.group_send(
            driver_group_name,
            {
                'type': 'ride_request',
                'data': {
                    'type': 'ride_request',
                    'ride_id': str(booking.id),
                    'passenger_name': booking.passenger.get_full_name(),
                    'passenger_phone': booking.passenger.phone_number,
                    'pickup_address': booking.pickup_address,
                    'dropoff_address': booking.dropoff_address,
                    'pickup_latitude': float(booking.pickup_latitude),
                    'pickup_longitude': float(booking.pickup_longitude),
                    'dropoff_latitude': float(booking.dropoff_latitude),
                    'dropoff_longitude': float(booking.dropoff_longitude),
                    'distance': float(booking.distance_km),
                    'fare': float(booking.fare_amount),
                    'estimated_duration': booking.estimated_duration_minutes,
                }
            }
        )

    @database_sync_to_async
    def assign_driver(self, driver, booking):
        """Assign driver to booking"""
        booking.driver = driver
        booking.status = 'confirmed'
        booking.save()

        driver.status = 'busy'
        driver.total_rides += 1
        driver.save()

        return booking

    async def driver_assigned(self, driver, booking):
        """Send driver assigned notification"""
        await self.send(text_data=json.dumps({
            'type': 'driver_assigned',
            'message': 'Driver found!',
            'booking_id': booking.id,
            'driver': {
                'id': driver.id,
                'name': driver.user.get_full_name(),
                'phone': driver.phone_number,
                'vehicle_type': driver.vehicle_type,
                'vehicle_registration': driver.vehicle_registration,
                'rating': float(driver.rating),
                'latitude': float(driver.location.latitude) if hasattr(driver, 'location') else None,
                'longitude': float(driver.location.longitude) if hasattr(driver, 'location') else None,
            }
        }))

    @database_sync_to_async
    def cancel_ride(self):
        """Cancel the current ride"""
        try:
            booking = Booking.objects.filter(id=self.ride_id, status='pending').first()
            if booking:
                booking.status = 'cancelled'
                booking.cancelled_at = timezone.now()
                booking.save()
                return True
            return False
        except Exception as e:
            print(f'❌ Error cancelling ride: {e}')
            return False

    # Handler for messages sent to the group
    async def ride_update(self, event):
        """Send ride update to WebSocket"""
        await self.send(text_data=json.dumps(event['data']))
