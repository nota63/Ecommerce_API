from django.core.management.base import BaseCommand
from django.core.cache import cache
from product.models import Product, Category, Brand
from product.serializers import ProductListSerializer, CategorySerializer, BrandSerializer


class Command(BaseCommand):
    help = 'Warm up cache with frequently accessed data'
    
    def handle(self, *args, **options):
        self.stdout.write('Starting cache warmup...')
        
        # Cache featured products
        featured_products = Product.objects.filter(
            is_featured=True, 
            is_active=True
        ).select_related('category', 'brand')[:10]
        
        serialized_data = ProductListSerializer(featured_products, many=True).data
        cache.set('featured_products', serialized_data, 1800)  # 30 minutes
        
        # Cache categories
        categories = Category.objects.filter(is_active=True, parent=None)
        serialized_categories = CategorySerializer(categories, many=True).data
        cache.set('categories_list', serialized_categories, 900)  # 15 minutes
        
        # Cache brands
        brands = Brand.objects.filter(is_active=True)[:20]
        serialized_brands = BrandSerializer(brands, many=True).data
        cache.set('brands_list', serialized_brands, 900)  # 15 minutes
        
        self.stdout.write(
            self.style.SUCCESS('Cache warmup completed successfully!')
        )
