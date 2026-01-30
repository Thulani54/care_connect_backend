from rest_framework import serializers
from .models import UserSettings, AppContent, FAQ, SupportTicket


class UserSettingsSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserSettings
        fields = [
            'id',
            'push_notifications_enabled',
            'email_notifications_enabled',
            'sms_notifications_enabled',
            'location_enabled',
            'share_ride_status',
            'language',
            'theme',
            'created_at',
            'updated_at',
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


class AppContentSerializer(serializers.ModelSerializer):
    class Meta:
        model = AppContent
        fields = [
            'id',
            'content_type',
            'title',
            'content',
            'version',
            'updated_at',
        ]
        read_only_fields = ['id', 'updated_at']


class FAQSerializer(serializers.ModelSerializer):
    class Meta:
        model = FAQ
        fields = [
            'id',
            'question',
            'answer',
            'category',
            'order',
        ]
        read_only_fields = ['id']


class SupportTicketSerializer(serializers.ModelSerializer):
    user_email = serializers.EmailField(source='user.email', read_only=True)
    user_name = serializers.CharField(source='user.name', read_only=True)

    class Meta:
        model = SupportTicket
        fields = [
            'id',
            'user_email',
            'user_name',
            'subject',
            'description',
            'status',
            'priority',
            'admin_response',
            'resolved_at',
            'created_at',
            'updated_at',
        ]
        read_only_fields = [
            'id',
            'user_email',
            'user_name',
            'status',
            'priority',
            'admin_response',
            'resolved_at',
            'created_at',
            'updated_at',
        ]
