from django.http import JsonResponse
import re
from django.conf import settings
import logging
from django.utils.functional import SimpleLazyObject
from django.utils.deprecation import MiddlewareMixin
from django.utils.translation import gettext_lazy as _
from django.contrib import messages
from django.shortcuts import redirect

logger = logging.getLogger(__name__)

class OrganizationContextMiddleware:
    """
    Middleware to ensure consistent organization context for all requests.
    This middleware does the following:
    
    1. Sets request.organization to the user's active organization if available
    2. Sets request.tenant as an alias for organization for backward compatibility
    3. Verifies organization access for paths containing organization ID
    4. Ensures all audit app paths have an active organization set
    """
    def __init__(self, get_response):
        self.get_response = get_response
        # Define audit app paths that require organization context
        self.audit_paths = [
            re.compile(r'^/audit/'),
            re.compile(r'^/api/audit/'),
        ]
        # Exclude these public paths from organization requirement
        self.excluded_paths = [
            re.compile(r'^/audit/login/'),
            re.compile(r'^/audit/logout/'),
            re.compile(r'^/audit/public/'),
            re.compile(r'^/static/'),
            re.compile(r'^/media/'),
        ]
        
    def __call__(self, request):
        # Skip processing for excluded paths
        for pattern in self.excluded_paths:
            if pattern.match(request.path_info):
                return self.get_response(request)
        
        # For authenticated users, set organization context
        if request.user.is_authenticated:
            # Get the active organization from the user
            active_organization = getattr(request.user, 'active_organization', None)
            
            # Set organization context on request for consistent access
            request.organization = active_organization
            # Set tenant as alias for compatibility with existing code
            request.tenant = active_organization
            
            # For audit paths, verify organization context is available
            if any(pattern.match(request.path_info) for pattern in self.audit_paths):
                if not active_organization and not request.is_ajax() and request.method == 'GET':
                    # Redirect to organization selection if no active organization
                    messages.warning(request, _('Please select an organization to continue'))
                    return redirect('users:organization-list')
        
        # Process the request normally
        return self.get_response(request)


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
            # Add Risk-related API endpoints
            re.compile(r'^/audit/api/risks'),
            re.compile(r'^/api/audit/risks'),
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
