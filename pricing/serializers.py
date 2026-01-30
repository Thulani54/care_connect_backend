from rest_framework import serializers
from .models import VehicleType, PeakHour, SurgeMultiplier, DistanceTier, PromoCode


class VehicleTypeSerializer(serializers.ModelSerializer):
    """Serializer for vehicle types"""

    class Meta:
        model = VehicleType
        fields = [
            'id',
            'name',
            'display_name',
            'description',
            'icon',
            'capacity',
            'base_fare',
            'per_km_rate',
            'per_minute_rate',
            'minimum_fare',
            'is_elderly_assisted',
            'is_active',
            'priority'
        ]
        read_only_fields = ['id']


class PeakHourSerializer(serializers.ModelSerializer):
    """Serializer for peak hour pricing"""

    day_of_week_display = serializers.SerializerMethodField()

    class Meta:
        model = PeakHour
        fields = [
            'id',
            'name',
            'day_of_week',
            'day_of_week_display',
            'start_time',
            'end_time',
            'multiplier',
            'is_active'
        ]
        read_only_fields = ['id']

    def get_day_of_week_display(self, obj):
        if obj.day_of_week is None:
            return 'All days'
        return dict(obj.DAYS_OF_WEEK).get(obj.day_of_week, 'Unknown')


class SurgeMultiplierSerializer(serializers.ModelSerializer):
    """Serializer for surge pricing"""

    class Meta:
        model = SurgeMultiplier
        fields = [
            'id',
            'name',
            'area_name',
            'min_latitude',
            'max_latitude',
            'min_longitude',
            'max_longitude',
            'multiplier',
            'start_time',
            'end_time',
            'is_active'
        ]
        read_only_fields = ['id']


class DistanceTierSerializer(serializers.ModelSerializer):
    """Serializer for distance tiers"""

    vehicle_type_name = serializers.CharField(source='vehicle_type.name', read_only=True)

    class Meta:
        model = DistanceTier
        fields = [
            'id',
            'vehicle_type',
            'vehicle_type_name',
            'min_distance_km',
            'max_distance_km',
            'per_km_rate'
        ]
        read_only_fields = ['id', 'vehicle_type_name']


class PromoCodeSerializer(serializers.ModelSerializer):
    """Serializer for promo codes"""

    is_valid = serializers.SerializerMethodField()

    class Meta:
        model = PromoCode
        fields = [
            'id',
            'code',
            'description',
            'discount_type',
            'discount_value',
            'max_discount',
            'min_fare',
            'max_uses',
            'uses_count',
            'valid_from',
            'valid_until',
            'is_active',
            'is_valid'
        ]
        read_only_fields = ['id', 'uses_count', 'is_valid']

    def get_is_valid(self, obj):
        is_valid, message = obj.is_valid()
        return {'valid': is_valid, 'message': message}


class FareCalculationSerializer(serializers.Serializer):
    """Serializer for fare calculation request"""

    pickup_latitude = serializers.DecimalField(max_digits=9, decimal_places=6)
    pickup_longitude = serializers.DecimalField(max_digits=9, decimal_places=6)
    dropoff_latitude = serializers.DecimalField(max_digits=9, decimal_places=6)
    dropoff_longitude = serializers.DecimalField(max_digits=9, decimal_places=6)
    vehicle_type_id = serializers.IntegerField(required=False)
    promo_code = serializers.CharField(max_length=50, required=False, allow_blank=True)
    request_time = serializers.DateTimeField(required=False)


class FareBreakdownSerializer(serializers.Serializer):
    """Serializer for fare calculation response"""

    vehicle_type = VehicleTypeSerializer()
    distance_km = serializers.DecimalField(max_digits=10, decimal_places=2)
    estimated_duration_minutes = serializers.IntegerField()
    base_fare = serializers.DecimalField(max_digits=10, decimal_places=2)
    distance_fare = serializers.DecimalField(max_digits=10, decimal_places=2)
    time_fare = serializers.DecimalField(max_digits=10, decimal_places=2)
    subtotal = serializers.DecimalField(max_digits=10, decimal_places=2)
    peak_hour_multiplier = serializers.DecimalField(max_digits=4, decimal_places=2)
    surge_multiplier = serializers.DecimalField(max_digits=4, decimal_places=2)
    total_before_discount = serializers.DecimalField(max_digits=10, decimal_places=2)
    discount_amount = serializers.DecimalField(max_digits=10, decimal_places=2)
    final_fare = serializers.DecimalField(max_digits=10, decimal_places=2)
    promo_code = serializers.CharField(required=False, allow_null=True)
    peak_hour_name = serializers.CharField(required=False, allow_null=True)
    surge_area_name = serializers.CharField(required=False, allow_null=True)
