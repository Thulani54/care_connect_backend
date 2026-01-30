from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from django.conf import settings
from django.db import transaction
import requests
import json
import uuid

from .models import PaymentMethod, Wallet, WalletTransaction
from .serializers import PaymentMethodSerializer, WalletSerializer, WalletTransactionSerializer


class PaymentMethodViewSet(viewsets.ModelViewSet):
    """ViewSet for Payment Method CRUD operations"""
    queryset = PaymentMethod.objects.all()
    serializer_class = PaymentMethodSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """Filter payment methods by current user"""
        return self.queryset.filter(passenger=self.request.user)

    @action(detail=False, methods=['post'])
    def initialize_payment(self, request):
        """Initialize Paystack payment for adding a card"""
        try:
            email = request.user.email
            amount = 5000  # R50 authorization charge (in cents)

            # Paystack API endpoint
            url = 'https://api.paystack.co/transaction/initialize'
            headers = {
                'Authorization': f'Bearer {settings.PAYSTACK_SECRET_KEY}',
                'Content-Type': 'application/json'
            }
            data = {
                'email': email,
                'amount': amount,
                'currency': 'ZAR',
                'callback_url': request.data.get('callback_url', ''),
                'metadata': {
                    'custom_fields': [
                        {
                            'display_name': 'User ID',
                            'variable_name': 'user_id',
                            'value': str(request.user.id)
                        }
                    ]
                }
            }

            response = requests.post(url, headers=headers, json=data)
            response_data = response.json()

            if response.status_code == 200 and response_data.get('status'):
                return Response({
                    'authorization_url': response_data['data']['authorization_url'],
                    'access_code': response_data['data']['access_code'],
                    'reference': response_data['data']['reference']
                })
            else:
                return Response({
                    'error': 'Failed to initialize payment',
                    'details': response_data
                }, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            return Response({
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['post'])
    def verify_payment(self, request):
        """Verify Paystack payment and save card"""
        try:
            reference = request.data.get('reference')
            if not reference:
                return Response({
                    'error': 'Reference is required'
                }, status=status.HTTP_400_BAD_REQUEST)

            # Verify transaction with Paystack
            url = f'https://api.paystack.co/transaction/verify/{reference}'
            headers = {
                'Authorization': f'Bearer {settings.PAYSTACK_SECRET_KEY}',
            }

            response = requests.get(url, headers=headers)
            response_data = response.json()

            if response.status_code == 200 and response_data.get('status'):
                data = response_data['data']
                authorization = data.get('authorization', {})

                # Check if transaction was successful
                if data.get('status') == 'success':
                    # Create payment method
                    payment_method = PaymentMethod.objects.create(
                        passenger=request.user,
                        card_last4=authorization.get('last4', ''),
                        card_brand=authorization.get('brand', ''),
                        card_exp_month=int(authorization.get('exp_month', 0)),
                        card_exp_year=int(authorization.get('exp_year', 0)),
                        paystack_authorization_code=authorization.get('authorization_code', ''),
                        is_default=not PaymentMethod.objects.filter(
                            passenger=request.user
                        ).exists()  # Set as default if it's the first card
                    )

                    serializer = self.get_serializer(payment_method)
                    return Response({
                        'message': 'Payment method added successfully',
                        'payment_method': serializer.data
                    }, status=status.HTTP_201_CREATED)
                else:
                    return Response({
                        'error': 'Transaction was not successful',
                        'status': data.get('status')
                    }, status=status.HTTP_400_BAD_REQUEST)
            else:
                return Response({
                    'error': 'Failed to verify payment',
                    'details': response_data
                }, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            return Response({
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=True, methods=['patch'])
    def set_default(self, request, pk=None):
        """Set a payment method as default"""
        payment_method = self.get_object()
        payment_method.is_default = True
        payment_method.save()

        return Response({
            'message': 'Payment method set as default',
            'payment_method': self.get_serializer(payment_method).data
        })


class WalletViewSet(viewsets.ModelViewSet):
    """ViewSet for Wallet operations"""
    queryset = Wallet.objects.all()
    serializer_class = WalletSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """Filter wallet by current user"""
        return self.queryset.filter(user=self.request.user)

    @action(detail=False, methods=['get'])
    def my_wallet(self, request):
        """Get or create wallet for current user"""
        wallet, created = Wallet.objects.get_or_create(user=request.user)
        serializer = self.get_serializer(wallet)
        return Response(serializer.data)

    @action(detail=False, methods=['post'])
    def topup(self, request):
        """Initialize Paystack payment for wallet top-up"""
        try:
            amount = request.data.get('amount')
            if not amount:
                return Response({
                    'error': 'Amount is required'
                }, status=status.HTTP_400_BAD_REQUEST)

            # Convert to cents for Paystack (ZAR)
            amount_in_cents = int(float(amount) * 100)

            if amount_in_cents < 100:  # Minimum R1.00
                return Response({
                    'error': 'Minimum top-up amount is R1.00'
                }, status=status.HTTP_400_BAD_REQUEST)

            # Get or create wallet
            wallet, created = Wallet.objects.get_or_create(user=request.user)

            # Generate unique reference
            reference = f"topup_{uuid.uuid4().hex[:12]}"

            # Create pending transaction
            wallet_transaction = WalletTransaction.objects.create(
                wallet=wallet,
                transaction_type='topup',
                amount=amount,
                status='pending',
                reference=reference,
                description=f'Wallet top-up of R{amount}',
                metadata={'user_id': str(request.user.id)}
            )

            # Initialize Paystack payment
            url = 'https://api.paystack.co/transaction/initialize'
            headers = {
                'Authorization': f'Bearer {settings.PAYSTACK_SECRET_KEY}',
                'Content-Type': 'application/json'
            }
            data = {
                'email': request.user.email,
                'amount': amount_in_cents,
                'currency': 'ZAR',
                'reference': reference,
                'callback_url': request.data.get('callback_url', ''),
                'metadata': {
                    'custom_fields': [
                        {
                            'display_name': 'User ID',
                            'variable_name': 'user_id',
                            'value': str(request.user.id)
                        },
                        {
                            'display_name': 'Transaction Type',
                            'variable_name': 'transaction_type',
                            'value': 'wallet_topup'
                        }
                    ]
                }
            }

            response = requests.post(url, headers=headers, json=data)
            response_data = response.json()

            if response.status_code == 200 and response_data.get('status'):
                return Response({
                    'authorization_url': response_data['data']['authorization_url'],
                    'access_code': response_data['data']['access_code'],
                    'reference': reference,
                    'transaction_id': wallet_transaction.id
                })
            else:
                # Mark transaction as failed
                wallet_transaction.status = 'failed'
                wallet_transaction.save()
                return Response({
                    'error': 'Failed to initialize payment',
                    'details': response_data
                }, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            return Response({
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['post'])
    def verify_topup(self, request):
        """Verify Paystack payment and credit wallet"""
        try:
            reference = request.data.get('reference')
            if not reference:
                return Response({
                    'error': 'Reference is required'
                }, status=status.HTTP_400_BAD_REQUEST)

            # Get transaction
            try:
                wallet_transaction = WalletTransaction.objects.get(reference=reference)
            except WalletTransaction.DoesNotExist:
                return Response({
                    'error': 'Transaction not found'
                }, status=status.HTTP_404_NOT_FOUND)

            # Check if already processed
            if wallet_transaction.status == 'completed':
                return Response({
                    'message': 'Transaction already completed',
                    'transaction': WalletTransactionSerializer(wallet_transaction).data
                })

            # Verify with Paystack
            url = f'https://api.paystack.co/transaction/verify/{reference}'
            headers = {
                'Authorization': f'Bearer {settings.PAYSTACK_SECRET_KEY}',
            }

            response = requests.get(url, headers=headers)
            response_data = response.json()

            if response.status_code == 200 and response_data.get('status'):
                data = response_data['data']

                if data.get('status') == 'success':
                    # Use atomic transaction to ensure consistency
                    with transaction.atomic():
                        # Credit wallet
                        wallet = wallet_transaction.wallet
                        wallet.credit(wallet_transaction.amount)

                        # Update transaction status
                        wallet_transaction.status = 'completed'
                        wallet_transaction.metadata = {
                            **wallet_transaction.metadata,
                            'paystack_response': data
                        }
                        wallet_transaction.save()

                    return Response({
                        'message': 'Wallet topped up successfully',
                        'transaction': WalletTransactionSerializer(wallet_transaction).data,
                        'wallet': WalletSerializer(wallet).data
                    })
                else:
                    # Mark as failed
                    wallet_transaction.status = 'failed'
                    wallet_transaction.save()
                    return Response({
                        'error': 'Transaction was not successful',
                        'status': data.get('status')
                    }, status=status.HTTP_400_BAD_REQUEST)
            else:
                wallet_transaction.status = 'failed'
                wallet_transaction.save()
                return Response({
                    'error': 'Failed to verify payment',
                    'details': response_data
                }, status=status.HTTP_400_BAD_REQUEST)

        except Exception as e:
            return Response({
                'error': str(e)
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    @action(detail=False, methods=['get'])
    def transactions(self, request):
        """Get wallet transaction history"""
        try:
            wallet = Wallet.objects.get(user=request.user)
            transactions = WalletTransaction.objects.filter(wallet=wallet).order_by('-created_at')

            # Optional filtering by transaction type
            transaction_type = request.query_params.get('type')
            if transaction_type:
                transactions = transactions.filter(transaction_type=transaction_type)

            # Optional filtering by status
            status_filter = request.query_params.get('status')
            if status_filter:
                transactions = transactions.filter(status=status_filter)

            serializer = WalletTransactionSerializer(transactions, many=True)
            return Response(serializer.data)
        except Wallet.DoesNotExist:
            # Return empty list if wallet doesn't exist yet
            return Response([])
