from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenRefreshView
from .views import (
    UserRegistrationView,
    DriverViewSet,
    BookingViewSet,
    ElderlyMemberViewSet,
    CaregiverRelationshipViewSet,
)
from . import auth_views

router = DefaultRouter()
router.register(r'users', UserRegistrationView, basename='user')
router.register(r'drivers', DriverViewSet, basename='driver')
router.register(r'bookings', BookingViewSet, basename='booking')
router.register(r'elderly-members', ElderlyMemberViewSet, basename='elderly-member')
router.register(r'caregivers', CaregiverRelationshipViewSet, basename='caregiver')

urlpatterns = [
    # OTP Authentication
    path('auth/send-otp/', auth_views.send_otp, name='send-otp'),
    path('auth/verify-otp/', auth_views.verify_otp, name='verify-otp'),
    path('auth/register/', auth_views.register, name='register'),
    path('auth/login/', auth_views.login, name='login'),
    path('auth/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('auth/profile/', auth_views.get_profile, name='get-profile'),
    path('auth/profile/update/', auth_views.update_profile, name='update-profile'),

    # API endpoints
    path('', include(router.urls)),
]
