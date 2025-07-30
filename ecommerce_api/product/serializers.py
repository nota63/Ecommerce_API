# serializers.py
from rest_framework import serializers
from django.contrib.auth.models import User
from .models import (
    Category, Brand, Product, ProductImage, ProductVariant, 
    AttributeName, AttributeValue, ProductAttribute,
    Cart, CartItem, Order, OrderItem, Review, Coupon, 
    Wishlist, WishlistItem
)


class CategorySerializer(serializers.ModelSerializer):
    children = serializers.SerializerMethodField()
    product_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Category
        fields = [
            'id', 'name', 'slug', 'description', 'image', 
            'parent', 'is_active', 'children', 'product_count',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['slug', 'created_at', 'updated_at']
    
    def get_children(self, obj):
        if hasattr(obj, 'children') and obj.children.exists():
            return CategorySerializer(obj.children.filter(is_active=True), many=True).data
        return []
    
    def get_product_count(self, obj):
        return obj.products.filter(is_active=True).count()


class BrandSerializer(serializers.ModelSerializer):
    product_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Brand
        fields = [
            'id', 'name', 'slug', 'description', 'logo', 
            'website', 'is_active', 'product_count', 'created_at'
        ]
        read_only_fields = ['slug', 'created_at']
    
    def get_product_count(self, obj):
        return obj.products.filter(is_active=True).count()


class ProductImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductImage
        fields = ['id', 'image', 'alt_text', 'is_primary', 'sort_order']


class ProductVariantSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductVariant
        fields = [
            'id', 'name', 'sku', 'price', 'stock_quantity', 
            'is_active', 'created_at'
        ]


class AttributeValueSerializer(serializers.ModelSerializer):
    attribute_name = serializers.CharField(source='attribute_name.display_name', read_only=True)
    
    class Meta:
        model = AttributeValue
        fields = ['id', 'attribute_name', 'value']


class ProductAttributeSerializer(serializers.ModelSerializer):
    attribute_name = serializers.CharField(source='attribute_value.attribute_name.display_name', read_only=True)
    value = serializers.CharField(source='attribute_value.value', read_only=True)
    
    class Meta:
        model = ProductAttribute
        fields = ['attribute_name', 'value']


class ProductListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for product listings"""
    category = CategorySerializer(read_only=True)
    brand = BrandSerializer(read_only=True)
    primary_image = serializers.SerializerMethodField()
    
    class Meta:
        model = Product
        fields = [
            'id', 'name', 'slug', 'short_description', 'category', 
            'brand', 'price', 'compare_price', 'stock_status', 
            'is_featured', 'average_rating', 'total_reviews',
            'primary_image', 'is_on_sale', 'discount_percentage'
        ]
    
    def get_primary_image(self, obj):
        primary_image = obj.images.filter(is_primary=True).first()
        if primary_image:
            return ProductImageSerializer(primary_image).data
        return None


class ProductDetailSerializer(serializers.ModelSerializer):
    """Detailed serializer for individual product views"""
    category = CategorySerializer(read_only=True)
    brand = BrandSerializer(read_only=True)
    images = ProductImageSerializer(many=True, read_only=True)
    variants = ProductVariantSerializer(many=True, read_only=True)
    attributes = ProductAttributeSerializer(many=True, read_only=True)
    reviews = serializers.SerializerMethodField()
    
    class Meta:
        model = Product
        fields = [
            'id', 'name', 'slug', 'description', 'short_description',
            'category', 'brand', 'price', 'compare_price', 'cost_price',
            'sku', 'barcode', 'stock_quantity', 'min_stock_level',
            'stock_status', 'track_inventory', 'weight', 'length',
            'width', 'height', 'meta_title', 'meta_description',
            'is_active', 'is_featured', 'is_digital', 'requires_shipping',
            'average_rating', 'total_reviews', 'created_at', 'updated_at',
            'published_at', 'is_on_sale', 'discount_percentage',
            'images', 'variants', 'attributes', 'reviews'
        ]
    
    def get_reviews(self, obj):
        recent_reviews = obj.reviews.filter(is_approved=True)[:5]
        return ReviewSerializer(recent_reviews, many=True).data


class CartItemSerializer(serializers.ModelSerializer):
    product = ProductListSerializer(read_only=True)
    variant = ProductVariantSerializer(read_only=True)
    product_id = serializers.UUIDField(write_only=True)
    variant_id = serializers.IntegerField(write_only=True, required=False)
    
    class Meta:
        model = CartItem
        fields = [
            'id', 'product', 'variant', 'quantity', 'unit_price',
            'total_price', 'product_id', 'variant_id', 'created_at'
        ]
        read_only_fields = ['unit_price', 'total_price', 'created_at']
    
    def validate_quantity(self, value):
        if value <= 0:
            raise serializers.ValidationError("Quantity must be greater than 0")
        return value
    
    def validate(self, data):
        product_id = data.get('product_id')
        variant_id = data.get('variant_id')
        quantity = data.get('quantity', 1)
        
        try:
            product = Product.objects.get(id=product_id, is_active=True)
        except Product.DoesNotExist:
            raise serializers.ValidationError("Product not found or inactive")
        
        if variant_id:
            try:
                variant = ProductVariant.objects.get(
                    id=variant_id, 
                    product=product, 
                    is_active=True
                )
                if variant.stock_quantity < quantity:
                    raise serializers.ValidationError("Insufficient stock for variant")
            except ProductVariant.DoesNotExist:
                raise serializers.ValidationError("Product variant not found")
        else:
            if product.track_inventory and product.stock_quantity < quantity:
                raise serializers.ValidationError("Insufficient stock")
        
        return data


class CartSerializer(serializers.ModelSerializer):
    items = CartItemSerializer(many=True, read_only=True)
    
    class Meta:
        model = Cart
        fields = [
            'id', 'total_items', 'total_price', 'items', 
            'created_at', 'updated_at'
        ]
        read_only_fields = ['total_items', 'total_price', 'created_at', 'updated_at']


class OrderItemSerializer(serializers.ModelSerializer):
    class Meta:
        model = OrderItem
        fields = [
            'id', 'product', 'variant', 'quantity', 'unit_price',
            'total_price', 'product_name', 'product_sku', 'variant_name'
        ]


class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)
    customer_name = serializers.CharField(source='customer.get_full_name', read_only=True)
    
    class Meta:
        model = Order
        fields = [
            'id', 'order_number', 'customer', 'customer_name', 'status',
            'payment_status', 'subtotal', 'tax_amount', 'shipping_amount',
            'discount_amount', 'total_amount', 'billing_address',
            'shipping_address', 'notes', 'tracking_number', 'items',
            'created_at', 'updated_at', 'shipped_at', 'delivered_at'
        ]
        read_only_fields = [
            'order_number', 'customer_name', 'created_at', 'updated_at'
        ]


class OrderCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating orders"""
    cart_id = serializers.UUIDField(write_only=True)
    coupon_code = serializers.CharField(write_only=True, required=False)
    
    class Meta:
        model = Order
        fields = [
            'billing_address', 'shipping_address', 'notes',
            'cart_id', 'coupon_code'
        ]
    
    def validate_cart_id(self, value):
        request = self.context.get('request')
        try:
            cart = Cart.objects.get(id=value)
            if request.user.is_authenticated:
                if cart.customer != request.user:
                    raise serializers.ValidationError("Cart does not belong to user")
            else:
                session_key = request.session.session_key
                if cart.session_key != session_key:
                    raise serializers.ValidationError("Cart does not belong to session")
            
            if not cart.items.exists():
                raise serializers.ValidationError("Cart is empty")
            
            return value
        except Cart.DoesNotExist:
            raise serializers.ValidationError("Cart not found")
    
    def validate_coupon_code(self, value):
        if value:
            try:
                coupon = Coupon.objects.get(code=value)
                if not coupon.is_valid:
                    raise serializers.ValidationError("Coupon is not valid")
                return value
            except Coupon.DoesNotExist:
                raise serializers.ValidationError("Coupon not found")
        return value


class ReviewSerializer(serializers.ModelSerializer):
    customer_name = serializers.CharField(source='customer.get_full_name', read_only=True)
    
    class Meta:
        model = Review
        fields = [
            'id', 'product', 'customer', 'customer_name', 'rating',
            'title', 'comment', 'is_verified_purchase', 'is_approved',
            'created_at', 'updated_at'
        ]
        read_only_fields = [
            'customer', 'customer_name', 'is_verified_purchase',
            'is_approved', 'created_at', 'updated_at'
        ]


class CouponSerializer(serializers.ModelSerializer):
    class Meta:
        model = Coupon
        fields = [
            'id', 'code', 'name', 'description', 'discount_type',
            'discount_value', 'minimum_order_amount', 'maximum_discount_amount',
            'usage_limit', 'used_count', 'is_active', 'valid_from',
            'valid_until', 'is_valid'
        ]
        read_only_fields = ['used_count', 'is_valid']


class WishlistItemSerializer(serializers.ModelSerializer):
    product = ProductListSerializer(read_only=True)
    product_id = serializers.UUIDField(write_only=True)
    
    class Meta:
        model = WishlistItem
        fields = ['id', 'product', 'product_id', 'added_at']
        read_only_fields = ['added_at']


class WishlistSerializer(serializers.ModelSerializer):
    items = WishlistItemSerializer(many=True, read_only=True)
    item_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Wishlist
        fields = [
            'id', 'name', 'is_default', 'is_public', 'items',
            'item_count', 'created_at'
        ]
        read_only_fields = ['created_at']
    
    def get_item_count(self, obj):
        return obj.items.count()


class UserSerializer(serializers.ModelSerializer):
    """Basic user serializer for order/review purposes"""
    class Meta:
        model = User
        fields = ['id', 'username', 'first_name', 'last_name', 'email']
        read_only_fields = ['username']