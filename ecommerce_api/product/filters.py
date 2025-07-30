

import django_filters
from django.db import models
from .models import Product, Category, Brand


class ProductFilter(django_filters.FilterSet):
    """
    Filter class for products with various filtering options
    """
    # Price range filters
    min_price = django_filters.NumberFilter(field_name="price", lookup_expr='gte')
    max_price = django_filters.NumberFilter(field_name="price", lookup_expr='lte')
    price_range = django_filters.RangeFilter(field_name="price")
    
    # Category filters
    category = django_filters.ModelChoiceFilter(queryset=Category.objects.filter(is_active=True))
    category_slug = django_filters.CharFilter(field_name="category__slug")
    
    # Brand filters
    brand = django_filters.ModelChoiceFilter(queryset=Brand.objects.filter(is_active=True))
    brand_slug = django_filters.CharFilter(field_name="brand__slug")
    
    # Stock status
    stock_status = django_filters.ChoiceFilter(choices=Product.STOCK_STATUS_CHOICES)
    in_stock = django_filters.BooleanFilter(method='filter_in_stock')
    
    # Product attributes
    is_featured = django_filters.BooleanFilter()
    is_digital = django_filters.BooleanFilter()
    is_on_sale = django_filters.BooleanFilter(method='filter_on_sale')
    
    # Rating filter
    min_rating = django_filters.NumberFilter(field_name="average_rating", lookup_expr='gte')
    
    # Date filters
    created_after = django_filters.DateTimeFilter(field_name="created_at", lookup_expr='gte')
    created_before = django_filters.DateTimeFilter(field_name="created_at", lookup_expr='lte')
    
    # Text search in multiple fields
    search = django_filters.CharFilter(method='filter_search')
    
    class Meta:
        model = Product
        fields = {
            'name': ['icontains'],
            'sku': ['exact', 'icontains'],
            'price': ['exact', 'lt', 'gt', 'lte', 'gte'],
            'average_rating': ['exact', 'lt', 'gt', 'lte', 'gte'],
            'is_active': ['exact'],
            'is_featured': ['exact'],
            'is_digital': ['exact'],
            'track_inventory': ['exact'],
        }
    
    def filter_in_stock(self, queryset, name, value):
        """Filter products that are in stock"""
        if value:
            return queryset.filter(
                models.Q(track_inventory=False) |
                models.Q(track_inventory=True, stock_quantity__gt=0)
            ).exclude(stock_status='out_of_stock')
        return queryset
    
    def filter_on_sale(self, queryset, name, value):
        """Filter products that are on sale"""
        if value:
            return queryset.filter(
                compare_price__isnull=False,
                price__lt=models.F('compare_price')
            )
        return queryset
    
    def filter_search(self, queryset, name, value):
        """Search across multiple fields"""
        if value:
            return queryset.filter(
                models.Q(name__icontains=value) |
                models.Q(description__icontains=value) |
                models.Q(short_description__icontains=value) |
                models.Q(sku__icontains=value) |
                models.Q(category__name__icontains=value) |
                models.Q(brand__name__icontains=value)
            )
        return queryset


class CategoryFilter(django_filters.FilterSet):
    """Filter class for categories"""
    parent = django_filters.ModelChoiceFilter(queryset=Category.objects.filter(is_active=True))
    parent_slug = django_filters.CharFilter(field_name="parent__slug")
    has_parent = django_filters.BooleanFilter(method='filter_has_parent')
    
    class Meta:
        model = Category
        fields = {
            'name': ['icontains'],
            'is_active': ['exact'],
        }
    
    def filter_has_parent(self, queryset, name, value):
        """Filter categories that have or don't have a parent"""
        if value:
            return queryset.filter(parent__isnull=False)
        else:
            return queryset.filter(parent__isnull=True)


class BrandFilter(django_filters.FilterSet):
    """Filter class for brands"""
    
    class Meta:
        model = Brand
        fields = {
            'name': ['icontains'],
            'is_active': ['exact'],
        }