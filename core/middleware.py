"""
Custom middleware for Akili platform
"""
import time
import logging
from django.core.cache import caches
from django.http import HttpResponse
from django.conf import settings

logger = logging.getLogger(__name__)

ratelimit_cache = caches['ratelimit']


def get_client_ip(request):
    """Extract client IP from request, handling proxies"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        return x_forwarded_for.split(',')[0].strip()
    return request.META.get('REMOTE_ADDR', 'unknown')


class RateLimitMiddleware:
    """
    Rate limiting middleware using database cache (works across workers).
    - Authenticated users: 10 requests per minute per endpoint
    - Anonymous users: 30 requests per minute per IP (global)
    Uses database cache backend for multi-worker safety.
    """
    
    RATE_LIMITS = {
        'authenticated': {'requests': 10, 'window': 60},
        'anonymous': {'requests': 30, 'window': 60},
    }
    
    RATE_LIMITED_PATHS = [
        '/courses/create',
        '/courses/ask-tutor',
        '/login/',
        '/signup/',
        '/password-reset/',
    ]
    
    def __init__(self, get_response):
        self.get_response = get_response
        
    def __call__(self, request):
        for path in self.RATE_LIMITED_PATHS:
            if request.path.startswith(path):
                is_limited, response = self._check_rate_limit(request, path)
                if is_limited:
                    return response
                break
        
        return self.get_response(request)
    
    def _check_rate_limit(self, request, path):
        """Check and update rate limit, returns (is_limited, response)"""
        try:
            if request.user.is_authenticated:
                cache_key = f'rl_user_{request.user.id}_{path.replace("/", "_")}'
                limits = self.RATE_LIMITS['authenticated']
            else:
                client_ip = get_client_ip(request)
                cache_key = f'rl_ip_{client_ip}_{path.replace("/", "_")}'
                limits = self.RATE_LIMITS['anonymous']
            
            current_time = time.time()
            request_data = ratelimit_cache.get(cache_key)
            
            if request_data is None:
                request_data = {'count': 1, 'timestamp': current_time}
            else:
                time_diff = current_time - request_data.get('timestamp', 0)
                if time_diff > limits['window']:
                    request_data = {'count': 1, 'timestamp': current_time}
                else:
                    request_data['count'] = request_data.get('count', 0) + 1
            
            if request_data['count'] > limits['requests']:
                logger.warning(f"Rate limit exceeded: {cache_key}")
                response = HttpResponse(
                    'Rate limit exceeded. Please wait a minute before trying again.',
                    status=429
                )
                response['Retry-After'] = str(limits['window'])
                return True, response
            
            ratelimit_cache.set(cache_key, request_data, limits['window'])
            return False, None
            
        except Exception as e:
            logger.error(f"Rate limit check failed: {e}")
            return False, None


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
