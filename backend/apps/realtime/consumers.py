import json
import asyncio
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async


class BankingConsumer(AsyncWebsocketConsumer):
    """
    WebSocket consumer for real-time banking updates
    """
    
    async def connect(self):
        """Handle WebSocket connection"""
        from django.contrib.auth.models import AnonymousUser
        
        self.user = self.scope["user"]
        
        # Reject anonymous users
        if isinstance(self.user, AnonymousUser):
            await self.close()
            return
        
        self.user_group_name = f"user_{self.user.id}"
        
        # Join user group
        await self.channel_layer.group_add(
            self.user_group_name,
            self.channel_name
        )
        
        await self.accept()
        
        # Send initial connection message
        await self.send(text_data=json.dumps({
            "type": "connection_established",
            "message": "Connected to real-time updates",
            "user_id": self.user.id
        }))
    
    async def disconnect(self, close_code):
        """Handle WebSocket disconnection"""
        # Leave user group
        await self.channel_layer.group_discard(
            self.user_group_name,
            self.channel_name
        )
    
    async def receive(self, text_data):
        """Handle received WebSocket messages"""
        try:
            data = json.loads(text_data)
            message_type = data.get("type")
            
            if message_type == "ping":
                await self.send(text_data=json.dumps({
                    "type": "pong",
                    "timestamp": asyncio.get_event_loop().time()
                }))
            elif message_type == "subscribe_balances":
                await self.handle_subscribe_balances(data)
            elif message_type == "subscribe_transactions":
                await self.handle_subscribe_transactions(data)
            else:
                await self.send(text_data=json.dumps({
                    "type": "error",
                    "message": f"Unknown message type: {message_type}"
                }))
                
        except json.JSONDecodeError:
            await self.send(text_data=json.dumps({
                "type": "error",
                "message": "Invalid JSON format"
            }))
        except Exception as e:
            await self.send(text_data=json.dumps({
                "type": "error",
                "message": "Internal server error"
            }))
    
    async def handle_subscribe_balances(self, data):
        """Handle subscription to balance updates"""
        account_ids = data.get("account_ids", [])
        
        if not account_ids:
            # Subscribe to all user's accounts
            account_ids = await self.get_user_account_ids()
        
        # Join account-specific groups
        for account_id in account_ids:
            group_name = f"account_{account_id}"
            await self.channel_layer.group_add(
                group_name,
                self.channel_name
            )
        
        await self.send(text_data=json.dumps({
            "type": "subscription_confirmed",
            "subscription": "balances",
            "account_ids": account_ids
        }))
    
    async def handle_subscribe_transactions(self, data):
        """Handle subscription to transaction updates"""
        # Join user's transaction group
        await self.channel_layer.group_add(
            f"transactions_{self.user.id}",
            self.channel_name
        )
        
        await self.send(text_data=json.dumps({
            "type": "subscription_confirmed",
            "subscription": "transactions"
        }))
    
    # Event handlers for real-time updates
    
    async def balance_updated(self, event):
        """Handle balance update event"""
        await self.send(text_data=json.dumps({
            "type": "balance_updated",
            "account_id": event["account_id"],
            "balance": event["balance"],
            "currency": event["currency"],
            "timestamp": event["timestamp"]
        }))
    
    async def transaction_updated(self, event):
        """Handle transaction update event"""
        await self.send(text_data=json.dumps({
            "type": "transaction_updated",
            "transaction": event["transaction"],
            "timestamp": event["timestamp"]
        }))
    
    async def account_status_updated(self, event):
        """Handle account status update event"""
        await self.send(text_data=json.dumps({
            "type": "account_status_updated",
            "account_id": event["account_id"],
            "status": event["status"],
            "timestamp": event["timestamp"]
        }))
    
    async def fraud_alert(self, event):
        """Handle fraud alert event"""
        await self.send(text_data=json.dumps({
            "type": "fraud_alert",
            "alert": event["alert"],
            "timestamp": event["timestamp"]
        }))
    
    @database_sync_to_async
    def get_user_account_ids(self):
        """Get user's account IDs from database"""
        from apps.accounts.models import BankAccount
        return list(
            BankAccount.objects.filter(user=self.user)
            .values_list('id', flat=True)
        )


class NotificationConsumer(AsyncWebsocketConsumer):
    """
    WebSocket consumer for general notifications
    """
    
    async def connect(self):
        """Handle WebSocket connection"""
        from django.contrib.auth.models import AnonymousUser
        
        self.user = self.scope["user"]
        
        # Reject anonymous users
        if isinstance(self.user, AnonymousUser):
            await self.close()
            return
        
        self.user_group_name = f"notifications_{self.user.id}"
        
        # Join notification group
        await self.channel_layer.group_add(
            self.user_group_name,
            self.channel_name
        )
        
        await self.accept()
        
        # Send initial connection message
        await self.send(text_data=json.dumps({
            "type": "connection_established",
            "message": "Connected to notifications",
            "user_id": self.user.id
        }))
    
    async def disconnect(self, close_code):
        """Handle WebSocket disconnection"""
        await self.channel_layer.group_discard(
            self.user_group_name,
            self.channel_name
        )
    
    async def receive(self, text_data):
        """Handle received WebSocket messages"""
        try:
            data = json.loads(text_data)
            message_type = data.get("type")
            
            if message_type == "ping":
                await self.send(text_data=json.dumps({
                    "type": "pong",
                    "timestamp": asyncio.get_event_loop().time()
                }))
            else:
                await self.send(text_data=json.dumps({
                    "type": "error",
                    "message": f"Unknown message type: {message_type}"
                }))
                
        except json.JSONDecodeError:
            await self.send(text_data=json.dumps({
                "type": "error",
                "message": "Invalid JSON format"
            }))
    
    async def notification(self, event):
        """Handle notification event"""
        await self.send(text_data=json.dumps({
            "type": "notification",
            "notification": event["notification"],
            "timestamp": event["timestamp"]
        }))
