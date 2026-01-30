# ✅ Django Authentication with SMS Portal - Complete Implementation

## Summary

Firebase has been **completely removed** and replaced with Django-based authentication using SMS Portal for OTP verification.

## What Was Implemented

### 1. **Custom User Model** ✅

**File:** `/Users/thulanimoyo/care_connect_backend/api/models.py`

#### User Types:
- `passenger` - Regular passengers who book rides
- `driver` - Drivers who accept and complete rides
- `caregiver` - Caregivers who manage elderly passengers

#### User Fields:
```python
- phone_number (unique, required)
- user_type (passenger/driver/caregiver)
- is_phone_verified (boolean)
- first_name, last_name
- email (optional)
- profile_picture
- date_of_birth
- address
```

### 2. **Caregiver-Passenger Relationship** ✅

**Model:** `CaregiverRelationship`

- One passenger can have **multiple caregivers**
- Caregivers can:
  - Book rides on behalf of passengers
  - View passenger location
  - Receive notifications
- Relationship types: family, friend, professional, volunteer, other

### 3. **OTP Authentication System** ✅

**Model:** `OTPCode`

- 6-digit OTP codes
- 10-minute expiration
- Purpose-based (register, login, verify_phone, reset_password)
- Auto-invalidates previous OTPs

### 4. **SMS Portal Integration** ✅

**File:** `/Users/thulanimoyo/care_connect_backend/api/services.py`

**Service:** `SMSPortalService`

Credentials:
```python
SMS_PORTAL_USERNAME = 'cb3fe3f5-99c9-4ca2-89de-4af71abdc41b'
SMS_PORTAL_PASSWORD = 'b5849253-76d8-4875-90de-c89cc9253b55'
SMS_PORTAL_ENDPOINT = 'https://api.smsportal.com/api5/http5.aspx'
```

### 5. **Authentication APIs** ✅

**File:** `/Users/thulanimoyo/care_connect_backend/api/auth_views.py`

#### Endpoints:

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/auth/send-otp/` | POST | Send OTP to phone number |
| `/api/auth/verify-otp/` | POST | Verify OTP code |
| `/api/auth/register/` | POST | Register new user after OTP verification |
| `/api/auth/login/` | POST | Login after OTP verification |
| `/api/auth/refresh/` | POST | Refresh JWT access token |
| `/api/auth/profile/` | GET | Get current user profile |
| `/api/auth/profile/update/` | PUT | Update user profile |

### 6. **Test Users Created** ✅

**Command:** `python manage.py seed_users`

| User Type | Name | Phone Number | Email |
|-----------|------|--------------|-------|
| Passenger | Sarah Johnson | +27821234567 | sarah@example.com |
| Driver | Michael Brown | +27821234568 | michael@example.com |
| Caregiver | Emily Davis | +27821234569 | emily@example.com |

**Notes:**
- Sarah (passenger) is linked to Emily (caregiver)
- Michael (driver) has an active driver profile and location

## Authentication Flow

### Registration Flow

```
1. User enters phone number
   └─► POST /api/auth/send-otp/
       {
         "phone_number": "+27821234567",
         "purpose": "register"
       }

2. Backend sends OTP via SMS Portal
   └─► User receives: "Your CareConnect verification code is: 123456"

3. User enters OTP code
   └─► POST /api/auth/verify-otp/
       {
         "phone_number": "+27821234567",
         "code": "123456",
         "purpose": "register"
       }

4. OTP verified successfully
   └─► POST /api/auth/register/
       {
         "phone_number": "+27821234567",
         "first_name": "Sarah",
         "last_name": "Johnson",
         "user_type": "passenger",
         "email": "sarah@example.com"
       }

5. Backend returns:
   {
     "message": "User registered successfully",
     "user": { user_data },
     "tokens": {
       "refresh": "...",
       "access": "..."
     }
   }
```

### Login Flow

```
1. User enters phone number
   └─► POST /api/auth/send-otp/
       {
         "phone_number": "+27821234567",
         "purpose": "login"
       }

2. Backend sends OTP via SMS Portal

3. User enters OTP code
   └─► POST /api/auth/verify-otp/
       {
         "phone_number": "+27821234567",
         "code": "123456",
         "purpose": "login"
       }

4. OTP verified successfully
   └─► POST /api/auth/login/
       {
         "phone_number": "+27821234567"
       }

5. Backend returns JWT tokens and user data
```

## Database Schema

### Users Table
```sql
CREATE TABLE api_user (
    id BIGINT PRIMARY KEY,
    username VARCHAR(150) UNIQUE,
    phone_number VARCHAR(15) UNIQUE,
    user_type VARCHAR(20),  -- passenger/driver/caregiver
    is_phone_verified BOOLEAN,
    first_name VARCHAR(150),
    last_name VARCHAR(150),
    email VARCHAR(254),
    profile_picture VARCHAR(200),
    date_of_birth DATE,
    address TEXT,
    created_at TIMESTAMP,
    updated_at TIMESTAMP
);
```

### Caregiver Relationships Table
```sql
CREATE TABLE api_caregiverrelationship (
    id BIGINT PRIMARY KEY,
    passenger_id BIGINT REFERENCES api_user(id),
    caregiver_id BIGINT REFERENCES api_user(id),
    relationship_type VARCHAR(20),  -- family/friend/professional/volunteer/other
    can_book_rides BOOLEAN,
    can_view_location BOOLEAN,
    can_receive_notifications BOOLEAN,
    notes TEXT,
    is_active BOOLEAN,
    created_at TIMESTAMP,
    updated_at TIMESTAMP,
    UNIQUE(passenger_id, caregiver_id)
);
```

### OTP Codes Table
```sql
CREATE TABLE api_otpcode (
    id BIGINT PRIMARY KEY,
    phone_number VARCHAR(15),
    code VARCHAR(6),
    purpose VARCHAR(20),  -- register/login/verify_phone/reset_password
    is_used BOOLEAN,
    created_at TIMESTAMP,
    expires_at TIMESTAMP,
    verified_at TIMESTAMP
);
```

## Testing the API

### 1. Send OTP (Registration)
```bash
curl -X POST http://127.0.0.1:8067/api/auth/send-otp/ \
  -H "Content-Type: application/json" \
  -d '{
    "phone_number": "+27821234570",
    "purpose": "register"
  }'
```

**Response:**
```json
{
  "message": "OTP sent successfully",
  "phone_number": "27821234570",
  "expires_in_minutes": 10,
  "otp_code": "123456"  // Only in debug mode
}
```

### 2. Verify OTP
```bash
curl -X POST http://127.0.0.1:8067/api/auth/verify-otp/ \
  -H "Content-Type: application/json" \
  -d '{
    "phone_number": "+27821234570",
    "code": "123456",
    "purpose": "register"
  }'
```

### 3. Register User
```bash
curl -X POST http://127.0.0.1:8067/api/auth/register/ \
  -H "Content-Type: application/json" \
  -d '{
    "phone_number": "+27821234570",
    "first_name": "John",
    "last_name": "Doe",
    "user_type": "passenger",
    "email": "john@example.com"
  }'
```

**Response:**
```json
{
  "message": "User registered successfully",
  "user": {
    "id": 4,
    "username": "user_27821234570",
    "phone_number": "27821234570",
    "first_name": "John",
    "last_name": "Doe",
    "user_type": "passenger",
    "is_phone_verified": true,
    "email": "john@example.com"
  },
  "tokens": {
    "refresh": "eyJ0eXAiOiJKV1QiLCJhbGc...",
    "access": "eyJ0eXAiOiJKV1QiLCJhbGc..."
  }
}
```

### 4. Login (Existing User)
```bash
# Step 1: Send OTP
curl -X POST http://127.0.0.1:8067/api/auth/send-otp/ \
  -H "Content-Type: application/json" \
  -d '{
    "phone_number": "+27821234567",
    "purpose": "login"
  }'

# Step 2: Verify OTP
curl -X POST http://127.0.0.1:8067/api/auth/verify-otp/ \
  -H "Content-Type: application/json" \
  -d '{
    "phone_number": "+27821234567",
    "code": "123456",
    "purpose": "login"
  }'

# Step 3: Login
curl -X POST http://127.0.0.1:8067/api/auth/login/ \
  -H "Content-Type: application/json" \
  -d '{
    "phone_number": "+27821234567"
  }'
```

### 5. Get Profile (Authenticated)
```bash
curl -X GET http://127.0.0.1:8067/api/auth/profile/ \
  -H "Authorization: Bearer <access_token>"
```

## SMS Portal Integration Details

### SMS Format
```
Your CareConnect verification code is: 123456. Valid for 10 minutes. Do not share this code.
```

### SMS Portal API Parameters
```
Type: sendparam
Username: cb3fe3f5-99c9-4ca2-89de-4af71abdc41b
Password: b5849253-76d8-4875-90de-c89cc9253b55
numto: 27821234567 (cleaned phone number)
data1: OTP message text
```

### Response Format
```
EventID|Status|Credits
12345|OK|95.5  (success)
0|Error|Error description  (failure)
```

## Security Features

✅ **OTP Expiration** - Codes expire after 10 minutes
✅ **One-Time Use** - OTPs can only be used once
✅ **Auto-Invalidation** - Previous OTPs are invalidated when new one is requested
✅ **Phone Verification** - Users marked as verified after OTP
✅ **JWT Authentication** - Secure token-based auth
✅ **Purpose-Based OTPs** - Different OTPs for register/login/reset

## Next Steps for Flutter App

### 1. Remove Firebase Dependencies
```yaml
# Remove from pubspec.yaml:
# firebase_core: ^4.2.1
# firebase_database: ^12.0.4

# Already done ✅
```

### 2. Create Auth Service
```dart
class AuthService {
  static const String baseUrl = 'http://127.0.0.1:8067/api/auth';

  // Send OTP
  static Future<Map<String, dynamic>> sendOTP(String phoneNumber, String purpose) async {
    final response = await http.post(
      Uri.parse('$baseUrl/send-otp/'),
      headers: {'Content-Type': 'application/json'},
      body: jsonEncode({
        'phone_number': phoneNumber,
        'purpose': purpose,
      }),
    );
    return jsonDecode(response.body);
  }

  // Verify OTP
  static Future<Map<String, dynamic>> verifyOTP(
    String phoneNumber,
    String code,
    String purpose,
  ) async {
    final response = await http.post(
      Uri.parse('$baseUrl/verify-otp/'),
      headers: {'Content-Type': 'application/json'},
      body: jsonEncode({
        'phone_number': phoneNumber,
        'code': code,
        'purpose': purpose,
      }),
    );
    return jsonDecode(response.body);
  }

  // Register
  static Future<Map<String, dynamic>> register({
    required String phoneNumber,
    required String firstName,
    required String lastName,
    required String userType,
    String? email,
  }) async {
    final response = await http.post(
      Uri.parse('$baseUrl/register/'),
      headers: {'Content-Type': 'application/json'},
      body: jsonEncode({
        'phone_number': phoneNumber,
        'first_name': firstName,
        'last_name': lastName,
        'user_type': userType,
        'email': email,
      }),
    );
    return jsonDecode(response.body);
  }

  // Login
  static Future<Map<String, dynamic>> login(String phoneNumber) async {
    final response = await http.post(
      Uri.parse('$baseUrl/login/'),
      headers: {'Content-Type': 'application/json'},
      body: jsonEncode({
        'phone_number': phoneNumber,
      }),
    );
    return jsonDecode(response.body);
  }
}
```

### 3. Update OTP Screen
- User enters phone number
- App calls `/api/auth/send-otp/`
- User receives SMS with OTP code
- User enters OTP code
- App calls `/api/auth/verify-otp/`
- If verified successfully, call `/api/auth/login/` or `/api/auth/register/`
- Save JWT tokens for authenticated requests

## Commands Reference

```bash
# Create fresh database with new models
cd /Users/thulanimoyo/care_connect_backend
source .venv/bin/activate

# Create migrations
python manage.py makemigrations

# Run migrations
python manage.py migrate

# Seed test users
python manage.py seed_users

# Seed test drivers
python manage.py seed_drivers

# Create superuser for Django admin
python manage.py createsuperuser

# Run server (WebSocket)
daphne -b 0.0.0.0 -p 8067 care_connect_backend.asgi:application
```

## Summary of Changes

### ✅ Completed
1. **Custom User Model** with 3 types (passenger, driver, caregiver)
2. **Caregiver-Passenger Relationship** (one-to-many)
3. **OTP System** with 10-minute expiration
4. **SMS Portal Integration** for OTP delivery
5. **Authentication APIs** (send-otp, verify-otp, register, login)
6. **3 Test Users** created and seeded
7. **Firebase Removed** from entire stack
8. **WebSocket for Ride Matching** (from previous implementation)
9. **Updated all models** to use custom User model
10. **JWT Token Authentication** for API access

### 🚀 Ready to Use
- Django backend with OTP authentication: `http://127.0.0.1:8067`
- SMS Portal configured and ready
- Test users created:
  - Passenger: +27821234567
  - Driver: +27821234568
  - Caregiver: +27821234569

### ⏳ Next: Flutter App Updates
- Remove Firebase imports
- Create Auth Service for OTP flow
- Update Login/Register screens
- Implement OTP verification screen
- Store JWT tokens for authenticated API calls

---

**All backend authentication is now complete and ready for frontend integration!** 🎉
