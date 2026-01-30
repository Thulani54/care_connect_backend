from django.urls import path
from . import views

urlpatterns = [
    path('vehicle-types/', views.vehicle_types, name='vehicle-types'),
    path('calculate-fares/', views.calculate_fares, name='calculate-fares'),
    path('peak-hours/', views.peak_hours, name='peak-hours'),
    path('validate-promo/', views.validate_promo_code, name='validate-promo'),
]
