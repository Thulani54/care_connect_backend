from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator


class VehicleType(models.Model):
    """Different vehicle types with their pricing"""

    name = models.CharField(max_length=50, unique=True)  # e.g., Standard, Premium, Luxury
    display_name = models.CharField(max_length=100)  # e.g., "Care Connect Go", "Care Connect Premium"
    description = models.TextField()
    icon = models.CharField(max_length=50, default='car')  # Icon identifier
    capacity = models.IntegerField(default=4)
    base_fare = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )
    per_km_rate = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )
    per_minute_rate = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        default=0.00
    )
    minimum_fare = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )

    # Features
    is_elderly_assisted = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    priority = models.IntegerField(default=0, help_text='Display order (higher = first)')

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-priority', 'name']
        verbose_name = 'Vehicle Type'
        verbose_name_plural = 'Vehicle Types'

    def __str__(self):
        return self.display_name


class PeakHour(models.Model):
    """Define peak hour periods for surge pricing"""

    DAYS_OF_WEEK = [
        (0, 'Monday'),
        (1, 'Tuesday'),
        (2, 'Wednesday'),
        (3, 'Thursday'),
        (4, 'Friday'),
        (5, 'Saturday'),
        (6, 'Sunday'),
    ]

    name = models.CharField(max_length=100)  # e.g., "Morning Rush", "Evening Rush"
    day_of_week = models.IntegerField(
        choices=DAYS_OF_WEEK,
        null=True,
        blank=True,
        help_text='Leave blank for all days'
    )
    start_time = models.TimeField()
    end_time = models.TimeField()
    multiplier = models.DecimalField(
        max_digits=4,
        decimal_places=2,
        validators=[MinValueValidator(1.0), MaxValueValidator(5.0)],
        help_text='Price multiplier (e.g., 1.5 = 50% increase)'
    )
    is_active = models.BooleanField(default=True)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['start_time']
        verbose_name = 'Peak Hour'
        verbose_name_plural = 'Peak Hours'

    def __str__(self):
        day_str = dict(self.DAYS_OF_WEEK).get(self.day_of_week, 'All days')
        return f"{self.name} ({day_str}: {self.start_time.strftime('%H:%M')} - {self.end_time.strftime('%H:%M')})"


class SurgeMultiplier(models.Model):
    """Dynamic surge pricing based on demand"""

    name = models.CharField(max_length=100)
    area_name = models.CharField(max_length=200, blank=True, help_text='Specific area name')

    # Geographic area (bounding box)
    min_latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    max_latitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    min_longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)
    max_longitude = models.DecimalField(max_digits=9, decimal_places=6, null=True, blank=True)

    multiplier = models.DecimalField(
        max_digits=4,
        decimal_places=2,
        validators=[MinValueValidator(1.0), MaxValueValidator(5.0)]
    )

    start_time = models.DateTimeField(null=True, blank=True)
    end_time = models.DateTimeField(null=True, blank=True)

    is_active = models.BooleanField(default=True)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Surge Multiplier'
        verbose_name_plural = 'Surge Multipliers'

    def __str__(self):
        return f"{self.name} (x{self.multiplier})"


class DistanceTier(models.Model):
    """Different pricing tiers based on distance"""

    vehicle_type = models.ForeignKey(
        VehicleType,
        on_delete=models.CASCADE,
        related_name='distance_tiers'
    )
    min_distance_km = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )
    max_distance_km = models.DecimalField(
        max_digits=6,
        decimal_places=2,
        validators=[MinValueValidator(0)],
        null=True,
        blank=True,
        help_text='Leave blank for unlimited'
    )
    per_km_rate = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )

    class Meta:
        ordering = ['vehicle_type', 'min_distance_km']
        verbose_name = 'Distance Tier'
        verbose_name_plural = 'Distance Tiers'
        unique_together = ['vehicle_type', 'min_distance_km']

    def __str__(self):
        max_dist = f"{self.max_distance_km}km" if self.max_distance_km else "unlimited"
        return f"{self.vehicle_type.name}: {self.min_distance_km}km - {max_dist} @ R{self.per_km_rate}/km"


class PromoCode(models.Model):
    """Promotional discount codes"""

    DISCOUNT_TYPE_CHOICES = [
        ('percentage', 'Percentage'),
        ('fixed', 'Fixed Amount'),
    ]

    code = models.CharField(max_length=50, unique=True)
    description = models.TextField()

    discount_type = models.CharField(max_length=20, choices=DISCOUNT_TYPE_CHOICES)
    discount_value = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        validators=[MinValueValidator(0)]
    )
    max_discount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        help_text='Maximum discount amount (for percentage type)'
    )

    min_fare = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        default=0,
        help_text='Minimum fare required to use this code'
    )

    max_uses = models.IntegerField(null=True, blank=True, help_text='Leave blank for unlimited')
    uses_count = models.IntegerField(default=0)

    valid_from = models.DateTimeField()
    valid_until = models.DateTimeField()

    is_active = models.BooleanField(default=True)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']
        verbose_name = 'Promo Code'
        verbose_name_plural = 'Promo Codes'

    def __str__(self):
        return f"{self.code} ({self.discount_type})"

    def is_valid(self):
        from django.utils import timezone
        now = timezone.now()

        if not self.is_active:
            return False, "Promo code is inactive"

        if now < self.valid_from:
            return False, "Promo code not yet valid"

        if now > self.valid_until:
            return False, "Promo code has expired"

        if self.max_uses and self.uses_count >= self.max_uses:
            return False, "Promo code has reached maximum uses"

        return True, "Valid"
