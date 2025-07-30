from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from .models import Product, Category, Brand, ProductImage, Review
from .cache_utils import CacheInvalidator


@receiver(post_save, sender=Product)
def invalidate_product_cache_on_save(sender, instance, **kwargs):
    """Invalidate product-related caches when product is saved"""
    CacheInvalidator.invalidate_product_caches(instance)


@receiver(post_delete, sender=Product)
def invalidate_product_cache_on_delete(sender, instance, **kwargs):
    """Invalidate product-related caches when product is deleted"""
    CacheInvalidator.invalidate_product_caches(instance)


@receiver(post_save, sender=Category)
def invalidate_category_cache_on_save(sender, instance, **kwargs):
    """Invalidate category-related caches when category is saved"""
    CacheInvalidator.invalidate_category_caches(instance)


@receiver(post_save, sender=Brand)
def invalidate_brand_cache_on_save(sender, instance, **kwargs):
    """Invalidate brand-related caches when brand is saved"""
    CacheInvalidator.invalidate_brand_caches(instance)


@receiver(post_save, sender=ProductImage)
def invalidate_product_image_cache(sender, instance, **kwargs):
    """Invalidate product caches when product image is updated"""
    CacheInvalidator.invalidate_product_caches(instance.product)


@receiver(post_save, sender=Review)
def invalidate_review_cache(sender, instance, **kwargs):
    """Invalidate product caches when review is updated"""
    CacheInvalidator.invalidate_product_caches(instance.product)
