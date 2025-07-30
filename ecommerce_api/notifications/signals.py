from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync
from django.utils import timezone
from product.models import Order
import json

# Store the old status before saving
@receiver(pre_save, sender=Order)
def store_old_status(sender, instance, **kwargs):
    if instance.pk:  # Only for existing instances
        try:
            old_instance = Order.objects.get(pk=instance.pk)
            instance._old_status = old_instance.status
        except Order.DoesNotExist:
            instance._old_status = None
    else:
        instance._old_status = None

@receiver(post_save, sender=Order)
def order_status_changed(sender, instance, created, **kwargs):
    # Don't send notification for newly created orders
    if created:
        return
    
    # Check if status actually changed
    old_status = getattr(instance, '_old_status', None)
    if old_status and old_status != instance.status:
        # Send real-time notification
        channel_layer = get_channel_layer()
        group_name = f"user_{instance.customer.id}_orders"
        
        # Create a user-friendly message
        status_messages = {
            'confirmed': 'Your order has been confirmed!',
            'processing': 'Your order is being processed.',
            'shipped': 'Your order has been shipped!',
            'delivered': 'Your order has been delivered.',
            'cancelled': 'Your order has been cancelled.',
            'refunded': 'Your order has been refunded.',
        }
        
        message = status_messages.get(instance.status, 'Your order status has been updated.')
        
        async_to_sync(channel_layer.group_send)(
            group_name,
            {
                'type': 'order_status_update',
                'order_id': str(instance.id),
                'order_number': instance.order_number,
                'old_status': old_status,
                'new_status': instance.status,
                'message': message,
                'timestamp': timezone.now().isoformat()
            }
        )
