# WebSocket Ride Request System - Complete Implementation

## Summary

Successfully implemented a real-time WebSocket-based ride request and notification system that connects passengers, drivers, and the Django backend.

## Architecture

```
Passenger App → Django WebSocket (RideMatchingConsumer) → Django WebSocket (DriverConsumer) → Driver App
     ↓                                                              ↓
  Book Ride                                                  Receive Notification
  Wait for Driver                                           Accept/Decline Ride
     ↓                                                              ↓
  Receive Driver Info  ←  Django Updates Booking  ←  Driver Accepts
```

## Backend Implementation

### 1. Django WebSocket Consumers

#### RideMatchingConsumer (`bookings/consumers.py`)
- **URL**: `ws://127.0.0.1:8067/ws/ride/<ride_id>/`
- **Purpose**: Handle passenger ride requests
- **Features**:
  - Receives ride booking details from passenger
  - Finds nearby available drivers (within 10km)
  - Notifies top 5 closest drivers via their WebSocket channels
  - Sends real-time status updates to passenger

**Key Methods**:
```python
async def find_nearest_driver(data):
    # Create booking
    # Find nearby drivers
    # Notify drivers via WebSocket

async def notify_driver(driver, booking):
    # Send ride request to driver's WebSocket group
    await channel_layer.group_send(
        f'driver_{driver.user.phone_number}',
        {'type': 'ride_request', 'data': {...}}
    )
```

#### DriverConsumer (`drivers/consumers.py`)
- **URL**: `ws://127.0.0.1:8067/ws/driver/<driver_id>/`
- **Purpose**: Handle driver connections and ride responses
- **Features**:
  - Maintains persistent connection with online drivers
  - Receives ride acceptance/decline from drivers
  - Updates booking status when driver accepts
  - Sends notifications back to passengers
  - Tracks driver location updates

**Key Methods**:
```python
async def ride_request(event):
    # Forward ride request to driver
    await self.send(text_data=json.dumps(event['data']))

async def accept_ride(ride_id):
    # Update booking with driver
    # Update driver status to 'busy'
    # Notify passenger
```

### 2. WebSocket URL Routing

**File**: `bookings/routing.py`
```python
websocket_urlpatterns = [
    re_path(r'ws/ride/(?P<ride_id>\w+)/$', RideMatchingConsumer.as_asgi()),
    re_path(r'ws/driver/(?P<driver_id>[\w\+]+)/$', DriverConsumer.as_asgi()),
]
```

## Driver App Implementation

### 1. RideRequestService (`core/services/ride_request_service.dart`)

**Purpose**: Manages WebSocket connection for drivers

**Features**:
- Connects to Django WebSocket: `ws://127.0.0.1:8067/ws/driver/<phone_number>/`
- Heartbeat ping/pong every 5 seconds
- Stream-based ride request notifications
- Accept/decline ride methods
- Location update broadcasting

**Key Methods**:
```dart
void connect(String driverId)
void acceptRide(String rideId)
void declineRide(String rideId)
void updateLocation(double latitude, double longitude)
Stream<Map<String, dynamic>> get rideRequestStream
```

### 2. RideRequestDialog (`features/rides/presentation/widgets/ride_request_dialog.dart`)

**Purpose**: Display ride request notification to driver

**Features**:
- Animated popup dialog
- Shows passenger name, pickup/dropoff locations
- Displays distance and fare
- Accept/Decline buttons
- Auto-dismissible on action

### 3. Home Screen Integration

**File**: `features/rides/presentation/pages/home_screen.dart`

**Changes**:
- Added RideRequestService initialization
- WebSocket connection on app start
- Stream listener for incoming ride requests
- Dialog display for new requests
- Accept/decline action handlers

```dart
void _initializeWebSocket() {
  _rideRequestService.connect(driverPhone);
  _rideRequestSubscription = _rideRequestService.rideRequestStream.listen(
    (rideData) {
      if (rideData['type'] == 'ride_request') {
        _showRideRequestDialog(rideData);
      }
    },
  );
}
```

## Passenger App Implementation

### WebSocket Integration

**File**: `features/booking/presentation/pages/ride_waiting_screen.dart`

**Already Implemented**:
- Connects to `ws://127.0.0.1:8067/ws/ride/<ride_id>/`
- Sends `find_driver` message with booking details
- Receives real-time updates:
  - `searching` - Looking for drivers
  - `driver_assigned` - Driver accepted
  - `no_drivers` - No drivers available

## Complete Flow

### 1. Passenger Books Ride
```
1. Passenger enters pickup/dropoff locations
2. Gets fare calculation from pricing API
3. Confirms booking
4. App navigates to RideWaitingScreen
5. WebSocket connects to ws://127.0.0.1:8067/ws/ride/<ride_id>/
6. Sends 'find_driver' message with:
   - pickup_latitude, pickup_longitude
   - dropoff_latitude, dropoff_longitude
   - pickup_address, dropoff_address
   - distance_km, estimated_duration_minutes, fare_amount
```

### 2. Backend Processes Request
```
1. RideMatchingConsumer receives find_driver message
2. Creates Booking in database (status='pending')
3. Finds drivers within 10km using Haversine formula
4. Sorts drivers by distance (closest first)
5. Sends ride_request to top 5 drivers via their WebSocket groups
```

### 3. Driver Receives Notification
```
1. DriverConsumer receives ride_request via channel_layer.group_send
2. Forwards to driver's WebSocket connection
3. Driver app RideRequestService receives message
4. Stream emits ride data
5. HomeScreen displays RideRequestDialog
6. Shows passenger name, locations, distance, fare
```

### 4. Driver Accepts Ride
```
1. Driver taps "Accept" button
2. RideRequestService sends accept_ride message
3. DriverConsumer.accept_ride() method:
   - Updates Booking.driver = driver
   - Updates Booking.status = 'accepted'
   - Updates Driver.status = 'busy'
   - Sends driver_assigned to passenger via ride group
4. Dialog closes
5. Driver app shows success message
```

### 5. Passenger Receives Driver Info
```
1. RideWaitingScreen receives driver_assigned message
2. Displays driver information:
   - Name, phone number
   - Vehicle type, registration
   - Driver rating
3. Shows "Driver on the way" status
4. Can navigate to active ride tracking
```

## Message Formats

### Ride Request (Backend → Driver)
```json
{
  "type": "ride_request",
  "ride_id": "123",
  "passenger_name": "Sarah Johnson",
  "passenger_phone": "27821234567",
  "pickup_address": "123 Main St",
  "dropoff_address": "456 Oak Ave",
  "pickup_latitude": -26.2041,
  "pickup_longitude": 28.0473,
  "dropoff_latitude": -26.1850,
  "dropoff_longitude": 28.0550,
  "distance": 5.2,
  "fare": 85.50,
  "estimated_duration": 15
}
```

### Accept Ride (Driver → Backend)
```json
{
  "type": "accept_ride",
  "ride_id": "123",
  "driver_id": "27821234568"
}
```

### Driver Assigned (Backend → Passenger)
```json
{
  "type": "driver_assigned",
  "ride_id": "123",
  "driver_id": "2",
  "driver_name": "Michael Brown",
  "driver_phone": "27821234568",
  "driver_rating": 4.9,
  "vehicle_type": "sedan",
  "vehicle_registration": "CA 999 GP"
}
```

## Testing

### Start Django WebSocket Server
```bash
cd /Users/thulanimoyo/care_connect_backend
source .venv/bin/activate
daphne -b 0.0.0.0 -p 8067 care_connect_backend.asgi:application
```

### Test with Seeded Users
- **Passenger**: +27821234567 (Sarah Johnson)
- **Driver**: +27821234568 (Michael Brown)

### Test Flow
1. Open driver app, login with +27821234568
2. Driver connects to WebSocket automatically
3. Open passenger app, login with +27821234567
4. Book a ride in passenger app
5. Driver receives notification popup
6. Driver can accept or decline
7. Passenger sees driver info on acceptance

## Features Implemented

### Backend
- ✅ WebSocket consumers for passengers and drivers
- ✅ Real-time ride request broadcasting
- ✅ Driver proximity calculation (Haversine formula)
- ✅ Accept/decline ride handling
- ✅ Booking status updates
- ✅ Heartbeat ping/pong
- ✅ Channel layer group messaging

### Driver App
- ✅ OTP authentication with Django
- ✅ WebSocket service integration
- ✅ Ride request notification dialog
- ✅ Accept/decline functionality
- ✅ Real-time connection management
- ✅ Stream-based message handling

### Passenger App
- ✅ OTP authentication with Django
- ✅ WebSocket ride matching
- ✅ Real-time driver search
- ✅ Driver assignment notifications
- ✅ Fare calculation integration

## Next Steps (Optional Enhancements)

1. **Production Channel Layer**
   - Replace InMemoryChannelLayer with Redis
   - Install: `pip install channels-redis`
   - Configure in settings.py

2. **Ride Tracking**
   - Real-time driver location updates
   - ETA calculation
   - Live map tracking for passenger

3. **Ride Completion**
   - Driver marks ride as completed
   - Payment processing
   - Rating system

4. **Push Notifications**
   - FCM integration for offline drivers
   - Background notification handling

5. **Driver Rejection Handling**
   - If all 5 drivers decline, find next batch
   - Timeout mechanism (30 seconds)
   - Auto-decline on timeout

---

**Status**: ✅ WebSocket ride request system fully implemented and ready for testing!
**Both Apps Ready**: Passenger app + Driver app with real-time communication
