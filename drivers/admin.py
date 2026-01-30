from django.contrib import admin
from .models import Driver, DriverLocation


@admin.register(Driver)
class DriverAdmin(admin.ModelAdmin):
    list_display = ['user', 'license_number', 'vehicle_registration', 'status', 'rating', 'total_rides', 'is_verified']
    list_filter = ['status', 'is_verified', 'created_at']
    search_fields = ['user__username', 'user__email', 'license_number', 'vehicle_registration', 'phone_number']
    readonly_fields = ['created_at', 'updated_at']
    fieldsets = (
        ('User Information', {
            'fields': ('user', 'phone_number')
        }),
        ('Vehicle Information', {
            'fields': ('license_number', 'vehicle_registration', 'vehicle_type')
        }),
        ('Status & Metrics', {
            'fields': ('status', 'is_verified', 'rating', 'total_rides')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(DriverLocation)
class DriverLocationAdmin(admin.ModelAdmin):
    list_display = ['driver', 'latitude', 'longitude', 'speed', 'updated_at']
    search_fields = ['driver__user__username', 'driver__license_number']
    readonly_fields = ['updated_at']
    list_filter = ['updated_at']
