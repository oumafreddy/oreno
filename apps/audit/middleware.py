from django.http import JsonResponse
import re
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

class NotificationAPIMiddleware:
    """
    Middleware to gracefully handle unauthenticated requests to the notifications API
    by returning an empty array instead of redirecting to the login page.
    """
    def __init__(self, get_response):
        self.get_response = get_response
        # Define the patterns for API endpoints that should return empty results when not authenticated
        self.api_patterns = [
            re.compile(r'^/audit/api/notifications'),
            re.compile(r'^/api/audit/notifications'),
        ]

    def __call__(self, request):
        # Build the full URL path including query string
        full_path = request.path_info
        if request.META.get('QUERY_STRING'):
            full_path += '?' + request.META.get('QUERY_STRING')
        
        # Check if this matches any of our API patterns
        is_api_request = any(pattern.match(request.path_info) for pattern in self.api_patterns)
        is_json_request = request.META.get('HTTP_ACCEPT', '').find('application/json') != -1 or 'format=json' in full_path
        
        # If it's a JSON API request and user is not authenticated
        if is_api_request and is_json_request and not request.user.is_authenticated:
            if settings.DEBUG:
                logger.debug(f"NotificationAPIMiddleware: Handling unauthenticated request to {full_path}")
            # Return empty array instead of redirecting
            return JsonResponse([], safe=False)
        
        # Process the request normally for all other cases
        return self.get_response(request)
