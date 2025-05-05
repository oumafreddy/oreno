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
    Auto-attach request.organization and redirect unaffiliated users
    to the organization creation page. Allows skipping via decorator
    or URL prefixes.
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

        # 3) Enforce for authenticated users
        user = getattr(request, 'user', None)
        organization = None
        
        if user and user.is_authenticated:
            # Get organization from user or their memberships
            organization = getattr(user, 'organization', None)
            if not organization:
                # Check OrganizationUser memberships
                from organizations.models import OrganizationUser
                org_user = OrganizationUser.objects.filter(user=user).first()
                if org_user:
                    organization = org_user.organization
                elif not path.startswith('/organizations/create/'):
                    return redirect('organizations:create')

        # 4) Store for downstream use
        _thread_locals.organization = organization
        request.organization = organization

        response = self.get_response(request)
        
        # Prevent thread‑local leakage
        if hasattr(_thread_locals, 'organization'):
            del _thread_locals.organization
            
        print(f"Current schema: {connection.schema_name}")
        return response
