from rest_framework import serializers
from django.contrib.auth import get_user_model
from drivers.models import Driver, DriverLocation
from bookings.models import Booking
from .models import ElderlyMember, CaregiverRelationship

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    """Serializer for User model"""

    class Meta:
        model = User
        fields = [
            'id', 'username', 'email', 'first_name', 'last_name',
            'phone_number', 'user_type', 'is_phone_verified',
            'profile_picture', 'date_of_birth', 'address',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'username', 'is_phone_verified', 'created_at', 'updated_at']


class UserRegistrationSerializer(serializers.ModelSerializer):
    """Serializer for user registration"""
    password = serializers.CharField(write_only=True, min_length=8)
    password_confirm = serializers.CharField(write_only=True, min_length=8)

    class Meta:
        model = User
        fields = ['username', 'email', 'password', 'password_confirm', 'first_name', 'last_name']

    def validate(self, data):
        if data['password'] != data['password_confirm']:
            raise serializers.ValidationError("Passwords do not match")
        return data

    def create(self, validated_data):
        validated_data.pop('password_confirm')
        user = User.objects.create_user(**validated_data)
        return user


class DriverLocationSerializer(serializers.ModelSerializer):
    """Serializer for Driver Location"""

    class Meta:
        model = DriverLocation
        fields = ['latitude', 'longitude', 'heading', 'speed', 'updated_at']
        read_only_fields = ['updated_at']


class DriverSerializer(serializers.ModelSerializer):
    """Serializer for Driver model"""
    user = UserSerializer(read_only=True)
    location = DriverLocationSerializer(read_only=True)

    class Meta:
        model = Driver
        fields = [
            'id',
            'user',
            'phone_number',
            'license_number',
            'vehicle_registration',
            'vehicle_type',
            'status',
            'rating',
            'total_rides',
            'is_verified',
            'location',
            'created_at'
        ]
        read_only_fields = ['id', 'rating', 'total_rides', 'created_at']


class BookingSerializer(serializers.ModelSerializer):
    """Serializer for Booking model"""
    passenger = UserSerializer(read_only=True)
    driver = DriverSerializer(read_only=True)
    elderly_member = serializers.SerializerMethodField()

    class Meta:
        model = Booking
        fields = [
            'id',
            'passenger',
            'passenger_phone',
            'driver',
            'elderly_member',
            'pickup_latitude',
            'pickup_longitude',
            'pickup_address',
            'dropoff_latitude',
            'dropoff_longitude',
            'dropoff_address',
            'distance_km',
            'estimated_duration_minutes',
            'fare_amount',
            'status',
            'payment_status',
            'booking_time',
            'pickup_time',
            'dropoff_time',
            'special_requirements',
            'passenger_rating',
            'driver_rating',
            'feedback',
        ]
        read_only_fields = ['id', 'passenger', 'booking_time', 'pickup_time', 'dropoff_time']

    def get_elderly_member(self, obj):
        """Return elderly member details if present"""
        if obj.elderly_member:
            return {
                'id': obj.elderly_member.id,
                'name': obj.elderly_member.name,
                'relationship': obj.elderly_member.relationship,
            }
        return None


class BookingCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating bookings"""
    elderly_member = serializers.IntegerField(required=False, write_only=True)

    class Meta:
        model = Booking
        fields = [
            'passenger_phone',
            'pickup_latitude',
            'pickup_longitude',
            'pickup_address',
            'dropoff_latitude',
            'dropoff_longitude',
            'dropoff_address',
            'distance_km',
            'estimated_duration_minutes',
            'fare_amount',
            'special_requirements',
            'elderly_member',
        ]

    def create(self, validated_data):
        elderly_member_id = validated_data.pop('elderly_member', None)
        validated_data['passenger'] = self.context['request'].user

        # If elderly_member ID is provided, fetch and assign it
        if elderly_member_id:
            try:
                elderly_member = ElderlyMember.objects.get(
                    id=elderly_member_id,
                    passenger=self.context['request'].user
                )
                validated_data['elderly_member'] = elderly_member
            except ElderlyMember.DoesNotExist:
                pass  # Silently ignore if not found

        return super().create(validated_data)


class DriverLocationUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating driver location"""

    class Meta:
        model = DriverLocation
        fields = ['latitude', 'longitude', 'heading', 'speed']


class ElderlyMemberSerializer(serializers.ModelSerializer):
    """Serializer for Elderly Member model"""

    class Meta:
        model = ElderlyMember
        fields = [
            'id',
            'passenger',
            'name',
            'relationship',
            'age',
            'phone_number',
            'emergency_contact',
            'medical_conditions',
            'created_at',
            'updated_at'
        ]
        read_only_fields = ['id', 'passenger', 'created_at', 'updated_at']

    def create(self, validated_data):
        validated_data['passenger'] = self.context['request'].user
        return super().create(validated_data)


class CaregiverRelationshipSerializer(serializers.ModelSerializer):
    """Serializer for Caregiver Relationship model"""
    passenger = UserSerializer(read_only=True)
    caregiver = UserSerializer(read_only=True)

    class Meta:
        model = CaregiverRelationship
        fields = [
            'id',
            'passenger',
            'caregiver',
            'relationship_type',
            'can_book_rides',
            'can_view_location',
            'can_receive_notifications',
            'notes',
            'is_active',
            'created_at',
            'updated_at'
        ]
        read_only_fields = ['id', 'passenger', 'created_at', 'updated_at']


class CaregiverRelationshipCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating caregiver relationships"""
    caregiver_phone = serializers.CharField(write_only=True)

    class Meta:
        model = CaregiverRelationship
        fields = [
            'caregiver_phone',
            'relationship_type',
            'can_book_rides',
            'can_view_location',
            'can_receive_notifications',
            'notes',
        ]

    def validate_caregiver_phone(self, value):
        """Validate that caregiver exists and is a caregiver user type"""
        try:
            caregiver = User.objects.get(phone_number=value, user_type='caregiver')
            return caregiver
        except User.DoesNotExist:
            raise serializers.ValidationError(
                "No caregiver found with this phone number. The caregiver must be registered as a caregiver user."
            )

    def create(self, validated_data):
        caregiver = validated_data.pop('caregiver_phone')
        validated_data['passenger'] = self.context['request'].user
        validated_data['caregiver'] = caregiver

        # Check if relationship already exists
        existing = CaregiverRelationship.objects.filter(
            passenger=validated_data['passenger'],
            caregiver=caregiver
        ).first()

        if existing:
            # Update existing relationship
            for key, value in validated_data.items():
                setattr(existing, key, value)
            existing.save()
            return existing

        return super().create(validated_data)
