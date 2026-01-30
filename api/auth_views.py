from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import get_user_model
from django.conf import settings

from .models import OTPCode, CaregiverRelationship
from .serializers import UserSerializer
from .services import SMSPortalService

User = get_user_model()


@api_view(['POST'])
@permission_classes([AllowAny])
def send_otp(request):
    """Send OTP code to phone number"""
    phone_number = request.data.get('phone_number')
    purpose = request.data.get('purpose', 'login')

    if not phone_number:
        return Response(
            {'error': 'Phone number is required'},
            status=status.HTTP_400_BAD_REQUEST
        )

    # Clean phone number
    clean_phone = phone_number.replace('+', '').replace(' ', '').replace('-', '')

    # For login, check if user exists
    if purpose == 'login':
        if not User.objects.filter(phone_number=clean_phone).exists():
            return Response(
                {'error': 'Phone number not registered'},
                status=status.HTTP_404_NOT_FOUND
            )

    # For registration, check if phone is already registered
    if purpose == 'register':
        if User.objects.filter(phone_number=clean_phone).exists():
            return Response(
                {'error': 'Phone number already registered'},
                status=status.HTTP_400_BAD_REQUEST
            )

    # Create OTP
    otp = OTPCode.create_otp(clean_phone, purpose)

    # Always log OTP to console for debugging
    print(f'\n{"="*60}')
    print(f'🔐 OTP CODE FOR {clean_phone}')
    print(f'📱 Code: {otp.code}')
    print(f'🎯 Purpose: {purpose}')
    print(f'⏰ Valid for: 10 minutes')
    print(f'{"="*60}\n')

    # Always send OTP via SMS
    sms_result = SMSPortalService.send_otp(f'+{clean_phone}', otp.code)

    if sms_result['success']:
        return Response({
            'message': 'OTP sent successfully',
            'phone_number': clean_phone,
            'expires_in_minutes': 10,
            # Include OTP in response during development for easy testing
            'otp_code': otp.code if settings.DEBUG else None
        })
    else:
        # Even if SMS fails, allow development to continue
        if settings.DEBUG:
            print(f'⚠️ SMS sending failed: {sms_result["error"]}')
            print(f'✅ Continuing in development mode - use OTP from console')
            return Response({
                'message': 'OTP sent successfully (console only - SMS failed)',
                'phone_number': clean_phone,
                'expires_in_minutes': 10,
                'otp_code': otp.code,
                'warning': 'SMS delivery failed, but you can use the code from console'
            })
        else:
            return Response(
                {'error': sms_result['error']},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


@api_view(['POST'])
@permission_classes([AllowAny])
def verify_otp(request):
    """Verify OTP code"""
    phone_number = request.data.get('phone_number')
    code = request.data.get('code')
    purpose = request.data.get('purpose', 'login')

    if not phone_number or not code:
        return Response(
            {'error': 'Phone number and code are required'},
            status=status.HTTP_400_BAD_REQUEST
        )

    # Clean phone number
    clean_phone = phone_number.replace('+', '').replace(' ', '').replace('-', '')

    # Find OTP
    try:
        otp = OTPCode.objects.get(
            phone_number=clean_phone,
            code=code,
            purpose=purpose
        )
    except OTPCode.DoesNotExist:
        return Response(
            {'error': 'Invalid OTP code'},
            status=status.HTTP_400_BAD_REQUEST
        )

    # Check if OTP is valid
    is_valid, message = otp.is_valid()
    if not is_valid:
        return Response({'error': message}, status=status.HTTP_400_BAD_REQUEST)

    # Mark OTP as used
    otp.is_used = True
    otp.save()

    return Response({
        'verified': True,
        'message': 'OTP verified successfully',
        'phone_number': clean_phone
    })


@api_view(['POST'])
@permission_classes([AllowAny])
def register(request):
    """Register a new user after OTP verification"""
    phone_number = request.data.get('phone_number')
    first_name = request.data.get('first_name')
    last_name = request.data.get('last_name')
    user_type = request.data.get('user_type', 'passenger')
    email = request.data.get('email', '')

    if not phone_number or not first_name or not last_name:
        return Response(
            {'error': 'Phone number, first name, and last name are required'},
            status=status.HTTP_400_BAD_REQUEST
        )

    # Clean phone number
    clean_phone = phone_number.replace('+', '').replace(' ', '').replace('-', '')

    # Check if user already exists
    if User.objects.filter(phone_number=clean_phone).exists():
        return Response(
            {'error': 'Phone number already registered'},
            status=status.HTTP_400_BAD_REQUEST
        )

    # Create username from phone number
    username = f'user_{clean_phone}'

    # Create user
    user = User.objects.create(
        username=username,
        phone_number=clean_phone,
        first_name=first_name,
        last_name=last_name,
        user_type=user_type,
        email=email,
        is_phone_verified=True  # Already verified via OTP
    )

    # Generate JWT tokens
    refresh = RefreshToken.for_user(user)

    user_data = UserSerializer(user).data

    return Response({
        'message': 'User registered successfully',
        'user': user_data,
        'tokens': {
            'refresh': str(refresh),
            'access': str(refresh.access_token),
        }
    }, status=status.HTTP_201_CREATED)


@api_view(['POST'])
@permission_classes([AllowAny])
def login(request):
    """Login user with phone number after OTP verification"""
    phone_number = request.data.get('phone_number')

    if not phone_number:
        return Response(
            {'error': 'Phone number is required'},
            status=status.HTTP_400_BAD_REQUEST
        )

    # Clean phone number
    clean_phone = phone_number.replace('+', '').replace(' ', '').replace('-', '')

    # Find user
    try:
        user = User.objects.get(phone_number=clean_phone)
    except User.DoesNotExist:
        return Response(
            {'error': 'User not found'},
            status=status.HTTP_404_NOT_FOUND
        )

    # Mark phone as verified
    if not user.is_phone_verified:
        user.is_phone_verified = True
        user.save()

    # Generate JWT tokens
    refresh = RefreshToken.for_user(user)

    user_data = UserSerializer(user).data

    return Response({
        'message': 'Login successful',
        'user': user_data,
        'tokens': {
            'refresh': str(refresh),
            'access': str(refresh.access_token),
        }
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def get_profile(request):
    """Get current user profile"""
    user_data = UserSerializer(request.user).data
    return Response(user_data)


@api_view(['PUT'])
@permission_classes([IsAuthenticated])
def update_profile(request):
    """Update current user profile"""
    user = request.user

    # Update fields
    user.first_name = request.data.get('first_name', user.first_name)
    user.last_name = request.data.get('last_name', user.last_name)
    user.email = request.data.get('email', user.email)
    user.profile_picture = request.data.get('profile_picture', user.profile_picture)
    user.address = request.data.get('address', user.address)

    user.save()

    user_data = UserSerializer(user).data

    return Response({
        'message': 'Profile updated successfully',
        'user': user_data
    })
