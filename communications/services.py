import requests
import logging
from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils.html import strip_tags
from django.utils import timezone
from .models import CommunicationProvider, CommunicationMessage

logger = logging.getLogger(__name__)


class BulkSMSService:
    """Service for sending SMS via BulkSMS"""

    def __init__(self):
        self.api_url = settings.BULKSMS_API_URL
        self.api_key = settings.BULKSMS_API_KEY
        self.api_secret = settings.BULKSMS_API_SECRET
        self.sender_id = settings.BULKSMS_SENDER_ID

    def send_sms(self, phone_number, message, user=None, message_type='notification'):
        """Send SMS via BulkSMS API"""
        try:
            # Get or create SMS provider
            provider, _ = CommunicationProvider.objects.get_or_create(
                name='BulkSMS',
                provider_type='sms',
                defaults={
                    'api_key': self.api_key,
                    'api_secret': self.api_secret,
                    'api_url': self.api_url,
                    'sender_id': self.sender_id,
                }
            )

            # Create communication record
            comm_message = CommunicationMessage.objects.create(
                user=user,
                provider=provider,
                message_type=message_type,
                recipient=phone_number,
                content=message,
                status='pending'
            )

            # Prepare API request
            headers = {
                'Content-Type': 'application/json',
            }

            payload = {
                'to': phone_number,
                'body': message,
            }

            # Make API call
            response = requests.post(
                self.api_url,
                json=payload,
                auth=(self.api_key, self.api_secret),
                headers=headers,
                timeout=30
            )

            # Update communication record
            if response.status_code == 201:
                comm_message.status = 'sent'
                comm_message.sent_at = timezone.now()
                comm_message.metadata = response.json()
                logger.info(f"SMS sent successfully to {phone_number}")
            else:
                comm_message.status = 'failed'
                comm_message.error_message = f"Status: {response.status_code}, Response: {response.text}"
                logger.error(f"Failed to send SMS to {phone_number}: {response.text}")

            comm_message.save()
            return comm_message.status == 'sent'

        except Exception as e:
            logger.exception(f"Error sending SMS to {phone_number}: {str(e)}")
            if 'comm_message' in locals():
                comm_message.status = 'failed'
                comm_message.error_message = str(e)
                comm_message.save()
            return False


class EmailService:
    """Service for sending emails"""

    def __init__(self):
        self.from_email = settings.DEFAULT_FROM_EMAIL

    def send_email(self, recipient_email, subject, message, user=None, message_type='notification', html_message=None):
        """Send email"""
        try:
            # Get or create Email provider
            provider, _ = CommunicationProvider.objects.get_or_create(
                name='Django Email',
                provider_type='email',
                defaults={
                    'sender_id': self.from_email,
                }
            )

            # Create communication record
            comm_message = CommunicationMessage.objects.create(
                user=user,
                provider=provider,
                message_type=message_type,
                recipient=recipient_email,
                subject=subject,
                content=message,
                status='pending'
            )

            try:
                # Send email
                send_mail(
                    subject=subject,
                    message=message,
                    from_email=self.from_email,
                    recipient_list=[recipient_email],
                    html_message=html_message,
                    fail_silently=False,
                )

                comm_message.status = 'sent'
                comm_message.sent_at = timezone.now()
                logger.info(f"Email sent successfully to {recipient_email}")

            except Exception as e:
                comm_message.status = 'failed'
                comm_message.error_message = str(e)
                logger.error(f"Failed to send email to {recipient_email}: {str(e)}")

            comm_message.save()
            return comm_message.status == 'sent'

        except Exception as e:
            logger.exception(f"Error sending email to {recipient_email}: {str(e)}")
            return False

    def send_welcome_email(self, user):
        """Send welcome email to new user"""
        subject = 'Welcome to Care Connect Mobility'
        message = f"""
        Dear {user.first_name or user.username},

        Welcome to Care Connect Mobility Solutions!

        We're excited to have you on board. Our platform is designed to provide accessible
        and compassionate transportation services for individuals with mobility needs.

        Your account has been successfully created. You can now:
        - Book rides on-demand or in advance
        - Track your rides in real-time
        - Share your location with family and caregivers
        - Access trained and professional drivers

        If you have any questions or need assistance, please don't hesitate to contact
        our support team.

        Best regards,
        The Care Connect Team
        """

        html_message = f"""
        <html>
        <body style="font-family: Arial, sans-serif; line-height: 1.6; color: #333;">
            <div style="max-width: 600px; margin: 0 auto; padding: 20px;">
                <h2 style="color: #000;">Welcome to Care Connect Mobility</h2>
                <p>Dear {user.first_name or user.username},</p>
                <p>Welcome to <strong>Care Connect Mobility Solutions</strong>!</p>
                <p>We're excited to have you on board. Our platform is designed to provide accessible
                and compassionate transportation services for individuals with mobility needs.</p>

                <div style="background-color: #f5f5f5; padding: 15px; border-radius: 5px; margin: 20px 0;">
                    <h3 style="margin-top: 0;">Your account has been successfully created!</h3>
                    <p style="margin-bottom: 0;">You can now:</p>
                    <ul>
                        <li>Book rides on-demand or in advance</li>
                        <li>Track your rides in real-time</li>
                        <li>Share your location with family and caregivers</li>
                        <li>Access trained and professional drivers</li>
                    </ul>
                </div>

                <p>If you have any questions or need assistance, please don't hesitate to contact
                our support team.</p>

                <p>Best regards,<br>
                <strong>The Care Connect Team</strong></p>
            </div>
        </body>
        </html>
        """

        return self.send_email(
            recipient_email=user.email,
            subject=subject,
            message=message,
            user=user,
            message_type='welcome',
            html_message=html_message
        )


class OTPService:
    """Service for OTP operations"""

    def __init__(self):
        self.sms_service = BulkSMSService()

    def send_otp(self, otp):
        """Send OTP via SMS"""
        message = f"Your Care Connect verification code is: {otp.code}. Valid for 10 minutes. Do not share this code."

        success = self.sms_service.send_sms(
            phone_number=otp.phone_number,
            message=message,
            user=otp.user,
            message_type='otp'
        )

        return success
