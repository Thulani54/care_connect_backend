from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


class UserSettings(models.Model):
    """User preferences and settings"""

    LANGUAGE_CHOICES = [
        ('en', 'English'),
        ('af', 'Afrikaans'),
        ('zu', 'Zulu'),
        ('xh', 'Xhosa'),
        ('st', 'Sotho'),
    ]

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name='settings'
    )

    # Notification Settings
    push_notifications_enabled = models.BooleanField(default=True)
    email_notifications_enabled = models.BooleanField(default=False)
    sms_notifications_enabled = models.BooleanField(default=True)

    # Privacy Settings
    location_enabled = models.BooleanField(default=True)
    share_ride_status = models.BooleanField(default=True)

    # App Settings
    language = models.CharField(
        max_length=5,
        choices=LANGUAGE_CHOICES,
        default='en'
    )
    theme = models.CharField(
        max_length=10,
        choices=[('light', 'Light'), ('dark', 'Dark')],
        default='dark'
    )

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'User Setting'
        verbose_name_plural = 'User Settings'

    def __str__(self):
        return f"{self.user.email} - Settings"


class AppContent(models.Model):
    """Store app content like privacy policy, terms of service, etc."""

    CONTENT_TYPE_CHOICES = [
        ('privacy_policy', 'Privacy Policy'),
        ('terms_of_service', 'Terms of Service'),
        ('about', 'About'),
        ('safety_tips', 'Safety Tips'),
        ('user_guide', 'User Guide'),
    ]

    content_type = models.CharField(
        max_length=50,
        choices=CONTENT_TYPE_CHOICES,
        unique=True
    )
    title = models.CharField(max_length=200)
    content = models.TextField()
    version = models.CharField(max_length=20, default='1.0.0')
    is_active = models.BooleanField(default=True)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'App Content'
        verbose_name_plural = 'App Contents'
        ordering = ['content_type']

    def __str__(self):
        return f"{self.get_content_type_display()} - v{self.version}"


class FAQ(models.Model):
    """Frequently Asked Questions"""

    question = models.CharField(max_length=500)
    answer = models.TextField()
    category = models.CharField(
        max_length=50,
        choices=[
            ('general', 'General'),
            ('booking', 'Booking'),
            ('payment', 'Payment'),
            ('elderly', 'Elderly Assistance'),
            ('safety', 'Safety'),
        ],
        default='general'
    )
    order = models.IntegerField(default=0, help_text='Display order')
    is_active = models.BooleanField(default=True)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'FAQ'
        verbose_name_plural = 'FAQs'
        ordering = ['order', 'category']

    def __str__(self):
        return self.question[:50]


class SupportTicket(models.Model):
    """User support tickets"""

    STATUS_CHOICES = [
        ('open', 'Open'),
        ('in_progress', 'In Progress'),
        ('resolved', 'Resolved'),
        ('closed', 'Closed'),
    ]

    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('medium', 'Medium'),
        ('high', 'High'),
        ('urgent', 'Urgent'),
    ]

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='support_tickets'
    )
    subject = models.CharField(max_length=200)
    description = models.TextField()
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='open'
    )
    priority = models.CharField(
        max_length=20,
        choices=PRIORITY_CHOICES,
        default='medium'
    )

    # Admin response
    admin_response = models.TextField(blank=True, null=True)
    resolved_at = models.DateTimeField(blank=True, null=True)
    resolved_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='resolved_tickets'
    )

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = 'Support Ticket'
        verbose_name_plural = 'Support Tickets'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.user.email} - {self.subject}"
