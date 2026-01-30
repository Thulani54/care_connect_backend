from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenObtainPairView
from django.contrib.auth.models import User

from drivers.models import Driver, DriverLocation
from bookings.models import Booking
from .models import ElderlyMember, CaregiverRelationship
from .serializers import (
    UserSerializer,
    UserRegistrationSerializer,
    DriverSerializer,
    DriverLocationSerializer,
    DriverLocationUpdateSerializer,
    BookingSerializer,
    BookingCreateSerializer,
    ElderlyMemberSerializer,
    CaregiverRelationshipSerializer,
    CaregiverRelationshipCreateSerializer,
)


class UserRegistrationView(viewsets.GenericViewSet):
    """User registration endpoint"""
    permission_classes = [permissions.AllowAny]
    serializer_class = UserRegistrationSerializer

    @action(detail=False, methods=['post'])
    def register(self, request):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        user_data = UserSerializer(user).data
        return Response({
            'user': user_data,
            'user_id': str(user.id),  # Return user_id for OTP flow
            'message': 'User registered successfully'
        }, status=status.HTTP_201_CREATED)


class DriverViewSet(viewsets.ModelViewSet):
    """ViewSet for Driver CRUD operations"""
    queryset = Driver.objects.select_related('user', 'location').all()
    serializer_class = DriverSerializer
    permission_classes = [permissions.IsAuthenticated]

    @action(detail=False, methods=['get'])
    def available(self, request):
        """Get all available drivers"""
        drivers = self.queryset.filter(status='available', is_verified=True)
        serializer = self.get_serializer(drivers, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def update_location(self, request, pk=None):
        """Update driver location"""
        driver = self.get_object()
        location, created = DriverLocation.objects.get_or_create(driver=driver)

        serializer = DriverLocationUpdateSerializer(location, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response({
            'message': 'Location updated successfully',
            'location': DriverLocationSerializer(location).data
        })

    @action(detail=True, methods=['patch'])
    def update_status(self, request, pk=None):
        """Update driver status (available/busy/offline)"""
        driver = self.get_object()
        new_status = request.data.get('status')

        if new_status not in ['available', 'busy', 'offline']:
            return Response({
                'error': 'Invalid status'
            }, status=status.HTTP_400_BAD_REQUEST)

        driver.status = new_status
        driver.save()

        return Response({
            'message': 'Status updated successfully',
            'driver': self.get_serializer(driver).data
        })


class BookingViewSet(viewsets.ModelViewSet):
    """ViewSet for Booking CRUD operations"""
    queryset = Booking.objects.select_related('passenger', 'driver', 'driver__user').all()
    permission_classes = [permissions.IsAuthenticated]

    def get_serializer_class(self):
        if self.action == 'create':
            return BookingCreateSerializer
        return BookingSerializer

    def get_queryset(self):
        """Filter bookings based on user role"""
        user = self.request.user

        # If user is a driver, show their assigned bookings
        if hasattr(user, 'driver_profile'):
            return self.queryset.filter(driver=user.driver_profile)

        # Otherwise show bookings for the passenger
        return self.queryset.filter(passenger=user)

    @action(detail=False, methods=['get'])
    def my_bookings(self, request):
        """Get current user's bookings"""
        bookings = self.get_queryset().order_by('-booking_time')
        page = self.paginate_queryset(bookings)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(bookings, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def active(self, request):
        """Get active bookings (pending, confirmed, in_progress)"""
        bookings = self.get_queryset().filter(
            status__in=['pending', 'confirmed', 'in_progress']
        )
        serializer = self.get_serializer(bookings, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def history(self, request):
        """Get ride history (all bookings)"""
        bookings = self.get_queryset().order_by('-booking_time')

        page = self.paginate_queryset(bookings)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(bookings, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['patch'])
    def cancel(self, request, pk=None):
        """Cancel a booking"""
        booking = self.get_object()

        if booking.status not in ['pending', 'confirmed']:
            return Response({
                'error': 'Cannot cancel booking in current status'
            }, status=status.HTTP_400_BAD_REQUEST)

        booking.status = 'cancelled'
        booking.cancellation_reason = request.data.get('reason', '')
        from django.utils import timezone
        booking.cancelled_at = timezone.now()
        booking.save()

        return Response({
            'message': 'Booking cancelled successfully',
            'booking': self.get_serializer(booking).data
        })

    @action(detail=True, methods=['patch'])
    def assign_driver(self, request, pk=None):
        """Assign a driver to a booking"""
        booking = self.get_object()
        driver_id = request.data.get('driver_id')

        try:
            driver = Driver.objects.get(id=driver_id, is_verified=True)
        except Driver.DoesNotExist:
            return Response({
                'error': 'Driver not found or not verified'
            }, status=status.HTTP_404_NOT_FOUND)

        booking.driver = driver
        booking.status = 'confirmed'
        booking.save()

        # Update driver status
        driver.status = 'busy'
        driver.save()

        return Response({
            'message': 'Driver assigned successfully',
            'booking': self.get_serializer(booking).data
        })

    @action(detail=True, methods=['patch'])
    def rate(self, request, pk=None):
        """Rate a completed booking"""
        booking = self.get_object()

        if booking.status != 'completed':
            return Response({
                'error': 'Can only rate completed bookings'
            }, status=status.HTTP_400_BAD_REQUEST)

        user = request.user

        # Passenger rating the driver
        if user == booking.passenger:
            booking.driver_rating = request.data.get('rating')
            booking.feedback = request.data.get('feedback', '')
        # Driver rating the passenger
        elif hasattr(user, 'driver_profile') and user.driver_profile == booking.driver:
            booking.passenger_rating = request.data.get('rating')

        booking.save()

        return Response({
            'message': 'Rating submitted successfully',
            'booking': self.get_serializer(booking).data
        })


class ElderlyMemberViewSet(viewsets.ModelViewSet):
    """ViewSet for Elderly Member CRUD operations"""
    queryset = ElderlyMember.objects.all()
    serializer_class = ElderlyMemberSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        """Filter elderly members by current user"""
        return self.queryset.filter(passenger=self.request.user)


class CaregiverRelationshipViewSet(viewsets.ModelViewSet):
    """ViewSet for Caregiver Relationship CRUD operations"""
    queryset = CaregiverRelationship.objects.select_related('passenger', 'caregiver').all()
    permission_classes = [permissions.IsAuthenticated]

    def get_serializer_class(self):
        if self.action == 'create':
            return CaregiverRelationshipCreateSerializer
        return CaregiverRelationshipSerializer

    def get_queryset(self):
        """Filter caregiver relationships by current user"""
        user = self.request.user

        # If user is a passenger, show their caregivers
        if user.user_type == 'passenger':
            return self.queryset.filter(passenger=user, is_active=True)

        # If user is a caregiver, show their patients
        elif user.user_type == 'caregiver':
            return self.queryset.filter(caregiver=user, is_active=True)

        return self.queryset.none()

    @action(detail=False, methods=['get'])
    def my_caregivers(self, request):
        """Get current passenger's caregivers"""
        if request.user.user_type != 'passenger':
            return Response({
                'error': 'Only passengers can view their caregivers'
            }, status=status.HTTP_403_FORBIDDEN)

        relationships = self.get_queryset().order_by('-created_at')
        serializer = self.get_serializer(relationships, many=True)
        return Response(serializer.data)

    @action(detail=False, methods=['get'])
    def my_patients(self, request):
        """Get current caregiver's patients"""
        if request.user.user_type != 'caregiver':
            return Response({
                'error': 'Only caregivers can view their patients'
            }, status=status.HTTP_403_FORBIDDEN)

        relationships = self.get_queryset().order_by('-created_at')
        serializer = self.get_serializer(relationships, many=True)
        return Response(serializer.data)

    @action(detail=True, methods=['patch'])
    def update_permissions(self, request, pk=None):
        """Update caregiver permissions"""
        relationship = self.get_object()

        # Only passenger can update permissions
        if request.user != relationship.passenger:
            return Response({
                'error': 'Only the passenger can update permissions'
            }, status=status.HTTP_403_FORBIDDEN)

        # Update permissions
        if 'can_book_rides' in request.data:
            relationship.can_book_rides = request.data['can_book_rides']
        if 'can_view_location' in request.data:
            relationship.can_view_location = request.data['can_view_location']
        if 'can_receive_notifications' in request.data:
            relationship.can_receive_notifications = request.data['can_receive_notifications']
        if 'notes' in request.data:
            relationship.notes = request.data['notes']

        relationship.save()

        return Response({
            'message': 'Permissions updated successfully',
            'relationship': self.get_serializer(relationship).data
        })

    @action(detail=True, methods=['delete'])
    def deactivate(self, request, pk=None):
        """Deactivate a caregiver relationship"""
        relationship = self.get_object()

        # Only passenger can deactivate
        if request.user != relationship.passenger:
            return Response({
                'error': 'Only the passenger can deactivate this relationship'
            }, status=status.HTTP_403_FORBIDDEN)

        relationship.is_active = False
        relationship.save()

        return Response({
            'message': 'Caregiver relationship deactivated successfully'
        }, status=status.HTTP_200_OK)
