from django.urls import path
from . import views

urlpatterns = [
    # User Settings
    path('user/', views.user_settings, name='user_settings'),

    # App Content
    path('content/<str:content_type>/', views.app_content, name='app_content'),

    # FAQs
    path('faqs/', views.faqs, name='faqs'),

    # Support Tickets
    path('support/tickets/', views.support_tickets, name='support_tickets'),
    path('support/tickets/<int:ticket_id>/', views.support_ticket_detail, name='support_ticket_detail'),
]
