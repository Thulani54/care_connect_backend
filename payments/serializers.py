from rest_framework import serializers
from .models import PaymentMethod, Wallet, WalletTransaction


class PaymentMethodSerializer(serializers.ModelSerializer):
    """Serializer for Payment Method model"""

    class Meta:
        model = PaymentMethod
        fields = [
            'id',
            'passenger',
            'card_last4',
            'card_brand',
            'card_exp_month',
            'card_exp_year',
            'is_default',
            'paystack_authorization_code',
            'created_at',
            'updated_at'
        ]
        read_only_fields = ['id', 'passenger', 'created_at', 'updated_at']

    def create(self, validated_data):
        validated_data['passenger'] = self.context['request'].user
        return super().create(validated_data)


class WalletSerializer(serializers.ModelSerializer):
    """Serializer for Wallet model"""

    class Meta:
        model = Wallet
        fields = [
            'id',
            'user',
            'balance',
            'created_at',
            'updated_at'
        ]
        read_only_fields = ['id', 'user', 'created_at', 'updated_at']


class WalletTransactionSerializer(serializers.ModelSerializer):
    """Serializer for Wallet Transaction model"""

    class Meta:
        model = WalletTransaction
        fields = [
            'id',
            'wallet',
            'transaction_type',
            'amount',
            'status',
            'reference',
            'description',
            'metadata',
            'created_at',
            'updated_at'
        ]
        read_only_fields = ['id', 'wallet', 'created_at', 'updated_at']
