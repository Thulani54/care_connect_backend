from django.urls import path
from . import views

app_name = 'communications'

urlpatterns = [
    path('otp/send/', views.send_otp, name='send_otp'),
    path('otp/verify/', views.verify_otp, name='verify_otp'),
    path('otp/resend/', views.resend_otp, name='resend_otp'),
]
