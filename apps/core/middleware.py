# apps/core/middleware.py

import threading
from django.http import HttpResponseForbidden
from django.shortcuts import redirect
from django.core.exceptions import ImproperlyConfigured
from django.db import connection

_thread_locals = threading.local()

class CustomDomainMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        from organizations.models import Domain
        host = request.get_host().split(':')[0]
        try:
            domain_obj = Domain.objects.get(domain=host)
            request.organization = domain_obj.tenant if hasattr(domain_obj, 'tenant') else domain_obj.organization
        except Domain.DoesNotExist:
            return HttpResponseForbidden("Unknown domain")
        return self.get_response(request)

def get_current_user():
    return getattr(_thread_locals, 'user', None)

def get_current_organization():
    return getattr(_thread_locals, 'organization', None)

class CurrentUserMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        _thread_locals.user = getattr(request, 'user', None)
        response = self.get_response(request)
        return response

class OrganizationMiddleware:
    """
    Enhanced middleware that enforces tenant access control and organization context.
    This middleware ensures:
    1. Users can only access their assigned organization/tenant
    2. Proper organization context is set for all requests
    3. Cross-tenant access is prevented
    """

    # Paths to bypass org‑check entirely
    EXEMPT_PATH_PREFIXES = (
        '/accounts/login/',
        '/accounts/register/',
        '/accounts/logout/',
        '/admin/',
        '/static/',
        '/media/',
        '/favicon.ico',
        '/organizations/create/',
        '/api/users/profile/',
        '/api/users/logout/',
        '/api/',  # Exempt all API endpoints
        '/users/login/',
        '/users/register/',
        '/users/logout/',
        '/service_paused/',
        '/service_info/',
    )

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # 1) Skip decorated views
        if getattr(request, '_skip_org_check', False):
            _thread_locals.organization = None
            request.organization = None
            return self.get_response(request)

        # 2) Skip exempt prefixes
        path = request.path_info
        if any(path.startswith(prefix) for prefix in self.EXEMPT_PATH_PREFIXES):
            _thread_locals.organization = None
            request.organization = None
            return self.get_response(request)

        # 3) Get current tenant from request
        current_tenant = getattr(request, 'tenant', None)
        
        # 4) Enforce tenant access control for authenticated users
        user = getattr(request, 'user', None)
        organization = None
        
        if user and user.is_authenticated:
            # Get user's assigned organization
            user_organization = getattr(user, 'organization', None)
            
            # Check if user has access to current tenant
            if current_tenant and user_organization:
                from .utils import user_has_tenant_access
                if not user_has_tenant_access(user, current_tenant):
                    # User doesn't have access to this tenant - log them out
                    from django.contrib.auth import logout
                    from django.contrib import messages
                    from django.utils.translation import gettext_lazy as _
                    
                    logout(request)
                    messages.error(
                        request, 
                        _("Access denied. You can only access your assigned organization.")
                    )
                    return redirect('users:login')
            
            # Set organization for the request
            organization = user_organization
            if not organization:
                # Check OrganizationUser memberships
                from organizations.models import OrganizationUser
                org_user = OrganizationUser.objects.filter(user=user).first()
                if org_user:
                    organization = org_user.organization
                elif not path.startswith('/organizations/create/'):
                    return redirect('organizations:create')

        # 5) Store for downstream use
        _thread_locals.organization = organization
        request.organization = organization

        response = self.get_response(request)
        
        # Prevent thread‑local leakage
        if hasattr(_thread_locals, 'organization'):
            del _thread_locals.organization
            
        return response
