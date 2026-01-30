from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from .models import UserSettings, AppContent, FAQ, SupportTicket
from .serializers import (
    UserSettingsSerializer,
    AppContentSerializer,
    FAQSerializer,
    SupportTicketSerializer,
)


@api_view(['GET', 'PUT', 'PATCH'])
@permission_classes([IsAuthenticated])
def user_settings(request):
    """
    GET: Retrieve user settings
    PUT/PATCH: Update user settings
    """
    # Get or create user settings
    settings, created = UserSettings.objects.get_or_create(user=request.user)

    if request.method == 'GET':
        serializer = UserSettingsSerializer(settings)
        return Response(serializer.data)

    elif request.method in ['PUT', 'PATCH']:
        serializer = UserSettingsSerializer(
            settings,
            data=request.data,
            partial=(request.method == 'PATCH')
        )
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
def app_content(request, content_type):
    """
    Get app content by type (privacy_policy, terms_of_service, about, etc.)
    """
    try:
        content = AppContent.objects.get(
            content_type=content_type,
            is_active=True
        )
        serializer = AppContentSerializer(content)
        return Response(serializer.data)
    except AppContent.DoesNotExist:
        return Response(
            {'detail': 'Content not found'},
            status=status.HTTP_404_NOT_FOUND
        )


@api_view(['GET'])
def faqs(request):
    """
    Get all active FAQs, optionally filter by category
    """
    category = request.query_params.get('category', None)

    queryset = FAQ.objects.filter(is_active=True)

    if category:
        queryset = queryset.filter(category=category)

    serializer = FAQSerializer(queryset, many=True)
    return Response(serializer.data)


@api_view(['GET', 'POST'])
@permission_classes([IsAuthenticated])
def support_tickets(request):
    """
    GET: List user's support tickets
    POST: Create a new support ticket
    """
    if request.method == 'GET':
        tickets = SupportTicket.objects.filter(user=request.user)
        serializer = SupportTicketSerializer(tickets, many=True)
        return Response(serializer.data)

    elif request.method == 'POST':
        serializer = SupportTicketSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(user=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def support_ticket_detail(request, ticket_id):
    """
    Get details of a specific support ticket
    """
    try:
        ticket = SupportTicket.objects.get(id=ticket_id, user=request.user)
        serializer = SupportTicketSerializer(ticket)
        return Response(serializer.data)
    except SupportTicket.DoesNotExist:
        return Response(
            {'detail': 'Ticket not found'},
            status=status.HTTP_404_NOT_FOUND
        )
