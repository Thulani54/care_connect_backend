from django.contrib import admin
from .models import Booking


@admin.register(Booking)
class BookingAdmin(admin.ModelAdmin):
    list_display = [
        'id',
        'passenger',
        'driver',
        'status',
        'payment_status',
        'fare_amount',
        'booking_time'
    ]
    list_filter = ['status', 'payment_status', 'booking_time']
    search_fields = [
        'passenger__username',
        'passenger__email',
        'driver__user__username',
        'pickup_address',
        'dropoff_address'
    ]
    readonly_fields = ['booking_time', 'pickup_time', 'dropoff_time', 'cancelled_at']

    fieldsets = (
        ('Passenger Information', {
            'fields': ('passenger', 'passenger_phone')
        }),
        ('Driver Assignment', {
            'fields': ('driver',)
        }),
        ('Pickup Location', {
            'fields': ('pickup_latitude', 'pickup_longitude', 'pickup_address')
        }),
        ('Dropoff Location', {
            'fields': ('dropoff_latitude', 'dropoff_longitude', 'dropoff_address')
        }),
        ('Trip Details', {
            'fields': ('distance_km', 'estimated_duration_minutes', 'fare_amount')
        }),
        ('Status', {
            'fields': ('status', 'payment_status')
        }),
        ('Timestamps', {
            'fields': ('booking_time', 'pickup_time', 'dropoff_time', 'cancelled_at'),
            'classes': ('collapse',)
        }),
        ('Additional Information', {
            'fields': ('special_requirements', 'cancellation_reason'),
            'classes': ('collapse',)
        }),
        ('Ratings & Feedback', {
            'fields': ('passenger_rating', 'driver_rating', 'feedback'),
            'classes': ('collapse',)
        }),
    )

    def get_queryset(self, request):
        """Optimize queryset with select_related"""
        qs = super().get_queryset(request)
        return qs.select_related('passenger', 'driver', 'driver__user')
