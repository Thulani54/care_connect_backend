from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework import status
from django.utils import timezone
from decimal import Decimal
import math
from datetime import datetime

from .models import VehicleType, PeakHour, SurgeMultiplier, DistanceTier, PromoCode
from .serializers import (
    VehicleTypeSerializer,
    PeakHourSerializer,
    FareCalculationSerializer,
    FareBreakdownSerializer
)


def calculate_distance(lat1, lon1, lat2, lon2):
    """Calculate distance between two points using Haversine formula"""
    # Convert to radians
    lat1_rad = math.radians(float(lat1))
    lat2_rad = math.radians(float(lat2))
    lon1_rad = math.radians(float(lon1))
    lon2_rad = math.radians(float(lon2))

    # Haversine formula
    dlon = lon2_rad - lon1_rad
    dlat = lat2_rad - lat1_rad
    a = math.sin(dlat / 2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon / 2)**2
    c = 2 * math.asin(math.sqrt(a))

    # Radius of earth in kilometers
    r = 6371
    return c * r


def get_peak_hour_multiplier(request_time):
    """Get peak hour multiplier for given time"""
    from django.db.models import Q

    day_of_week = request_time.weekday()  # Monday = 0, Sunday = 6
    current_time = request_time.time()

    # Check for peak hours (specific day or all days)
    peak_hours = PeakHour.objects.filter(
        is_active=True,
        start_time__lte=current_time,
        end_time__gte=current_time
    ).filter(
        Q(day_of_week=day_of_week) | Q(day_of_week__isnull=True)
    ).order_by('-multiplier').first()

    if peak_hours:
        return peak_hours.multiplier, peak_hours.name
    return Decimal('1.0'), None


def get_surge_multiplier(pickup_lat, pickup_lon, dropoff_lat, dropoff_lon, request_time):
    """Get surge multiplier for given location and time"""
    from django.db.models import Q

    # Check for active surge pricing
    surge_multipliers = SurgeMultiplier.objects.filter(
        is_active=True
    )

    # Filter by time if specified
    surge_multipliers = surge_multipliers.filter(
        Q(start_time__isnull=True) | Q(start_time__lte=request_time),
        Q(end_time__isnull=True) | Q(end_time__gte=request_time)
    )

    best_surge = None
    best_multiplier = Decimal('1.0')

    for surge in surge_multipliers:
        # Check if location is within surge area
        if surge.min_latitude and surge.max_latitude and surge.min_longitude and surge.max_longitude:
            pickup_in_area = (
                surge.min_latitude <= Decimal(str(pickup_lat)) <= surge.max_latitude and
                surge.min_longitude <= Decimal(str(pickup_lon)) <= surge.max_longitude
            )
            dropoff_in_area = (
                surge.min_latitude <= Decimal(str(dropoff_lat)) <= surge.max_latitude and
                surge.min_longitude <= Decimal(str(dropoff_lon)) <= surge.max_longitude
            )

            if pickup_in_area or dropoff_in_area:
                if surge.multiplier > best_multiplier:
                    best_multiplier = surge.multiplier
                    best_surge = surge.name
        else:
            # No geographic restriction, apply globally
            if surge.multiplier > best_multiplier:
                best_multiplier = surge.multiplier
                best_surge = surge.name

    return best_multiplier, best_surge


def get_distance_tier_rate(vehicle_type, distance_km):
    """Get per km rate based on distance tier"""
    from django.db.models import Q

    tier = DistanceTier.objects.filter(
        vehicle_type=vehicle_type,
        min_distance_km__lte=distance_km
    ).filter(
        Q(max_distance_km__gte=distance_km) | Q(max_distance_km__isnull=True)
    ).order_by('-min_distance_km').first()

    if tier:
        return tier.per_km_rate
    return vehicle_type.per_km_rate


def calculate_fare(vehicle_type, distance_km, duration_minutes, pickup_lat, pickup_lon,
                   dropoff_lat, dropoff_lon, request_time, promo_code=None):
    """Calculate fare with all multipliers and discounts"""

    # Base calculations
    base_fare = vehicle_type.base_fare

    # Get appropriate per km rate (from tiers or default)
    per_km_rate = get_distance_tier_rate(vehicle_type, Decimal(str(distance_km)))
    distance_fare = per_km_rate * Decimal(str(distance_km))

    # Time-based fare
    time_fare = vehicle_type.per_minute_rate * Decimal(str(duration_minutes))

    # Subtotal before multipliers
    subtotal = base_fare + distance_fare + time_fare

    # Apply peak hour multiplier
    peak_multiplier, peak_name = get_peak_hour_multiplier(request_time)

    # Apply surge multiplier
    surge_multiplier, surge_name = get_surge_multiplier(
        pickup_lat, pickup_lon, dropoff_lat, dropoff_lon, request_time
    )

    # Total multiplier (peak * surge)
    total_multiplier = peak_multiplier * surge_multiplier

    # Total before discount
    total_before_discount = subtotal * total_multiplier

    # Apply promo code discount
    discount_amount = Decimal('0.00')
    promo_code_applied = None

    if promo_code:
        try:
            promo = PromoCode.objects.get(code=promo_code, is_active=True)
            is_valid, message = promo.is_valid()

            if is_valid and total_before_discount >= promo.min_fare:
                if promo.discount_type == 'percentage':
                    discount = (promo.discount_value / Decimal('100.0')) * total_before_discount
                    if promo.max_discount:
                        discount = min(discount, promo.max_discount)
                    discount_amount = discount
                else:  # fixed
                    discount_amount = min(promo.discount_value, total_before_discount)

                promo_code_applied = promo_code
        except PromoCode.DoesNotExist:
            pass

    # Final fare
    final_fare = max(total_before_discount - discount_amount, vehicle_type.minimum_fare)

    return {
        'vehicle_type': vehicle_type,
        'distance_km': Decimal(str(distance_km)).quantize(Decimal('0.01')),
        'estimated_duration_minutes': duration_minutes,
        'base_fare': base_fare,
        'distance_fare': distance_fare.quantize(Decimal('0.01')),
        'time_fare': time_fare.quantize(Decimal('0.01')),
        'subtotal': subtotal.quantize(Decimal('0.01')),
        'peak_hour_multiplier': peak_multiplier,
        'surge_multiplier': surge_multiplier,
        'total_before_discount': total_before_discount.quantize(Decimal('0.01')),
        'discount_amount': discount_amount.quantize(Decimal('0.01')),
        'final_fare': final_fare.quantize(Decimal('0.01')),
        'promo_code': promo_code_applied,
        'peak_hour_name': peak_name,
        'surge_area_name': surge_name,
    }


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def vehicle_types(request):
    """Get all active vehicle types"""
    types = VehicleType.objects.filter(is_active=True).order_by('-priority', 'name')
    serializer = VehicleTypeSerializer(types, many=True)
    return Response(serializer.data)


@api_view(['POST'])
@permission_classes([AllowAny])  # Allow unauthenticated access for testing
def calculate_fares(request):
    """Calculate fares for all vehicle types or specific vehicle type"""
    serializer = FareCalculationSerializer(data=request.data)

    if not serializer.is_valid():
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    data = serializer.validated_data

    # Calculate distance
    distance_km = calculate_distance(
        data['pickup_latitude'],
        data['pickup_longitude'],
        data['dropoff_latitude'],
        data['dropoff_longitude']
    )

    # Estimate duration (rough estimate: 2 minutes per km in city traffic)
    duration_minutes = int(distance_km * 2)

    # Use current time if not specified
    request_time = data.get('request_time', timezone.now())

    # Get vehicle types to calculate for
    if 'vehicle_type_id' in data and data['vehicle_type_id']:
        vehicle_types_list = VehicleType.objects.filter(
            id=data['vehicle_type_id'],
            is_active=True
        )
    else:
        vehicle_types_list = VehicleType.objects.filter(is_active=True).order_by('-priority', 'name')

    # Calculate fare for each vehicle type
    fares = []
    for vehicle_type in vehicle_types_list:
        fare_data = calculate_fare(
            vehicle_type=vehicle_type,
            distance_km=distance_km,
            duration_minutes=duration_minutes,
            pickup_lat=data['pickup_latitude'],
            pickup_lon=data['pickup_longitude'],
            dropoff_lat=data['dropoff_latitude'],
            dropoff_lon=data['dropoff_longitude'],
            request_time=request_time,
            promo_code=data.get('promo_code')
        )
        fares.append(fare_data)

    # Serialize response
    fare_serializer = FareBreakdownSerializer(fares, many=True)
    return Response(fare_serializer.data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def peak_hours(request):
    """Get all active peak hours"""
    peaks = PeakHour.objects.filter(is_active=True).order_by('day_of_week', 'start_time')
    serializer = PeakHourSerializer(peaks, many=True)
    return Response(serializer.data)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def validate_promo_code(request):
    """Validate a promo code"""
    code = request.data.get('code')
    fare_amount = request.data.get('fare_amount', 0)

    if not code:
        return Response(
            {'error': 'Promo code is required'},
            status=status.HTTP_400_BAD_REQUEST
        )

    try:
        promo = PromoCode.objects.get(code=code)
        is_valid, message = promo.is_valid()

        if not is_valid:
            return Response({'valid': False, 'message': message})

        if Decimal(str(fare_amount)) < promo.min_fare:
            return Response({
                'valid': False,
                'message': f'Minimum fare of R{promo.min_fare} required'
            })

        # Calculate discount
        if promo.discount_type == 'percentage':
            discount = (promo.discount_value / Decimal('100.0')) * Decimal(str(fare_amount))
            if promo.max_discount:
                discount = min(discount, promo.max_discount)
        else:
            discount = promo.discount_value

        return Response({
            'valid': True,
            'message': 'Promo code is valid',
            'discount_type': promo.discount_type,
            'discount_value': promo.discount_value,
            'discount_amount': discount.quantize(Decimal('0.01')),
            'description': promo.description
        })

    except PromoCode.DoesNotExist:
        return Response({'valid': False, 'message': 'Invalid promo code'})
