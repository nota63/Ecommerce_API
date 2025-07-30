# views.py
from rest_framework import viewsets, status, filters
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Q, Prefetch, F
from django.core.cache import cache
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from django.db import transaction
from decimal import Decimal
import uuid

from .models import (
    Category, Brand, Product, ProductImage, ProductVariant,
    Cart, CartItem, Order, OrderItem, Review, Coupon,
    Wishlist, WishlistItem
)
from .serializers import (
    CategorySerializer, BrandSerializer, ProductListSerializer,
    ProductDetailSerializer, CartSerializer, CartItemSerializer,
    OrderSerializer, OrderCreateSerializer, ReviewSerializer,
    CouponSerializer, WishlistSerializer, WishlistItemSerializer
)

from .pagination import StandardResultsSetPagination
from .filters import ProductFilter


class CategoryViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for browsing categories
    """
    queryset = Category.objects.filter(is_active=True).prefetch_related('children')
    serializer_class = CategorySerializer
    lookup_field = 'slug'
    filter_backends = [filters.SearchFilter]
    search_fields = ['name', 'description']
    
    @method_decorator(cache_page(60 * 15))  # Cache for 15 minutes
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)
    
    @method_decorator(cache_page(60 * 15))
    def retrieve(self, request, *args, **kwargs):
        return super().retrieve(request, *args, **kwargs)
    
    def get_queryset(self):
        queryset = super().get_queryset()
        # Only return parent categories for listing
        if self.action == 'list':
            queryset = queryset.filter(parent=None)
        return queryset
    
    @action(detail=True, methods=['get'])
    def products(self, request, slug=None):
        """Get products in this category"""
        category = self.get_object()
        products = Product.objects.filter(
            category=category,
            is_active=True
        ).select_related('category', 'brand').prefetch_related('images')
        
        # Apply filters
        filter_backend = ProductFilter()
        products = filter_backend.filter_queryset(request, products, self)
        
        # Paginate
        page = self.paginate_queryset(products)
        if page is not None:
            serializer = ProductListSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = ProductListSerializer(products, many=True)
        return Response(serializer.data)


class BrandViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for browsing brands
    """
    queryset = Brand.objects.filter(is_active=True)
    serializer_class = BrandSerializer
    lookup_field = 'slug'
    filter_backends = [filters.SearchFilter]
    search_fields = ['name', 'description']
    pagination_class = StandardResultsSetPagination
    
    @method_decorator(cache_page(60 * 15))
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)
    
    @action(detail=True, methods=['get'])
    def products(self, request, slug=None):
        """Get products from this brand"""
        brand = self.get_object()
        products = Product.objects.filter(
            brand=brand,
            is_active=True
        ).select_related('category', 'brand').prefetch_related('images')
        
        # Apply filters
        filter_backend = ProductFilter()
        products = filter_backend.filter_queryset(request, products, self)
        
        # Paginate
        page = self.paginate_queryset(products)
        if page is not None:
            serializer = ProductListSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = ProductListSerializer(products, many=True)
        return Response(serializer.data)


class ProductViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for browsing products
    """
    queryset = Product.objects.filter(is_active=True)
    lookup_field = 'slug'
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = ProductFilter
    search_fields = ['name', 'description', 'short_description', 'sku']
    ordering_fields = ['price', 'created_at', 'average_rating', 'name']
    ordering = ['-created_at']
    pagination_class = StandardResultsSetPagination
    
    def get_serializer_class(self):
        if self.action == 'retrieve':
            return ProductDetailSerializer
        return ProductListSerializer
    
    def get_queryset(self):
        queryset = super().get_queryset()
        
        if self.action == 'list':
            # Optimize for list view
            queryset = queryset.select_related('category', 'brand').prefetch_related(
                Prefetch('images', queryset=ProductImage.objects.filter(is_primary=True))
            )
        elif self.action == 'retrieve':
            # Optimize for detail view
            queryset = queryset.select_related('category', 'brand').prefetch_related(
                'images', 'variants', 'attributes__attribute_value__attribute_name',
                Prefetch('reviews', queryset=Review.objects.filter(is_approved=True)[:5])
            )
        
        return queryset
    
    @method_decorator(cache_page(60 * 5))  # Cache for 5 minutes
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)
    
    def retrieve(self, request, *args, **kwargs):
        # Cache individual products for longer
        cache_key = f"product_detail_{kwargs.get('slug')}"
        cached_data = cache.get(cache_key)
        
        if cached_data:
            return Response(cached_data)
        
        response = super().retrieve(request, *args, **kwargs)
        cache.set(cache_key, response.data, 60 * 10)  # Cache for 10 minutes
        return response
    
    @action(detail=False, methods=['get'])
    def featured(self, request):
        """Get featured products"""
        cache_key = "featured_products"
        cached_data = cache.get(cache_key)
        
        if cached_data:
            return Response(cached_data)
        
        products = self.get_queryset().filter(is_featured=True)[:10]
        serializer = self.get_serializer(products, many=True)
        cache.set(cache_key, serializer.data, 60 * 30)  # Cache for 30 minutes
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def on_sale(self, request):
        """Get products on sale"""
        products = self.get_queryset().filter(
            compare_price__isnull=False,
            price__lt=F('compare_price')
        )
        
        page = self.paginate_queryset(products)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = self.get_serializer(products, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def reviews(self, request, slug=None):
        """Get product reviews"""
        product = self.get_object()
        reviews = Review.objects.filter(
            product=product,
            is_approved=True
        ).select_related('customer')
        
        page = self.paginate_queryset(reviews)
        if page is not None:
            serializer = ReviewSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        
        serializer = ReviewSerializer(reviews, many=True)
        return Response(serializer.data)


class CartViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing shopping cart
    """
    serializer_class = CartSerializer
    
    def get_queryset(self):
        if self.request.user.is_authenticated:
            return Cart.objects.filter(customer=self.request.user).prefetch_related(
                'items__product__category',
                'items__product__brand',
                'items__variant'
            )
        else:
            session_key = self.request.session.session_key
            if not session_key:
                self.request.session.create()
                session_key = self.request.session.session_key
            return Cart.objects.filter(session_key=session_key).prefetch_related(
                'items__product__category',
                'items__product__brand',
                'items__variant'
            )
    
    def get_or_create_cart(self):
        """Get or create cart for current user/session"""
        if self.request.user.is_authenticated:
            cart, created = Cart.objects.get_or_create(
                customer=self.request.user
            )
        else:
            session_key = self.request.session.session_key
            if not session_key:
                self.request.session.create()
                session_key = self.request.session.session_key
            cart, created = Cart.objects.get_or_create(
                session_key=session_key
            )
        return cart
    
    def list(self, request, *args, **kwargs):
        """Get current cart"""
        cart = self.get_or_create_cart()
        serializer = self.get_serializer(cart)
        return Response(serializer.data)
    
    @action(detail=False, methods=['post'])
    def add_item(self, request):
        """Add item to cart"""
        cart = self.get_or_create_cart()
        serializer = CartItemSerializer(data=request.data)
        
        if serializer.is_valid():
            product_id = serializer.validated_data['product_id']
            variant_id = serializer.validated_data.get('variant_id')
            quantity = serializer.validated_data['quantity']
            
            # Check if item already exists in cart
            cart_item, created = CartItem.objects.get_or_create(
                cart=cart,
                product_id=product_id,
                variant_id=variant_id,
                defaults={'quantity': quantity}
            )
            
            if not created:
                # Update quantity if item already exists
                cart_item.quantity += quantity
                cart_item.save()
            
            return Response(
                CartItemSerializer(cart_item).data,
                status=status.HTTP_201_CREATED
            )
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['patch'])
    def update_item(self, request):
        """Update cart item quantity"""
        cart = self.get_or_create_cart()
        item_id = request.data.get('item_id')
        quantity = request.data.get('quantity')
        
        try:
            cart_item = CartItem.objects.get(id=item_id, cart=cart)
            if quantity <= 0:
                cart_item.delete()
                return Response({'message': 'Item removed from cart'})
            else:
                cart_item.quantity = quantity
                cart_item.save()
                return Response(CartItemSerializer(cart_item).data)
        except CartItem.DoesNotExist:
            return Response(
                {'error': 'Cart item not found'},
                status=status.HTTP_404_NOT_FOUND
            )
    
    @action(detail=False, methods=['delete'])
    def remove_item(self, request):
        """Remove item from cart"""
        cart = self.get_or_create_cart()
        item_id = request.data.get('item_id')
        
        try:
            cart_item = CartItem.objects.get(id=item_id, cart=cart)
            cart_item.delete()
            return Response({'message': 'Item removed from cart'})
        except CartItem.DoesNotExist:
            return Response(
                {'error': 'Cart item not found'},
                status=status.HTTP_404_NOT_FOUND
            )
    
    @action(detail=False, methods=['delete'])
    def clear(self, request):
        """Clear entire cart"""
        cart = self.get_or_create_cart()
        cart.items.all().delete()
        return Response({'message': 'Cart cleared'})


class WishlistViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing wishlists
    """
    serializer_class = WishlistSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        return Wishlist.objects.filter(customer=self.request.user).prefetch_related(
            'items__product__category',
            'items__product__brand'
        )
    
    def perform_create(self, serializer):
        serializer.save(customer=self.request.user)
    
    @action(detail=True, methods=['post'])
    def add_item(self, request, pk=None):
        """Add item to wishlist"""
        wishlist = self.get_object()
        serializer = WishlistItemSerializer(data=request.data)
        
        if serializer.is_valid():
            product_id = serializer.validated_data['product_id']
            
            # Check if item already exists
            if wishlist.items.filter(product_id=product_id).exists():
                return Response(
                    {'error': 'Product already in wishlist'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            wishlist_item = WishlistItem.objects.create(
                wishlist=wishlist,
                product_id=product_id
            )
            
            return Response(
                WishlistItemSerializer(wishlist_item).data,
                status=status.HTTP_201_CREATED
            )
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['delete'])
    def remove_item(self, request, pk=None):
        """Remove item from wishlist"""
        wishlist = self.get_object()
        product_id = request.data.get('product_id')
        
        try:
            wishlist_item = wishlist.items.get(product_id=product_id)
            wishlist_item.delete()
            return Response({'message': 'Item removed from wishlist'})
        except WishlistItem.DoesNotExist:
            return Response(
                {'error': 'Item not found in wishlist'},
                status=status.HTTP_404_NOT_FOUND
            )


class CouponViewSet(viewsets.ReadOnlyModelViewSet):
    """
    ViewSet for validating coupons
    """
    queryset = Coupon.objects.filter(is_active=True)
    serializer_class = CouponSerializer
    lookup_field = 'code'
    
    @action(detail=True, methods=['post'])
    def validate_coupon(self, request, code=None):
        """Validate coupon for a given order amount"""
        coupon = self.get_object()
        order_amount = request.data.get('order_amount', 0)
        
        if not coupon.is_valid:
            return Response(
                {'valid': False, 'message': 'Coupon is not valid'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        if coupon.minimum_order_amount and order_amount < coupon.minimum_order_amount:
            return Response(
                {
                    'valid': False,
                    'message': f'Minimum order amount is {coupon.minimum_order_amount}'
                },
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Calculate discount
        if coupon.discount_type == 'percentage':
            discount = order_amount * (coupon.discount_value / 100)
        else:
            discount = coupon.discount_value
        
        if coupon.maximum_discount_amount:
            discount = min(discount, coupon.maximum_discount_amount)
        
        return Response({
            'valid': True,
            'discount_amount': discount,
            'coupon': CouponSerializer(coupon).data
        })


class OrderViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing orders
    """
    permission_classes = [IsAuthenticated]
    pagination_class = StandardResultsSetPagination
    
    def get_queryset(self):
        return Order.objects.filter(customer=self.request.user).prefetch_related(
            'items__product',
            'items__variant'
        )
    
    def get_serializer_class(self):
        if self.action == 'create':
            return OrderCreateSerializer
        return OrderSerializer
    
    @transaction.atomic
    def create(self, request, *args, **kwargs):
        """Create order from cart"""
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        cart_id = serializer.validated_data['cart_id']
        coupon_code = serializer.validated_data.get('coupon_code')
        
        try:
            cart = Cart.objects.get(id=cart_id)
            
            # Calculate totals
            subtotal = cart.total_price
            tax_amount = subtotal * Decimal('0.10')  # 10% tax
            shipping_amount = Decimal('10.00') if subtotal < 100 else Decimal('0.00')
            discount_amount = Decimal('0.00')
            
            # Apply coupon if provided
            if coupon_code:
                coupon = Coupon.objects.get(code=coupon_code)
                if coupon.discount_type == 'percentage':
                    discount_amount = subtotal * (coupon.discount_value / 100)
                else:
                    discount_amount = coupon.discount_value
                
                if coupon.maximum_discount_amount:
                    discount_amount = min(discount_amount, coupon.maximum_discount_amount)
                
                coupon.used_count += 1
                coupon.save()
            
            total_amount = subtotal + tax_amount + shipping_amount - discount_amount
            
            # Create order
            order = Order.objects.create(
                customer=request.user,
                subtotal=subtotal,
                tax_amount=tax_amount,
                shipping_amount=shipping_amount,
                discount_amount=discount_amount,
                total_amount=total_amount,
                billing_address=serializer.validated_data['billing_address'],
                shipping_address=serializer.validated_data['shipping_address'],
                notes=serializer.validated_data.get('notes', '')
            )
            
            # Create order items
            for cart_item in cart.items.all():
                OrderItem.objects.create(
                    order=order,
                    product=cart_item.product,
                    variant=cart_item.variant,
                    quantity=cart_item.quantity,
                    unit_price=cart_item.unit_price,
                    total_price=cart_item.total_price,
                    product_name=cart_item.product.name,
                    product_sku=cart_item.product.sku,
                    variant_name=cart_item.variant.name if cart_item.variant else ''
                )
                
                # Update stock
                if cart_item.variant:
                    cart_item.variant.stock_quantity -= cart_item.quantity
                    cart_item.variant.save()
                elif cart_item.product.track_inventory:
                    cart_item.product.stock_quantity -= cart_item.quantity
                    cart_item.product.save()
            
            # Clear cart
            cart.items.all().delete()
            
            return Response(
                OrderSerializer(order).data,
                status=status.HTTP_201_CREATED
            )
            
        except Cart.DoesNotExist:
            return Response(
                {'error': 'Cart not found'},
                status=status.HTTP_404_NOT_FOUND
            )
    
    @action(detail=True, methods=['post'])
    def cancel(self, request, pk=None):
        """Cancel an order"""
        order = self.get_object()
        
        if order.status in ['delivered', 'cancelled', 'refunded']:
            return Response(
                {'error': 'Order cannot be cancelled'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        order.status = 'cancelled'
        order.save()
        
        # Restore stock
        for item in order.items.all():
            if item.variant:
                item.variant.stock_quantity += item.quantity
                item.variant.save()
            elif item.product.track_inventory:
                item.product.stock_quantity += item.quantity
                item.product.save()
        
        return Response(OrderSerializer(order).data)


class ReviewViewSet(viewsets.ModelViewSet):
    """
    ViewSet for managing product reviews
    """
    serializer_class = ReviewSerializer
    permission_classes = [IsAuthenticatedOrReadOnly]
    pagination_class = StandardResultsSetPagination
    
    def get_queryset(self):
        if self.action in ['list', 'retrieve']:
            return Review.objects.filter(is_approved=True).select_related('customer', 'product')
        return Review.objects.filter(customer=self.request.user).select_related('product')
    
    def perform_create(self, serializer):
        serializer.save(customer=self.request.user)
    
    def get_permissions(self):
        """
        Set permissions based on action
        """
        if self.action in ['update', 'partial_update', 'destroy']:
            # Only authenticated users can modify their own reviews
            permission_classes = [IsAuthenticated]
        else:
            permission_classes = [IsAuthenticatedOrReadOnly]
        
        return [permission() for permission in permission_classes]
    
    def perform_update(self, serializer):
        """Ensure users can only update their own reviews"""
        if serializer.instance.customer != self.request.user:
            raise PermissionError("You can only edit your own reviews")
        serializer.save()
    
    def perform_destroy(self, instance):
        """Ensure users can only delete their own reviews"""
        if instance.customer != self.request.user:
            raise PermissionError("You can only delete your own reviews")
        instance.delete()