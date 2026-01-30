from django.db import models
from django.conf import settings
from decimal import Decimal


class PaymentMethod(models.Model):
    """Model for storing payment methods"""
    passenger = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='payment_methods'
    )
    card_last4 = models.CharField(max_length=4)
    card_brand = models.CharField(max_length=50)  # Visa, Mastercard, etc.
    card_exp_month = models.IntegerField()
    card_exp_year = models.IntegerField()
    is_default = models.BooleanField(default=False)
    paystack_authorization_code = models.CharField(max_length=255, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-is_default', '-created_at']

    def __str__(self):
        return f"{self.card_brand} ending in {self.card_last4}"

    def save(self, *args, **kwargs):
        # If this is set as default, unset all other defaults for this user
        if self.is_default:
            PaymentMethod.objects.filter(
                passenger=self.passenger,
                is_default=True
            ).exclude(pk=self.pk).update(is_default=False)
        super().save(*args, **kwargs)


class Wallet(models.Model):
    """Model for user wallet"""
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='wallet'
    )
    balance = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.user.phone_number}'s Wallet - R{self.balance}"

    def credit(self, amount):
        """Add money to wallet"""
        self.balance += Decimal(str(amount))
        self.save()

    def debit(self, amount):
        """Deduct money from wallet"""
        if self.balance >= Decimal(str(amount)):
            self.balance -= Decimal(str(amount))
            self.save()
            return True
        return False


class WalletTransaction(models.Model):
    """Model for wallet transaction history"""
    TRANSACTION_TYPES = (
        ('topup', 'Top Up'),
        ('payment', 'Payment'),
        ('refund', 'Refund'),
        ('withdrawal', 'Withdrawal'),
    )

    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('completed', 'Completed'),
        ('failed', 'Failed'),
        ('cancelled', 'Cancelled'),
    )

    wallet = models.ForeignKey(
        Wallet,
        on_delete=models.CASCADE,
        related_name='transactions'
    )
    transaction_type = models.CharField(max_length=20, choices=TRANSACTION_TYPES)
    amount = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    reference = models.CharField(max_length=255, unique=True)
    description = models.TextField(blank=True)
    metadata = models.JSONField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.transaction_type} - R{self.amount} ({self.status})"
