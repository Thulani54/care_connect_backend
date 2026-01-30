from django.contrib import admin
from .models import UserSettings, AppContent, FAQ, SupportTicket


@admin.register(UserSettings)
class UserSettingsAdmin(admin.ModelAdmin):
    list_display = [
        'user',
        'language',
        'push_notifications_enabled',
        'email_notifications_enabled',
        'sms_notifications_enabled',
        'location_enabled',
        'updated_at',
    ]
    list_filter = [
        'language',
        'push_notifications_enabled',
        'email_notifications_enabled',
        'sms_notifications_enabled',
        'location_enabled',
    ]
    search_fields = ['user__email', 'user__name']
    readonly_fields = ['created_at', 'updated_at']

    fieldsets = (
        ('User', {
            'fields': ('user',)
        }),
        ('Notification Settings', {
            'fields': (
                'push_notifications_enabled',
                'email_notifications_enabled',
                'sms_notifications_enabled',
            )
        }),
        ('Privacy Settings', {
            'fields': (
                'location_enabled',
                'share_ride_status',
            )
        }),
        ('App Settings', {
            'fields': (
                'language',
                'theme',
            )
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(AppContent)
class AppContentAdmin(admin.ModelAdmin):
    list_display = ['content_type', 'title', 'version', 'is_active', 'updated_at']
    list_filter = ['content_type', 'is_active']
    search_fields = ['title', 'content']
    readonly_fields = ['created_at', 'updated_at']

    fieldsets = (
        ('Content Information', {
            'fields': (
                'content_type',
                'title',
                'version',
                'is_active',
            )
        }),
        ('Content', {
            'fields': ('content',),
            'description': 'Supports Markdown formatting'
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )


@admin.register(FAQ)
class FAQAdmin(admin.ModelAdmin):
    list_display = ['question_preview', 'category', 'order', 'is_active', 'updated_at']
    list_filter = ['category', 'is_active']
    search_fields = ['question', 'answer']
    readonly_fields = ['created_at', 'updated_at']
    list_editable = ['order', 'is_active']
    ordering = ['order', 'category']

    fieldsets = (
        ('FAQ Details', {
            'fields': (
                'question',
                'answer',
                'category',
                'order',
                'is_active',
            )
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def question_preview(self, obj):
        return obj.question[:50] + '...' if len(obj.question) > 50 else obj.question
    question_preview.short_description = 'Question'


@admin.register(SupportTicket)
class SupportTicketAdmin(admin.ModelAdmin):
    list_display = [
        'ticket_id',
        'user',
        'subject',
        'status',
        'priority',
        'created_at',
    ]
    list_filter = ['status', 'priority', 'created_at']
    search_fields = ['user__email', 'user__name', 'subject', 'description']
    readonly_fields = ['created_at', 'updated_at']
    list_editable = ['status', 'priority']
    date_hierarchy = 'created_at'

    fieldsets = (
        ('Ticket Information', {
            'fields': (
                'user',
                'subject',
                'description',
                'status',
                'priority',
            )
        }),
        ('Admin Response', {
            'fields': (
                'admin_response',
                'resolved_at',
                'resolved_by',
            )
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

    def ticket_id(self, obj):
        return f"#{obj.id}"
    ticket_id.short_description = 'Ticket ID'

    def save_model(self, request, obj, form, change):
        if obj.status == 'resolved' and not obj.resolved_by:
            obj.resolved_by = request.user
            from django.utils import timezone
            obj.resolved_at = timezone.now()
        super().save_model(request, obj, form, change)
