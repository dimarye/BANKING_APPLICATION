from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from django.conf import settings
from .services import RealtimeService


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def websocket_info(request):
    """Get WebSocket connection information"""
    return Response({
        "websocket_url": f"ws://localhost:8000/ws/banking/",
        "notification_url": f"ws://localhost:8000/ws/notifications/",
        "available_events": [
            "balance_updated",
            "transaction_updated",
            "account_status_updated",
            "fraud_alert",
            "notification"
        ],
        "message_types": {
            "ping": "Ping server to check connection",
            "subscribe_balances": "Subscribe to balance updates for specific accounts",
            "subscribe_transactions": "Subscribe to transaction updates"
        }
    })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def test_notification(request):
    """Send test notification to user"""
    notification_data = {
        "id": "test_001",
        "title": "Test Notification",
        "message": "This is a test notification from the banking system",
        "type": "info",
        "data": {
            "test": True,
            "timestamp": "2023-01-01T00:00:00Z"
        }
    }
    
    RealtimeService.send_notification(request.user.id, notification_data)
    
    return Response({
        "message": "Test notification sent",
        "notification": notification_data
    }, status=status.HTTP_200_OK)
