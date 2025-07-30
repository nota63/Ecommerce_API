from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from .models import (
    Category, Brand, Product, ProductImage, ProductVariant,
    AttributeName, AttributeValue, ProductAttribute,
    Cart, CartItem, Order, OrderItem, Review, Coupon,
    Wishlist, WishlistItem
)


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'parent', 'is_active', 'product_count', 'created_at']
    list_filter = ['is_active', 'parent', 'created_at']
    search_fields = ['name', 'description']
    prepopulated_fields = {'slug': ('name',)}
    list_editable = ['is_active']
    ordering = ['name']
    
    def product_count(self, obj):
        return obj.products.count()
    product_count.short_description = 'Products'


@admin.register(Brand)
class BrandAdmin(admin.ModelAdmin):
    list_display = ['name', 'website', 'is_active', 'product_count', 'created_at']
    list_filter = ['is_active', 'created_at']
    search_fields = ['name', 'description']
    prepopulated_fields = {'slug': ('name',)}
    list_editable = ['is_active']
    
    def product_count(self, obj):
        return obj.products.count()
    product_count.short_description = 'Products'


class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 1
    fields = ['image', 'alt_text', 'is_primary', 'sort_order']
    readonly_fields = ['image_preview']
    
    def image_preview(self, obj):
        if obj.image:
            return format_html('<img src="{}" width="100" height="100" />', obj.image.url)
        return "No Image"
    image_preview.short_description = 'Preview'


class ProductVariantInline(admin.TabularInline):
    model = ProductVariant
    extra = 0
    fields = ['name', 'sku', 'price', 'stock_quantity', 'is_active']


class ProductAttributeInline(admin.TabularInline):
    model = ProductAttribute
    extra = 1
    autocomplete_fields = ['attribute_value']


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = [
        'name', 'category', 'brand', 'price', 'stock_quantity', 
        'stock_status', 'is_active', 'is_featured', 'average_rating'
    ]
    list_filter = [
        'category', 'brand', 'stock_status', 'is_active', 
        'is_featured', 'is_digital', 'created_at'
    ]
    search_fields = ['name', 'sku', 'description']
    prepopulated_fields = {'slug': ('name',)}
    list_editable = ['is_active', 'is_featured', 'stock_status']
    readonly_fields = ['id', 'average_rating', 'total_reviews', 'created_at', 'updated_at']
    autocomplete_fields = ['category', 'brand']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'slug', 'description', 'short_description', 'category', 'brand')
        }),
        ('Pricing', {
            'fields': ('price', 'compare_price', 'cost_price')
        }),
        ('Inventory', {
            'fields': ('sku', 'barcode', 'stock_quantity', 'min_stock_level', 'stock_status', 'track_inventory')
        }),
        ('Physical Attributes', {
            'fields': ('weight', 'length', 'width', 'height'),
            'classes': ('collapse',)
        }),
        ('SEO', {
            'fields': ('meta_title', 'meta_description'),
            'classes': ('collapse',)
        }),
        ('Status & Settings', {
            'fields': ('is_active', 'is_featured', 'is_digital', 'requires_shipping')
        }),
        ('Reviews & Rating', {
            'fields': ('average_rating', 'total_reviews'),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at', 'published_at'),
            'classes': ('collapse',)
        }),
    )
    
    inlines = [ProductImageInline, ProductVariantInline, ProductAttributeInline]
    
    actions = ['make_active', 'make_inactive', 'make_featured', 'remove_featured']
    
    def make_active(self, request, queryset):
        queryset.update(is_active=True)
    make_active.short_description = "Mark selected products as active"
    
    def make_inactive(self, request, queryset):
        queryset.update(is_active=False)
    make_inactive.short_description = "Mark selected products as inactive"
    
    def make_featured(self, request, queryset):
        queryset.update(is_featured=True)
    make_featured.short_description = "Mark selected products as featured"
    
    def remove_featured(self, request, queryset):
        queryset.update(is_featured=False)
    remove_featured.short_description = "Remove featured status from selected products"


@admin.register(ProductImage)
class ProductImageAdmin(admin.ModelAdmin):
    list_display = ['product', 'alt_text', 'is_primary', 'sort_order', 'image_preview']
    list_filter = ['is_primary', 'created_at']
    search_fields = ['product__name', 'alt_text']
    list_editable = ['is_primary', 'sort_order']
    autocomplete_fields = ['product']
    
    def image_preview(self, obj):
        if obj.image:
            return format_html('<img src="{}" width="50" height="50" />', obj.image.url)
        return "No Image"
    image_preview.short_description = 'Preview'


@admin.register(ProductVariant)
class ProductVariantAdmin(admin.ModelAdmin):
    list_display = ['product', 'name', 'sku', 'price', 'stock_quantity', 'is_active']
    list_filter = ['is_active', 'created_at']
    search_fields = ['product__name', 'name', 'sku']
    list_editable = ['price', 'stock_quantity', 'is_active']
    autocomplete_fields = ['product']


@admin.register(AttributeName)
class AttributeNameAdmin(admin.ModelAdmin):
    list_display = ['name', 'display_name', 'is_required', 'value_count']
    search_fields = ['name', 'display_name']
    list_editable = ['is_required']
    
    def value_count(self, obj):
        return obj.values.count()
    value_count.short_description = 'Values'


@admin.register(AttributeValue)
class AttributeValueAdmin(admin.ModelAdmin):
    list_display = ['attribute_name', 'value', 'created_at']
    list_filter = ['attribute_name', 'created_at']
    search_fields = ['attribute_name__name', 'value']
    autocomplete_fields = ['attribute_name']


@admin.register(ProductAttribute)
class ProductAttributeAdmin(admin.ModelAdmin):
    list_display = ['product', 'attribute_value', 'created_at']
    list_filter = ['attribute_value__attribute_name', 'created_at']
    search_fields = ['product__name', 'attribute_value__value']
    autocomplete_fields = ['product', 'attribute_value']


class CartItemInline(admin.TabularInline):
    model = CartItem
    extra = 0
    readonly_fields = ['unit_price', 'total_price']
    autocomplete_fields = ['product', 'variant']


@admin.register(Cart)
class CartAdmin(admin.ModelAdmin):
    list_display = ['id', 'customer', 'total_items', 'total_price', 'created_at']
    list_filter = ['created_at', 'updated_at']
    search_fields = ['customer__username', 'customer__email', 'session_key']
    readonly_fields = ['id', 'total_items', 'total_price', 'created_at', 'updated_at']
    
    inlines = [CartItemInline]


@admin.register(CartItem)
class CartItemAdmin(admin.ModelAdmin):
    list_display = ['cart', 'product', 'variant', 'quantity', 'unit_price', 'total_price']
    list_filter = ['created_at', 'updated_at']
    search_fields = ['product__name', 'cart__customer__username']
    readonly_fields = ['unit_price', 'total_price']
    autocomplete_fields = ['cart', 'product', 'variant']


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0
    readonly_fields = ['total_price']
    fields = ['product', 'variant', 'quantity', 'unit_price', 'total_price', 'product_name', 'variant_name']


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = [
        'order_number', 'customer', 'status', 'payment_status', 
        'total_amount', 'created_at'
    ]
    list_filter = ['status', 'payment_status', 'created_at', 'shipped_at', 'delivered_at']
    search_fields = ['order_number', 'customer__username', 'customer__email', 'tracking_number']
    readonly_fields = ['id', 'order_number', 'created_at', 'updated_at']
    list_editable = ['status', 'payment_status']
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Order Information', {
            'fields': ('order_number', 'customer', 'status', 'payment_status')
        }),
        ('Pricing', {
            'fields': ('subtotal', 'tax_amount', 'shipping_amount', 'discount_amount', 'total_amount')
        }),
        ('Addresses', {
            'fields': ('billing_address', 'shipping_address'),
            'classes': ('collapse',)
        }),
        ('Shipping', {
            'fields': ('tracking_number', 'shipped_at', 'delivered_at'),
            'classes': ('collapse',)
        }),
        ('Additional Information', {
            'fields': ('notes',),
            'classes': ('collapse',)
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    inlines = [OrderItemInline]
    
    actions = ['mark_as_confirmed', 'mark_as_shipped', 'mark_as_delivered']
    
    def mark_as_confirmed(self, request, queryset):
        queryset.update(status='confirmed')
    mark_as_confirmed.short_description = "Mark selected orders as confirmed"
    
    def mark_as_shipped(self, request, queryset):
        from django.utils import timezone
        queryset.update(status='shipped', shipped_at=timezone.now())
    mark_as_shipped.short_description = "Mark selected orders as shipped"
    
    def mark_as_delivered(self, request, queryset):
        from django.utils import timezone
        queryset.update(status='delivered', delivered_at=timezone.now())
    mark_as_delivered.short_description = "Mark selected orders as delivered"


@admin.register(OrderItem)
class OrderItemAdmin(admin.ModelAdmin):
    list_display = ['order', 'product_name', 'variant_name', 'quantity', 'unit_price', 'total_price']
    list_filter = ['order__status', 'order__created_at']
    search_fields = ['order__order_number', 'product_name', 'product_sku']
    readonly_fields = ['total_price']
    autocomplete_fields = ['order', 'product', 'variant']


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = [
        'product', 'customer', 'rating', 'title', 
        'is_verified_purchase', 'is_approved', 'created_at'
    ]
    list_filter = [
        'rating', 'is_verified_purchase', 'is_approved', 'created_at'
    ]
    search_fields = ['product__name', 'customer__username', 'title', 'comment']
    list_editable = ['is_approved']
    readonly_fields = ['is_verified_purchase', 'created_at', 'updated_at']
    autocomplete_fields = ['product', 'customer', 'order_item']
    
    actions = ['approve_reviews', 'disapprove_reviews']
    
    def approve_reviews(self, request, queryset):
        queryset.update(is_approved=True)
    approve_reviews.short_description = "Approve selected reviews"
    
    def disapprove_reviews(self, request, queryset):
        queryset.update(is_approved=False)
    disapprove_reviews.short_description = "Disapprove selected reviews"


@admin.register(Coupon)
class CouponAdmin(admin.ModelAdmin):
    list_display = [
        'code', 'name', 'discount_type', 'discount_value', 
        'usage_limit', 'used_count', 'is_active', 'valid_from', 'valid_until'
    ]
    list_filter = ['discount_type', 'is_active', 'valid_from', 'valid_until', 'created_at']
    search_fields = ['code', 'name', 'description']
    list_editable = ['is_active']
    readonly_fields = ['used_count', 'is_valid', 'created_at']
    date_hierarchy = 'valid_from'
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('code', 'name', 'description')
        }),
        ('Discount Settings', {
            'fields': ('discount_type', 'discount_value', 'minimum_order_amount', 'maximum_discount_amount')
        }),
        ('Usage Limits', {
            'fields': ('usage_limit', 'used_count')
        }),
        ('Validity', {
            'fields': ('is_active', 'valid_from', 'valid_until', 'is_valid')
        }),
        ('Timestamps', {
            'fields': ('created_at',),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['activate_coupons', 'deactivate_coupons']
    
    def activate_coupons(self, request, queryset):
        queryset.update(is_active=True)
    activate_coupons.short_description = "Activate selected coupons"
    
    def deactivate_coupons(self, request, queryset):
        queryset.update(is_active=False)
    deactivate_coupons.short_description = "Deactivate selected coupons"


class WishlistItemInline(admin.TabularInline):
    model = WishlistItem
    extra = 0
    autocomplete_fields = ['product']


@admin.register(Wishlist)
class WishlistAdmin(admin.ModelAdmin):
    list_display = ['customer', 'name', 'is_default', 'is_public', 'item_count', 'created_at']
    list_filter = ['is_default', 'is_public', 'created_at']
    search_fields = ['customer__username', 'customer__email', 'name']
    list_editable = ['is_public']
    autocomplete_fields = ['customer']
    
    inlines = [WishlistItemInline]
    
    def item_count(self, obj):
        return obj.items.count()
    item_count.short_description = 'Items'


@admin.register(WishlistItem)
class WishlistItemAdmin(admin.ModelAdmin):
    list_display = ['wishlist', 'product', 'added_at']
    list_filter = ['added_at']
    search_fields = ['wishlist__customer__username', 'product__name']
    autocomplete_fields = ['wishlist', 'product']


# Custom admin site configurations
admin.site.site_header = "E-Commerce Admin"
admin.site.site_title = "E-Commerce Admin Portal"
admin.site.index_title = "Welcome to E-Commerce Administration"