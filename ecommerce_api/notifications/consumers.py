import json
from channels.generic.websocket import AsyncWebsocketConsumer
from channels.db import database_sync_to_async
from django.contrib.auth.models import User

class OrderNotificationConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        # Get user from scope (requires authentication)
        self.user = self.scope["user"]
        
        if self.user.is_anonymous:
            await self.close()
            return
            
        # Create a unique group name for the user
        self.group_name = f"user_{self.user.id}_orders"
        
        # Join the user's group
        await self.channel_layer.group_add(
            self.group_name,
            self.channel_name
        )
        
        await self.accept()
        
        # Send connection confirmation
        await self.send(text_data=json.dumps({
            'type': 'connection_established',
            'message': 'Connected to order notifications'
        }))

    async def disconnect(self, close_code):
        # Leave the group
        if hasattr(self, 'group_name'):
            await self.channel_layer.group_discard(
                self.group_name,
                self.channel_name
            )

    # Receive message from WebSocket
    async def receive(self, text_data):
        # Handle any incoming messages if needed
        pass

    # Receive message from group
    async def order_status_update(self, event):
        # Send message to WebSocket
        await self.send(text_data=json.dumps({
            'type': 'order_status_update',
            'order_id': event['order_id'],
            'order_number': event['order_number'],
            'old_status': event['old_status'],
            'new_status': event['new_status'],
            'message': event['message'],
            'timestamp': event['timestamp']
        }))
