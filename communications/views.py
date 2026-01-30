from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from django.contrib.auth import get_user_model
from .models import OTP
from .services import OTPService, EmailService
import logging

logger = logging.getLogger(__name__)
User = get_user_model()


@api_view(['POST'])
@permission_classes([AllowAny])
def send_otp(request):
    """
    Send OTP to user's phone number
    Request body: {
        "user_id": "1",
        "phone_number": "+27821234567",
        "otp_type": "registration"  # optional, defaults to "registration"
    }
    """
    try:
        user_id = request.data.get('user_id')
        phone_number = request.data.get('phone_number')
        otp_type = request.data.get('otp_type', 'registration')

        if not user_id or not phone_number:
            return Response(
                {'error': 'user_id and phone_number are required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Get user
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response(
                {'error': 'User not found'},
                status=status.HTTP_404_NOT_FOUND
            )

        # Invalidate any existing OTPs for this user and type
        OTP.objects.filter(
            user=user,
            otp_type=otp_type,
            is_verified=False
        ).update(is_used=True)

        # Create new OTP
        otp = OTP.create_otp(
            user=user,
            phone_number=phone_number,
            otp_type=otp_type,
            expiry_minutes=10
        )

        # Send OTP via SMS
        otp_service = OTPService()
        success = otp_service.send_otp(otp)

        if success:
            logger.info(f"OTP sent successfully to {phone_number} for user {user.username}")
            return Response({
                'message': 'OTP sent successfully',
                'expires_at': otp.expires_at.isoformat(),
            }, status=status.HTTP_200_OK)
        else:
            logger.error(f"Failed to send OTP to {phone_number}")
            return Response(
                {'error': 'Failed to send OTP. Please try again.'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    except Exception as e:
        logger.exception(f"Error in send_otp: {str(e)}")
        return Response(
            {'error': 'An error occurred while sending OTP'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([AllowAny])
def verify_otp(request):
    """
    Verify OTP code
    Request body: {
        "user_id": "1",
        "phone_number": "+27821234567",
        "code": "123456",
        "otp_type": "registration"  # optional
    }
    """
    try:
        user_id = request.data.get('user_id')
        phone_number = request.data.get('phone_number')
        code = request.data.get('code')
        otp_type = request.data.get('otp_type', 'registration')

        if not user_id or not phone_number or not code:
            return Response(
                {'error': 'user_id, phone_number, and code are required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Get user
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response(
                {'error': 'User not found'},
                status=status.HTTP_404_NOT_FOUND
            )

        # Get the latest OTP for this user
        try:
            otp = OTP.objects.filter(
                user=user,
                phone_number=phone_number,
                otp_type=otp_type,
                is_used=False
            ).latest('created_at')
        except OTP.DoesNotExist:
            return Response(
                {'error': 'No OTP found for this user'},
                status=status.HTTP_404_NOT_FOUND
            )

        # Verify OTP
        if otp.verify(code):
            logger.info(f"OTP verified successfully for user {user.username}")

            # Send welcome email after successful verification
            if otp_type == 'registration':
                try:
                    email_service = EmailService()
                    email_service.send_welcome_email(user)
                except Exception as e:
                    logger.error(f"Failed to send welcome email: {str(e)}")

            return Response({
                'message': 'OTP verified successfully',
                'verified': True
            }, status=status.HTTP_200_OK)
        else:
            # Check if OTP is still valid
            if not otp.is_valid():
                error_message = 'OTP has expired or maximum attempts exceeded'
            else:
                error_message = 'Invalid OTP code'

            logger.warning(f"OTP verification failed for user {user.username}: {error_message}")
            return Response(
                {
                    'error': error_message,
                    'verified': False,
                    'attempts_remaining': max(0, otp.max_attempts - otp.attempts)
                },
                status=status.HTTP_400_BAD_REQUEST
            )

    except Exception as e:
        logger.exception(f"Error in verify_otp: {str(e)}")
        return Response(
            {'error': 'An error occurred while verifying OTP'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(['POST'])
@permission_classes([AllowAny])
def resend_otp(request):
    """
    Resend OTP to user's phone number
    Request body: {
        "user_id": "1",
        "phone_number": "+27821234567",
        "otp_type": "registration"  # optional
    }
    """
    try:
        user_id = request.data.get('user_id')
        phone_number = request.data.get('phone_number')
        otp_type = request.data.get('otp_type', 'registration')

        if not user_id or not phone_number:
            return Response(
                {'error': 'user_id and phone_number are required'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Get user
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response(
                {'error': 'User not found'},
                status=status.HTTP_404_NOT_FOUND
            )

        # Invalidate all previous OTPs
        OTP.objects.filter(
            user=user,
            otp_type=otp_type,
            is_verified=False
        ).update(is_used=True)

        # Create and send new OTP
        otp = OTP.create_otp(
            user=user,
            phone_number=phone_number,
            otp_type=otp_type,
            expiry_minutes=10
        )

        otp_service = OTPService()
        success = otp_service.send_otp(otp)

        if success:
            logger.info(f"OTP resent successfully to {phone_number}")
            return Response({
                'message': 'OTP resent successfully',
                'expires_at': otp.expires_at.isoformat(),
            }, status=status.HTTP_200_OK)
        else:
            return Response(
                {'error': 'Failed to resend OTP. Please try again.'},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    except Exception as e:
        logger.exception(f"Error in resend_otp: {str(e)}")
        return Response(
            {'error': 'An error occurred while resending OTP'},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )
