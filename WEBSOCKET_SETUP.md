# WebSocket Setup for CareConnect Mobility

## Overview
The backend now uses Django Channels with WebSocket for real-time ride matching instead of Firebase.

## Features
- ✅ Real-time driver matching via WebSocket
- ✅ Ping/pong heartbeat to keep connection alive
- ✅ Find nearest available drivers within 10km radius
- ✅ Automatic driver assignment
- ✅ Ride status tracking
- ✅ Cancel ride functionality

## Installation

1. **Install dependencies:**
```bash
cd /Users/thulanimoyo/care_connect_backend
source .venv/bin/activate
pip install -r requirements.txt
```

2. **Seed test drivers:**
```bash
python manage.py seed_drivers
```

This creates 3 test drivers with locations:
- **driver1** (John Doe) - Johannesburg (-26.2041, 28.0473)
- **driver2** (Jane Smith) - Near Johannesburg (-26.1041, 28.1473)
- **driver3** (Mike Johnson) - Pretoria (-25.7479, 28.2293)

All drivers have:
- Status: `available`
- Verified: `Yes`
- Password: `password123`

## Running the Server

**Start the WebSocket server using Daphne:**
```bash
daphne -b 0.0.0.0 -p 8067 care_connect_backend.asgi:application
```

The server will start on `http://127.0.0.1:8067`

**WebSocket endpoint:**
```
ws://127.0.0.1:8067/ws/ride/<ride_id>/
```

## WebSocket Protocol

### Client → Server Messages

#### 1. Ping (Keep-alive)
```json
{
  "type": "ping"
}
```

#### 2. Find Driver
```json
{
  "type": "find_driver",
  "pickup_latitude": -26.2041,
  "pickup_longitude": 28.0473,
  "dropoff_latitude": -26.1041,
  "dropoff_longitude": 28.1473,
  "pickup_address": "123 Main St, Johannesburg",
  "dropoff_address": "456 Oak St, Johannesburg",
  "distance_km": 12.5,
  "estimated_duration_minutes": 25,
  "fare_amount": 150.00,
  "passenger_phone": "+27123456789"
}
```

#### 3. Cancel Ride
```json
{
  "type": "cancel_ride"
}
```

### Server → Client Messages

#### 1. Connection Established
```json
{
  "type": "connection_established",
  "message": "Connected to ride matching service",
  "ride_id": "12345"
}
```

#### 2. Pong
```json
{
  "type": "pong",
  "timestamp": "2025-12-23T12:34:56.789Z"
}
```

#### 3. Searching
```json
{
  "type": "searching",
  "message": "Searching for available drivers...",
  "ride_id": "12345"
}
```

#### 4. Driver Assigned
```json
{
  "type": "driver_assigned",
  "message": "Driver found!",
  "booking_id": 1,
  "driver": {
    "id": 1,
    "name": "John Doe",
    "phone": "+27123456789",
    "vehicle_type": "sedan",
    "vehicle_registration": "CA 123 GP",
    "rating": 4.8,
    "latitude": -26.2041,
    "longitude": 28.0473
  }
}
```

#### 5. No Drivers Available
```json
{
  "type": "no_drivers",
  "message": "No drivers available nearby"
}
```

#### 6. Error
```json
{
  "type": "error",
  "message": "Error description"
}
```

## Driver Matching Algorithm

1. **Receives ride request** with pickup coordinates
2. **Finds all available drivers** (status=`available`, verified=`true`)
3. **Calculates distance** using Haversine formula
4. **Filters drivers** within 10km radius
5. **Sorts by distance** (nearest first)
6. **Notifies top 5** closest drivers
7. **Auto-assigns** first driver (for testing - in production, driver accepts)
8. **Updates booking** status to `confirmed`
9. **Updates driver** status to `busy`

## Database Models

### Booking
```python
- passenger (User)
- driver (Driver)
- pickup_latitude/longitude
- dropoff_latitude/longitude
- pickup/dropoff_address
- distance_km
- fare_amount
- status: pending/confirmed/in_progress/completed/cancelled
```

### Driver
```python
- user (User)
- phone_number
- license_number
- vehicle_registration
- vehicle_type
- status: available/busy/offline
- rating
- is_verified
```

### DriverLocation
```python
- driver (Driver)
- latitude/longitude
- heading
- speed
- updated_at
```

## Testing

### 1. Start Backend Server
```bash
cd /Users/thulanimoyo/care_connect_backend
source .venv/bin/activate
daphne -b 0.0.0.0 -p 8067 care_connect_backend.asgi:application
```

### 2. Start Flutter App
```bash
cd /Users/thulanimoyo/care_connect_mobility
flutter pub get
flutter run
```

### 3. Test Flow
1. Login to app
2. Select pickup and dropoff locations
3. Request ride
4. WebSocket connects to `ws://127.0.0.1:8067/ws/ride/<ride_id>/`
5. Sends `find_driver` message with coordinates
6. Backend finds nearest driver
7. Returns `driver_assigned` message
8. App navigates to ride tracking screen

## Production Deployment

### Use Redis for Channel Layer
Update `settings.py`:
```python
CHANNEL_LAYERS = {
    "default": {
        "BACKEND": "channels_redis.core.RedisChannelLayer",
        "CONFIG": {
            "hosts": [("127.0.0.1", 6379)],
        },
    },
}
```

### Install Redis
```bash
# macOS
brew install redis
brew services start redis

# Ubuntu
sudo apt install redis-server
sudo systemctl start redis
```

### Use ASGI Server (Daphne/Uvicorn)
```bash
# Daphne
daphne -b 0.0.0.0 -p 8067 care_connect_backend.asgi:application

# Or with gunicorn + uvicorn
gunicorn care_connect_backend.asgi:application -k uvicorn.workers.UvicornWorker -b 0.0.0.0:8067
```

### SSL/TLS for WSS
```bash
# For production, use wss:// instead of ws://
wss://your-domain.com/ws/ride/<ride_id>/
```

## Troubleshooting

### WebSocket Connection Failed
- Check if Django server is running on port 8067
- Verify WebSocket URL matches server
- Check firewall settings
- Ensure Daphne is running (not runserver)

### No Drivers Found
- Run `python manage.py seed_drivers` to create test drivers
- Check driver status in Django admin (`/admin`)
- Verify driver locations exist in database

### Ping/Pong Not Working
- Check WebSocket connection is active
- Verify ping timer is running
- Check server logs for errors

## Logs

### Backend Logs
```bash
🔌 WebSocket connected for ride: 12345
🔍 Finding driver for ride: 12345
✅ Booking created: #1
📢 Notifying driver: John Doe
```

### Flutter Logs
```bash
🔌 Connecting to WebSocket: ws://127.0.0.1:8067/ws/ride/12345/
📨 Received message: connection_established
📤 Sending find_driver request
📨 Received message: searching
📨 Received message: driver_assigned
👨‍✈️ Driver: John Doe
```

## Next Steps

1. **Driver App**: Build driver mobile app to accept/reject rides
2. **Real-time Tracking**: Implement driver location updates via WebSocket
3. **Chat**: Add passenger-driver chat via WebSocket
4. **Notifications**: Send push notifications when driver accepts
5. **Payment**: Integrate payment processing
6. **Rating**: Add rating system after ride completion

## Firebase Removal

Firebase has been completely removed from the app:
- ❌ `firebase_core` - Removed
- ❌ `firebase_database` - Removed
- ✅ `web_socket_channel` - Added
- ✅ Django Channels - Implemented
- ✅ WebSocket protocol - Defined

All real-time communication now uses Django WebSocket! 🎉
