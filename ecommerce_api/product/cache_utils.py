
from django.core.cache import cache
from django.conf import settings
from functools import wraps
import hashlib
import json


class CacheKeyGenerator:
    """Utility class for generating cache keys"""
    
    @staticmethod
    def product_list_key(filters=None, ordering=None, page=1):
        """Generate cache key for product listings"""
        key_parts = ['product_list']
        
        if filters:
            # Sort filters for consistent key generation
            filter_str = json.dumps(sorted(filters.items()))
            filter_hash = hashlib.md5(filter_str.encode()).hexdigest()
            key_parts.append(f'filters_{filter_hash}')
        
        if ordering:
            key_parts.append(f'order_{ordering}')
        
        key_parts.append(f'page_{page}')
        
        return '_'.join(key_parts)
    
    @staticmethod
    def product_detail_key(product_slug):
        """Generate cache key for product detail"""
        return f'product_detail_{product_slug}'
    
    @staticmethod
    def category_products_key(category_slug, filters=None, page=1):
        """Generate cache key for category products"""
        key_parts = [f'category_{category_slug}_products']
        
        if filters:
            filter_str = json.dumps(sorted(filters.items()))
            filter_hash = hashlib.md5(filter_str.encode()).hexdigest()
            key_parts.append(f'filters_{filter_hash}')
        
        key_parts.append(f'page_{page}')
        
        return '_'.join(key_parts)
    
    @staticmethod
    def brand_products_key(brand_slug, filters=None, page=1):
        """Generate cache key for brand products"""
        key_parts = [f'brand_{brand_slug}_products']
        
        if filters:
            filter_str = json.dumps(sorted(filters.items()))
            filter_hash = hashlib.md5(filter_str.encode()).hexdigest()
            key_parts.append(f'filters_{filter_hash}')
        
        key_parts.append(f'page_{page}')
        
        return '_'.join(key_parts)


def cache_response(timeout=300, key_func=None):
    """
    Decorator for caching API responses
    
    Args:
        timeout: Cache timeout in seconds (default: 5 minutes)
        key_func: Function to generate cache key (optional)
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(self, request, *args, **kwargs):
            # Generate cache key
            if key_func:
                cache_key = key_func(request, *args, **kwargs)
            else:
                # Default key generation
                cache_key = f"{view_func.__name__}_{hash(str(request.GET))}"
            
            # Try to get from cache
            cached_response = cache.get(cache_key)
            if cached_response:
                return cached_response
            
            # Execute view and cache response
            response = view_func(self, request, *args, **kwargs)
            cache.set(cache_key, response, timeout)
            
            return response
        return wrapper
    return decorator


class CacheInvalidator:
    """Utility class for cache invalidation"""
    
    @staticmethod
    def invalidate_product_caches(product):
        """Invalidate all caches related to a product"""
        # Product detail cache
        cache.delete(f'product_detail_{product.slug}')
        
        # Category product caches
        cache.delete_many([
            f'category_{product.category.slug}_products*',
            'featured_products',
            'product_list*'
        ])
        
        # Brand product caches if product has brand
        if product.brand:
            cache.delete_many([
                f'brand_{product.brand.slug}_products*'
            ])
    
    @staticmethod
    def invalidate_category_caches(category):
        """Invalidate all caches related to a category"""
        cache.delete_many([
            f'category_{category.slug}_products*',
            'categories_list'
        ])
    
    @staticmethod
    def invalidate_brand_caches(brand):
        """Invalidate all caches related to a brand"""
        cache.delete_many([
            f'brand_{brand.slug}_products*',
            'brands_list'
        ])