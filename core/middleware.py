"""
Custom middleware for Akili platform
"""
import time
from django.core.cache import cache
from django.http import HttpResponseForbidden
from django.conf import settings


class RateLimitMiddleware:
    """
    Simple rate limiting middleware for credit-consuming endpoints
    Limits: 10 requests per minute per user for expensive operations
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        
    def __call__(self, request):
        # Only rate limit authenticated users on specific paths
        if request.user.is_authenticated:
            rate_limited_paths = [
                '/courses/create',
                '/exams/start',
                '/courses/ask-tutor',
            ]
            
            # Check if the current path matches any rate-limited endpoint
            for path in rate_limited_paths:
                if request.path.startswith(path):
                    # Create a unique cache key for this user and endpoint
                    cache_key = f'rate_limit_{request.user.id}_{path}'
                    
                    # Get request count and timestamp
                    request_data = cache.get(cache_key, {'count': 0, 'timestamp': time.time()})
                    
                    current_time = time.time()
                    time_diff = current_time - request_data['timestamp']
                    
                    # Reset counter if more than 60 seconds have passed
                    if time_diff > 60:
                        request_data = {'count': 1, 'timestamp': current_time}
                    else:
                        request_data['count'] += 1
                    
                    # Check if user exceeded rate limit
                    if request_data['count'] > 10:
                        return HttpResponseForbidden('Rate limit exceeded. Please wait a minute before trying again.')
                    
                    # Update cache
                    cache.set(cache_key, request_data, 60)
        
        response = self.get_response(request)
        return response


class ErrorLoggingMiddleware:
    """
    Middleware to log errors and add request context
    """
    
    def __init__(self, get_response):
        self.get_response = get_response
        
    def __call__(self, request):
        response = self.get_response(request)
        return response
    
    def process_exception(self, request, exception):
        """Log exceptions with user and request context"""
        import logging
        logger = logging.getLogger(__name__)
        
        user_info = 'Anonymous'
        if request.user.is_authenticated:
            user_info = f'User {request.user.id} ({request.user.email})'
        
        logger.error(
            f'Exception for {user_info} at {request.path}: {str(exception)}',
            exc_info=True,
            extra={
                'user': user_info,
                'path': request.path,
                'method': request.method,
            }
        )
        return None  # Let Django's default handler take over
