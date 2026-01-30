from django.db import models
from django.conf import settings


class Driver(models.Model):
    """Driver model for Care Connect Mobility"""

    STATUS_CHOICES = [
        ('available', 'Available'),
        ('busy', 'Busy'),
        ('offline', 'Offline'),
    ]

    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='driver_profile')
    phone_number = models.CharField(max_length=15)
    license_number = models.CharField(max_length=50, unique=True)
    vehicle_registration = models.CharField(max_length=20)
    vehicle_type = models.CharField(max_length=50, default='sedan')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='offline')
    rating = models.DecimalField(max_digits=3, decimal_places=2, default=0.00)
    total_rides = models.IntegerField(default=0)
    is_verified = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.get_full_name()} - {self.license_number}"


class DriverLocation(models.Model):
    """Real-time driver location for Firebase Realtime Database sync"""

    driver = models.OneToOneField(Driver, on_delete=models.CASCADE, related_name='location')
    latitude = models.DecimalField(max_digits=9, decimal_places=6)
    longitude = models.DecimalField(max_digits=9, decimal_places=6)
    heading = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    speed = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = "Driver Locations"

    def __str__(self):
        return f"{self.driver.user.get_full_name()} - ({self.latitude}, {self.longitude})"
