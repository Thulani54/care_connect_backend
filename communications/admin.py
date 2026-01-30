from django.contrib import admin
from .models import CommunicationProvider, CommunicationMessage, OTP


@admin.register(CommunicationProvider)
class CommunicationProviderAdmin(admin.ModelAdmin):
    list_display = ['name', 'provider_type', 'is_active', 'created_at']
    list_filter = ['provider_type', 'is_active']
    search_fields = ['name', 'sender_id']
    readonly_fields = ['created_at', 'updated_at']
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'provider_type', 'is_active')
        }),
        ('API Configuration', {
            'fields': ('api_key', 'api_secret', 'api_url', 'sender_id', 'config')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(CommunicationMessage)
class CommunicationMessageAdmin(admin.ModelAdmin):
    list_display = ['recipient', 'message_type', 'status', 'user', 'sent_at', 'created_at']
    list_filter = ['message_type', 'status', 'created_at']
    search_fields = ['recipient', 'subject', 'content', 'user__username', 'user__email']
    readonly_fields = ['created_at', 'updated_at', 'sent_at', 'delivered_at']
    date_hierarchy = 'created_at'
    fieldsets = (
        ('Message Information', {
            'fields': ('user', 'provider', 'message_type', 'recipient')
        }),
        ('Content', {
            'fields': ('subject', 'content')
        }),
        ('Status', {
            'fields': ('status', 'error_message', 'metadata')
        }),
        ('Timestamps', {
            'fields': ('sent_at', 'delivered_at', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user', 'provider')


@admin.register(OTP)
class OTPAdmin(admin.ModelAdmin):
    list_display = ['user', 'phone_number', 'code', 'otp_type', 'is_verified', 'is_used', 'attempts', 'expires_at', 'created_at']
    list_filter = ['otp_type', 'is_verified', 'is_used', 'created_at']
    search_fields = ['user__username', 'user__email', 'phone_number', 'code']
    readonly_fields = ['created_at', 'updated_at', 'verified_at']
    date_hierarchy = 'created_at'
    fieldsets = (
        ('User Information', {
            'fields': ('user', 'phone_number')
        }),
        ('OTP Details', {
            'fields': ('otp_type', 'code', 'expires_at')
        }),
        ('Verification', {
            'fields': ('is_verified', 'is_used', 'attempts', 'max_attempts', 'verified_at')
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('user')
