from django.db import models
from django.conf import settings
from drivers.models import Driver
from api.models import ElderlyMember


class Booking(models.Model):
    """Booking model for Care Connect Mobility"""

    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('confirmed', 'Confirmed'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('cancelled', 'Cancelled'),
    ]

    PAYMENT_STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('paid', 'Paid'),
        ('failed', 'Failed'),
        ('refunded', 'Refunded'),
    ]

    # Passenger information
    passenger = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='bookings')
    passenger_phone = models.CharField(max_length=15)

    # Elderly member (optional - for bookings made on behalf of elderly)
    elderly_member = models.ForeignKey(
        ElderlyMember,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='bookings'
    )

    # Driver assignment
    driver = models.ForeignKey(
        Driver,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='bookings'
    )

    # Location details
    pickup_latitude = models.DecimalField(max_digits=9, decimal_places=6)
    pickup_longitude = models.DecimalField(max_digits=9, decimal_places=6)
    pickup_address = models.TextField()

    dropoff_latitude = models.DecimalField(max_digits=9, decimal_places=6)
    dropoff_longitude = models.DecimalField(max_digits=9, decimal_places=6)
    dropoff_address = models.TextField()

    # Trip details
    distance_km = models.DecimalField(max_digits=6, decimal_places=2, null=True, blank=True)
    estimated_duration_minutes = models.IntegerField(null=True, blank=True)
    fare_amount = models.DecimalField(max_digits=10, decimal_places=2)

    # Status tracking
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS_CHOICES, default='pending')

    # Timestamps
    booking_time = models.DateTimeField(auto_now_add=True)
    pickup_time = models.DateTimeField(null=True, blank=True)
    dropoff_time = models.DateTimeField(null=True, blank=True)
    cancelled_at = models.DateTimeField(null=True, blank=True)

    # Additional information
    special_requirements = models.TextField(blank=True)
    cancellation_reason = models.TextField(blank=True)

    # Rating
    passenger_rating = models.IntegerField(null=True, blank=True)  # 1-5 stars
    driver_rating = models.IntegerField(null=True, blank=True)  # 1-5 stars
    feedback = models.TextField(blank=True)

    class Meta:
        ordering = ['-booking_time']
        indexes = [
            models.Index(fields=['status', '-booking_time']),
            models.Index(fields=['passenger', '-booking_time']),
            models.Index(fields=['driver', '-booking_time']),
        ]

    def __str__(self):
        return f"Booking #{self.id} - {self.passenger.username} - {self.status}"

    @property
    def duration_minutes(self):
        """Calculate actual trip duration"""
        if self.pickup_time and self.dropoff_time:
            duration = self.dropoff_time - self.pickup_time
            return duration.total_seconds() / 60
        return None
