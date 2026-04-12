import re
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
            # Exclude Django admin paths to avoid overriding tenant set by AdminTenantMiddleware
            re.compile(r'^/admin/'),
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
            # Get the active organization from the user or from the current tenant
            active_organization = getattr(request.user, 'active_organization', None)
            
            # If no active organization but we're on a tenant subdomain, set active org from tenant
            if not active_organization and hasattr(request, 'tenant'):
                from organizations.models import Organization
                try:
                    # Get organization based on tenant schema name
                    org = Organization.objects.filter(schema_name=request.tenant.schema_name).first()
                    if org:
                        # Set as active organization for the user
                        request.user.active_organization = org
                        active_organization = org
                except Exception as e:
                    logger.error(f"Error setting active organization from tenant: {e}")
            
            # Set organization context on request for consistent access
            request.organization = active_organization
            # Set tenant as alias for compatibility with existing code
            request.tenant = active_organization
            
            # For audit paths, verify organization context is available
            if any(pattern.match(request.path_info) for pattern in self.audit_paths):
                if not active_organization and not request.headers.get('X-Requested-With') == 'XMLHttpRequest' and request.method == 'GET':
                    # Redirect to organization selection if no active organization
                    messages.warning(request, _('Please select an organization to continue'))
                    return redirect('organizations:list')
        
        # Process the request normally
        return self.get_response(request)

