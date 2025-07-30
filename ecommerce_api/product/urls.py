
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

# router and register viewsets
router = DefaultRouter()
router.register(r'categories', views.CategoryViewSet)
router.register(r'brands', views.BrandViewSet)
router.register(r'products', views.ProductViewSet)
router.register(r'cart', views.CartViewSet, basename='cart')
router.register(r'orders', views.OrderViewSet, basename='order')
router.register(r'reviews', views.ReviewViewSet, basename='review')
router.register(r'wishlists', views.WishlistViewSet, basename='wishlist')
router.register(r'coupons', views.CouponViewSet)


urlpatterns = [
    path('api/v1/', include(router.urls)),
]