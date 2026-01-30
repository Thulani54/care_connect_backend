from django.db import models
from django.contrib.auth import get_user_model
import random
import string
from datetime import timedelta
from django.utils import timezone

User = get_user_model()


class CommunicationProvider(models.Model):
    """Store communication provider configurations"""
    PROVIDER_TYPES = [
        ('sms', 'SMS'),
        ('email', 'Email'),
        ('push', 'Push Notification'),
    ]

    name = models.CharField(max_length=100)
    provider_type = models.CharField(max_length=20, choices=PROVIDER_TYPES)
    is_active = models.BooleanField(default=True)
    api_key = models.CharField(max_length=255, blank=True)
    api_secret = models.CharField(max_length=255, blank=True)
    api_url = models.URLField(blank=True)
    sender_id = models.CharField(max_length=100, blank=True)
    config = models.JSONField(default=dict, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'communication_providers'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} ({self.get_provider_type_display()})"


class CommunicationMessage(models.Model):
    """Store all communication messages sent"""
    MESSAGE_TYPES = [
        ('otp', 'OTP'),
        ('welcome', 'Welcome'),
        ('booking_confirmation', 'Booking Confirmation'),
        ('ride_update', 'Ride Update'),
        ('notification', 'Notification'),
        ('marketing', 'Marketing'),
    ]

    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('sent', 'Sent'),
        ('failed', 'Failed'),
        ('delivered', 'Delivered'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='communications')
    provider = models.ForeignKey(CommunicationProvider, on_delete=models.SET_NULL, null=True)
    message_type = models.CharField(max_length=50, choices=MESSAGE_TYPES)
    recipient = models.CharField(max_length=255)  # Email or phone number
    subject = models.CharField(max_length=255, blank=True)
    content = models.TextField()
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    error_message = models.TextField(blank=True)
    metadata = models.JSONField(default=dict, blank=True)
    sent_at = models.DateTimeField(null=True, blank=True)
    delivered_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'communication_messages'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'message_type']),
            models.Index(fields=['status']),
            models.Index(fields=['created_at']),
        ]

    def __str__(self):
        return f"{self.get_message_type_display()} to {self.recipient} - {self.status}"


class OTP(models.Model):
    """OTP verification model"""
    OTP_TYPES = [
        ('registration', 'Registration'),
        ('login', 'Login'),
        ('password_reset', 'Password Reset'),
        ('phone_verification', 'Phone Verification'),
    ]

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='otps')
    otp_type = models.CharField(max_length=50, choices=OTP_TYPES)
    code = models.CharField(max_length=6)
    phone_number = models.CharField(max_length=20)
    is_verified = models.BooleanField(default=False)
    is_used = models.BooleanField(default=False)
    attempts = models.IntegerField(default=0)
    max_attempts = models.IntegerField(default=3)
    expires_at = models.DateTimeField()
    verified_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'otps'
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'otp_type', 'is_verified']),
            models.Index(fields=['code', 'phone_number']),
        ]

    def __str__(self):
        return f"OTP for {self.user.username} - {self.code}"

    @staticmethod
    def generate_code(length=6):
        """Generate random OTP code"""
        return ''.join(random.choices(string.digits, k=length))

    def is_valid(self):
        """Check if OTP is still valid"""
        return (
            not self.is_used
            and not self.is_verified
            and self.attempts < self.max_attempts
            and timezone.now() < self.expires_at
        )

    def verify(self, code):
        """Verify OTP code"""
        if not self.is_valid():
            return False

        self.attempts += 1

        if self.code == code:
            self.is_verified = True
            self.is_used = True
            self.verified_at = timezone.now()
            self.save()
            return True

        self.save()
        return False

    @classmethod
    def create_otp(cls, user, phone_number, otp_type='registration', expiry_minutes=10):
        """Create a new OTP"""
        code = cls.generate_code()
        expires_at = timezone.now() + timedelta(minutes=expiry_minutes)

        otp = cls.objects.create(
            user=user,
            otp_type=otp_type,
            code=code,
            phone_number=phone_number,
            expires_at=expires_at,
        )

        return otp
