from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from product.models import Order
from .serializers import OrderNotificationSerializer

class OrderViewSet(viewsets.ModelViewSet):
    serializer_class = OrderNotificationSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return Order.objects.filter(customer=self.request.user)
    
    @action(detail=True, methods=['patch'])
    def update_status(self, request, pk=None):
        """Admin endpoint to update order status"""
        order = self.get_object()
        new_status = request.data.get('status')
        
        if new_status in dict(Order.ORDER_STATUS_CHOICES):
            order.status = new_status
            order.save()  # This will trigger the signal
            
            return Response({
                'message': 'Order status updated successfully',
                'order_id': str(order.id),
                'new_status': new_status
            })
        
        return Response(
            {'error': 'Invalid status'}, 
            status=status.HTTP_400_BAD_REQUEST
        )