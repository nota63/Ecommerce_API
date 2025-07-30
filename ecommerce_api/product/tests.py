from django.test import TestCase
from django.contrib.auth.models import User
from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status
import json

from .models import Category, Brand, Product, Cart, CartItem, Order


class ProductAPITestCase(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        self.category = Category.objects.create(
            name='Electronics',
            slug='electronics'
        )
        
        self.brand = Brand.objects.create(
            name='Apple',
            slug='apple'
        )
        
        self.product = Product.objects.create(
            name='iPhone 15',
            slug='iphone-15',
            description='Latest iPhone',
            category=self.category,
            brand=self.brand,
            price=999.99,
            sku='IPHONE15-001',
            stock_quantity=10
        )
    
    def test_product_list(self):
        """Test product listing endpoint"""
        url = reverse('product-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
        self.assertEqual(response.data['results'][0]['name'], 'iPhone 15')
    
    def test_product_detail(self):
        """Test product detail endpoint"""
        url = reverse('product-detail', kwargs={'slug': 'iphone-15'})
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['name'], 'iPhone 15')
        self.assertEqual(response.data['price'], '999.99')
    
    def test_product_filtering(self):
        """Test product filtering"""
        url = reverse('product-list')
        response = self.client.get(url, {'category': self.category.id})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)
    
    def test_product_search(self):
        """Test product search"""
        url = reverse('product-list')
        response = self.client.get(url, {'search': 'iPhone'})
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(len(response.data['results']), 1)


class CartAPITestCase(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        self.category = Category.objects.create(
            name='Electronics',
            slug='electronics'
        )
        
        self.product = Product.objects.create(
            name='iPhone 15',
            slug='iphone-15',
            description='Latest iPhone',
            category=self.category,
            price=999.99,
            sku='IPHONE15-001',
            stock_quantity=10
        )
    
    def test_add_to_cart_authenticated(self):
        """Test adding item to cart for authenticated user"""
        self.client.force_authenticate(user=self.user)
        
        url = reverse('cart-add-item')
        data = {
            'product_id': str(self.product.id),
            'quantity': 2
        }
        response = self.client.post(url, data)
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['quantity'], 2)
    
    def test_add_to_cart_anonymous(self):
        """Test adding item to cart for anonymous user"""
        # Create session
        session = self.client.session
        session.create()
        
        url = reverse('cart-add-item')
        data = {
            'product_id': str(self.product.id),
            'quantity': 1
        }
        response = self.client.post(url, data)
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertEqual(response.data['quantity'], 1)
    
    def test_cart_total_calculation(self):
        """Test cart total calculation"""
        self.client.force_authenticate(user=self.user)
        
        # Add item to cart
        cart = Cart.objects.create(customer=self.user)
        CartItem.objects.create(
            cart=cart,
            product=self.product,
            quantity=2
        )
        
        url = reverse('cart-list')
        response = self.client.get(url)
        
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(float(response.data['total_price']), 1999.98)


class OrderAPITestCase(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            username='testuser',
            email='test@example.com',
            password='testpass123'
        )
        
        self.category = Category.objects.create(
            name='Electronics',
            slug='electronics'
        )
        
        self.product = Product.objects.create(
            name='iPhone 15',
            slug='iphone-15',
            description='Latest iPhone',
            category=self.category,
            price=999.99,
            sku='IPHONE15-001',
            stock_quantity=10
        )
        
        # Create cart with items
        self.cart = Cart.objects.create(customer=self.user)
        CartItem.objects.create(
            cart=self.cart,
            product=self.product,
            quantity=1
        )
    
    def test_create_order(self):
        """Test order creation"""
        self.client.force_authenticate(user=self.user)
        
        url = reverse('order-list')
        data = {
            'cart_id': str(self.cart.id),
            'billing_address': {
                'name': 'John Doe',
                'address': '123 Main St',
                'city': 'New York',
                'zip_code': '10001'
            },
            'shipping_address': {
                'name': 'John Doe',
                'address': '123 Main St',
                'city': 'New York',
                'zip_code': '10001'
            }
        }
        response = self.client.post(url, data, format='json')
        
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertTrue(response.data['order_number'])
        self.assertEqual(response.data['status'], 'pending')