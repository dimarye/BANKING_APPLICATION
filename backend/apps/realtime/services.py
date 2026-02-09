import json
import asyncio
from datetime import datetime
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from apps.accounts.models import BankAccount
from apps.transactions.models import Transaction
from apps.fraud.models import FraudEvent


class RealtimeService:
    """
    Service for handling real-time events and WebSocket notifications
    """
    
    @staticmethod
    def send_balance_update(account_id, balance, currency):
        """Send balance update event to user's WebSocket connections"""
        from channels.layers import get_channel_layer
        from asgiref.sync import async_to_sync
        
        channel_layer = get_channel_layer()
        
        event_data = {
            "type": "balance_updated",
            "account_id": account_id,
            "balance": str(balance),
            "currency": currency,
            "timestamp": datetime.now().isoformat()
        }
        
        # Send to account-specific group
        async_to_sync(channel_layer.group_send)(
            f"account_{account_id}",
            {
                "type": "balance_updated",
                "data": event_data
            }
        )
    
    @staticmethod
    def send_transaction_update(transaction_id, transaction_data):
        """Send transaction update to WebSocket clients"""
        from channels.layers import get_channel_layer
        from asgiref.sync import async_to_sync
        
        # Get transaction owner
        try:
            transaction = Transaction.objects.get(id=transaction_id)
            user_id = transaction.from_account.user.id
            
            event_data = {
                "type": "transaction_updated",
                "transaction": transaction_data,
                "timestamp": datetime.now().isoformat()
            }
            
            # Send to user's transaction group
            async_to_sync(channel_layer.group_send)(
                f"transactions_{user_id}",
                event_data
            )
            
            # Also send to both account holders
            async_to_sync(channel_layer.group_send)(
                f"account_{transaction.from_account.id}",
                event_data
            )
            
            async_to_sync(channel_layer.group_send)(
                f"account_{transaction.to_account.id}",
                event_data
            )
            
        except Transaction.DoesNotExist:
            pass
    
    @staticmethod
    def send_account_status_update(account_id, status):
        """Send account status update to WebSocket clients"""
        channel_layer = get_channel_layer()
        
        event_data = {
            "type": "account_status_updated",
            "account_id": account_id,
            "status": status,
            "timestamp": datetime.now().isoformat()
        }
        
        # Send to account-specific group
        async_to_sync(channel_layer.group_send)(
            f"account_{account_id}",
            event_data
        )
    
    @staticmethod
    def send_fraud_alert(user_id, alert_data):
        """Send fraud alert to WebSocket clients"""
        channel_layer = get_channel_layer()
        
        event_data = {
            "type": "fraud_alert",
            "alert": alert_data,
            "timestamp": datetime.now().isoformat()
        }
        
        # Send to user's notification group
        async_to_sync(channel_layer.group_send)(
            f"notifications_{user_id}",
            event_data
        )
        
        # Also send to user's banking group
        async_to_sync(channel_layer.group_send)(
            f"user_{user_id}",
            event_data
        )
    
    @staticmethod
    def send_notification(user_id, notification_data):
        """Send general notification to WebSocket clients"""
        channel_layer = get_channel_layer()
        
        event_data = {
            "type": "notification",
            "notification": notification_data,
            "timestamp": datetime.now().isoformat()
        }
        
        # Send to user's notification group
        async_to_sync(channel_layer.group_send)(
            f"notifications_{user_id}",
            event_data
        )


# Signal handlers for automatic real-time updates

@receiver(post_save, sender=BankAccount)
def bank_account_updated(sender, instance, created, **kwargs):
    """Handle BankAccount updates"""
    if not created:
        # Send status update if status changed
        RealtimeService.send_account_status_update(
            instance.id,
            instance.status
        )
        
        # Send balance update
        from apps.ledger.services import get_account_balance
        try:
            balance = get_account_balance(instance.ledger_account, instance.currency)
            RealtimeService.send_balance_update(
                instance.id,
                balance,
                instance.currency
            )
        except Exception:
            pass


@receiver(post_save, sender=Transaction)
def transaction_updated(sender, instance, created, **kwargs):
    """Handle Transaction updates"""
    from apps.transactions.serializers import TransactionSerializer
    
    serializer = TransactionSerializer(instance)
    transaction_data = serializer.data
    
    RealtimeService.send_transaction_update(
        instance.id,
        transaction_data
    )


@receiver(post_save, sender=FraudEvent)
def fraud_event_created(sender, instance, created, **kwargs):
    """Handle FraudEvent creation"""
    if created:
        # Get user from transaction
        user_id = None
        if instance.transaction:
            user_id = instance.transaction.from_account.user.id
        
        if user_id:
            alert_data = {
                "id": instance.id,
                "transaction_id": str(instance.transaction.id),
                "risk_level": instance.risk_level,
                "decision": instance.decision,
                "description": instance.description,
                "metadata": instance.metadata
            }
            
            RealtimeService.send_fraud_alert(user_id, alert_data)
