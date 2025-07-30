from django.db import models
from django.db.models import Prefetch
from .models import *



#  Database query optimization utilities

class ProductQueryOptimizer:
    """Utility class for optimizing product queries"""
    
    @staticmethod
    def get_optimized_product_list_queryset():
        """Get optimized queryset for product listings"""
        return Product.objects.select_related(
            'category', 'brand'
        ).prefetch_related(
            Prefetch(
                'images',
                queryset=ProductImage.objects.filter(is_primary=True),
                to_attr='primary_images'
            )
        ).filter(is_active=True)
    
    @staticmethod
    def get_optimized_product_detail_queryset():
        """Get optimized queryset for product detail"""
        return Product.objects.select_related(
            'category', 'brand'
        ).prefetch_related(
            'images',
            'variants',
            'attributes__attribute_value__attribute_name',
            Prefetch(
                'reviews',
                queryset=Review.objects.filter(
                    is_approved=True
                ).select_related('customer')[:10],
                to_attr='recent_reviews'
            )
        ).filter(is_active=True)