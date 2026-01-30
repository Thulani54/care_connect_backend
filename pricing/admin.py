from django.contrib import admin
from .models import VehicleType, PeakHour, SurgeMultiplier, DistanceTier, PromoCode


@admin.register(VehicleType)
class VehicleTypeAdmin(admin.ModelAdmin):
    """Admin interface for vehicle types"""

    list_display = [
        'display_name',
        'name',
        'base_fare',
        'per_km_rate',
        'per_minute_rate',
        'minimum_fare',
        'capacity',
        'is_elderly_assisted',
        'is_active',
        'priority'
    ]

    list_filter = ['is_active', 'is_elderly_assisted', 'priority']
    search_fields = ['name', 'display_name', 'description']

    ordering = ['-priority', 'name']

    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'display_name', 'description', 'icon')
        }),
        ('Pricing', {
            'fields': ('base_fare', 'per_km_rate', 'per_minute_rate', 'minimum_fare')
        }),
        ('Features', {
            'fields': ('capacity', 'is_elderly_assisted', 'is_active', 'priority')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    readonly_fields = ['created_at', 'updated_at']


@admin.register(PeakHour)
class PeakHourAdmin(admin.ModelAdmin):
    """Admin interface for peak hour pricing"""

    list_display = [
        'name',
        'get_day_display',
        'start_time',
        'end_time',
        'multiplier',
        'is_active'
    ]

    list_filter = ['is_active', 'day_of_week', 'multiplier']
    search_fields = ['name']

    ordering = ['day_of_week', 'start_time']

    fieldsets = (
        ('Peak Hour Details', {
            'fields': ('name', 'day_of_week', 'start_time', 'end_time')
        }),
        ('Pricing', {
            'fields': ('multiplier',)
        }),
        ('Status', {
            'fields': ('is_active',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    readonly_fields = ['created_at', 'updated_at']

    def get_day_display(self, obj):
        if obj.day_of_week is None:
            return 'All days'
        return dict(obj.DAYS_OF_WEEK).get(obj.day_of_week, 'Unknown')
    get_day_display.short_description = 'Day of Week'


@admin.register(SurgeMultiplier)
class SurgeMultiplierAdmin(admin.ModelAdmin):
    """Admin interface for surge pricing"""

    list_display = [
        'name',
        'area_name',
        'multiplier',
        'start_time',
        'end_time',
        'is_active'
    ]

    list_filter = ['is_active', 'multiplier']
    search_fields = ['name', 'area_name']

    ordering = ['-created_at']

    fieldsets = (
        ('Surge Details', {
            'fields': ('name', 'area_name', 'multiplier')
        }),
        ('Geographic Area (Optional)', {
            'fields': ('min_latitude', 'max_latitude', 'min_longitude', 'max_longitude'),
            'classes': ('collapse',)
        }),
        ('Time Period (Optional)', {
            'fields': ('start_time', 'end_time'),
            'classes': ('collapse',)
        }),
        ('Status', {
            'fields': ('is_active',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    readonly_fields = ['created_at', 'updated_at']


@admin.register(DistanceTier)
class DistanceTierAdmin(admin.ModelAdmin):
    """Admin interface for distance-based pricing tiers"""

    list_display = [
        'vehicle_type',
        'min_distance_km',
        'max_distance_km',
        'per_km_rate'
    ]

    list_filter = ['vehicle_type']
    search_fields = ['vehicle_type__name']

    ordering = ['vehicle_type', 'min_distance_km']

    fieldsets = (
        ('Tier Details', {
            'fields': ('vehicle_type', 'min_distance_km', 'max_distance_km', 'per_km_rate')
        }),
    )


@admin.register(PromoCode)
class PromoCodeAdmin(admin.ModelAdmin):
    """Admin interface for promotional codes"""

    list_display = [
        'code',
        'discount_type',
        'discount_value',
        'max_discount',
        'uses_count',
        'max_uses',
        'valid_from',
        'valid_until',
        'is_active'
    ]

    list_filter = ['is_active', 'discount_type', 'valid_from', 'valid_until']
    search_fields = ['code', 'description']

    ordering = ['-created_at']

    fieldsets = (
        ('Code Information', {
            'fields': ('code', 'description')
        }),
        ('Discount Details', {
            'fields': ('discount_type', 'discount_value', 'max_discount', 'min_fare')
        }),
        ('Usage Limits', {
            'fields': ('max_uses', 'uses_count')
        }),
        ('Validity Period', {
            'fields': ('valid_from', 'valid_until')
        }),
        ('Status', {
            'fields': ('is_active',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    readonly_fields = ['uses_count', 'created_at', 'updated_at']

    def save_model(self, request, obj, form, change):
        """Prevent manual modification of uses_count"""
        if change and 'uses_count' in form.changed_data:
            # Revert uses_count to original value
            original = PromoCode.objects.get(pk=obj.pk)
            obj.uses_count = original.uses_count
        super().save_model(request, obj, form, change)
