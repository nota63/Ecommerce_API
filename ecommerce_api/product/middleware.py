from django.utils.cache import get_cache_key
from django.core.cache import cache
from django.http import HttpResponse
import json
import hashlib

class APICacheMiddleware:
    """
    Custom middleware for API response caching
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
    
    def __call__(self, request):
        # Check if this is an API request
        if request.path.startswith('/api/'):
            # Try to get cached response for GET requests
            if request.method == 'GET':
                cache_key = self.get_api_cache_key(request)
                cached_response = cache.get(cache_key)
                
                if cached_response:
                    response = HttpResponse(
                        cached_response['content'],
                        content_type=cached_response['content_type'],
                        status=cached_response['status_code']
                    )
                    response['X-Cache'] = 'HIT'
                    return response
        
        response = self.get_response(request)
        
        # Cache successful GET responses
        if (request.path.startswith('/api/') and 
            request.method == 'GET' and 
            response.status_code == 200):
            
            cache_key = self.get_api_cache_key(request)
            cache_data = {
                'content': response.content.decode('utf-8'),
                'content_type': response.get('Content-Type', 'application/json'),
                'status_code': response.status_code
            }
            
            # Cache for 5 minutes by default
            cache.set(cache_key, cache_data, 300)
            response['X-Cache'] = 'MISS'
        
        return response
    
    def get_api_cache_key(self, request):
        """Generate cache key for API request"""
        key_parts = [
            request.path,
            request.GET.urlencode()
        ]
        
        if hasattr(request, 'user') and request.user.is_authenticated:
            key_parts.append(f'user_{request.user.id}')
        
        return hashlib.md5('_'.join(key_parts).encode()).hexdigest()

