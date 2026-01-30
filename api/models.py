from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone
from datetime import timedelta
import random


class User(AbstractUser):
    """Extended User model with user types"""

    USER_TYPE_CHOICES = [
        ('passenger', 'Passenger'),
        ('driver', 'Driver'),
        ('caregiver', 'Caregiver'),
    ]

    user_type = models.CharField(max_length=20, choices=USER_TYPE_CHOICES, default='passenger')
    phone_number = models.CharField(max_length=15, unique=True)
    is_phone_verified = models.BooleanField(default=False)
    profile_picture = models.URLField(blank=True, null=True)
    date_of_birth = models.DateField(blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.get_full_name()} ({self.user_type}) - {self.phone_number}"


class CaregiverRelationship(models.Model):
    """Links passengers to their caregivers"""

    RELATIONSHIP_CHOICES = [
        ('family', 'Family Member'),
        ('friend', 'Friend'),
        ('professional', 'Professional Caregiver'),
        ('volunteer', 'Volunteer'),
        ('other', 'Other'),
    ]

    passenger = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='caregiver_relationships',
        limit_choices_to={'user_type': 'passenger'}
    )
    caregiver = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='patient_relationships',
        limit_choices_to={'user_type': 'caregiver'}
    )
    relationship_type = models.CharField(max_length=20, choices=RELATIONSHIP_CHOICES)
    can_book_rides = models.BooleanField(default=True)
    can_view_location = models.BooleanField(default=True)
    can_receive_notifications = models.BooleanField(default=True)
    notes = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ('passenger', 'caregiver')
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.passenger.get_full_name()} -> {self.caregiver.get_full_name()} ({self.relationship_type})"


class OTPCode(models.Model):
    """OTP codes for phone verification and authentication"""

    PURPOSE_CHOICES = [
        ('register', 'Registration'),
        ('login', 'Login'),
        ('reset_password', 'Reset Password'),
        ('verify_phone', 'Verify Phone'),
    ]

    phone_number = models.CharField(max_length=15)
    code = models.CharField(max_length=6)
    purpose = models.CharField(max_length=20, choices=PURPOSE_CHOICES)
    is_used = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    verified_at = models.DateTimeField(blank=True, null=True)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['phone_number', 'code', 'purpose']),
        ]

    def __str__(self):
        return f"{self.phone_number} - {self.code} ({self.purpose})"

    def is_valid(self):
        """Check if OTP is still valid"""
        if self.is_used:
            return False, "OTP already used"
        if timezone.now() > self.expires_at:
            return False, "OTP expired"
        return True, "OTP is valid"

    @staticmethod
    def generate_code():
        """Generate a 6-digit OTP code"""
        return str(random.randint(100000, 999999))

    @classmethod
    def create_otp(cls, phone_number, purpose, expiry_minutes=10):
        """Create a new OTP code"""
        code = cls.generate_code()
        expires_at = timezone.now() + timedelta(minutes=expiry_minutes)

        # Invalidate all previous OTPs for this phone and purpose
        cls.objects.filter(
            phone_number=phone_number,
            purpose=purpose,
            is_used=False
        ).update(is_used=True)

        # Create new OTP
        otp = cls.objects.create(
            phone_number=phone_number,
            code=code,
            purpose=purpose,
            expires_at=expires_at
        )

        return otp


class ElderlyMember(models.Model):
    """Model for storing elderly family members (for caregivers)"""
    caregiver = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='elderly_members',
        limit_choices_to={'user_type': 'caregiver'}
    )
    name = models.CharField(max_length=255)
    relationship = models.CharField(max_length=100)
    age = models.IntegerField()
    phone_number = models.CharField(max_length=20, blank=True, null=True)
    emergency_contact = models.CharField(max_length=20)
    medical_conditions = models.TextField(blank=True, null=True)
    special_needs = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.name} ({self.relationship})"
