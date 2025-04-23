# apps/core/middleware.py

import threading
from django.http import HttpResponseForbidden
from organizations.models import Domain as TenantDomain
from django.shortcuts import redirect
from django.utils.deprecation import MiddlewareMixin
from django.core.exceptions import ImproperlyConfigured

_thread_locals = threading.local()

class CustomDomainMiddleware(MiddlewareMixin):
    def process_request(self, request):
        host = request.get_host().split(':')[0]
        try:
            domain_obj = TenantDomain.objects.get(domain=host)
            request.organization = domain_obj.tenant if hasattr(domain_obj, 'tenant') else domain_obj.organization
        except TenantDomain.DoesNotExist:
            return HttpResponseForbidden("Unknown domain")

def get_current_user():
    return getattr(_thread_locals, 'user', None)

def get_current_organization():
    return getattr(_thread_locals, 'organization', None)


class CurrentUserMiddleware(MiddlewareMixin):
    def process_request(self, request):
        _thread_locals.user = getattr(request, 'user', None)


class OrganizationMiddleware(MiddlewareMixin):
    """
    Auto-attach request.organization and redirect unaffiliated users
    to the organization creation page. Allows skipping via decorator
    or URL prefixes.
    """

    # Paths to bypass org‑check entirely
    EXEMPT_PATH_PREFIXES = (
        '/accounts/login/', '/accounts/register/',
        '/accounts/logout/', '/admin/',
        '/static/', '/media/', '/favicon.ico',
    )

    def process_request(self, request):
        # 1) Skip decorated views
        if getattr(request, '_skip_org_check', False):
            _thread_locals.organization = None
            request.organization = None
            return None

        # 2) Skip exempt prefixes
        path = request.path_info
        if any(path.startswith(prefix) for prefix in self.EXEMPT_PATH_PREFIXES):
            _thread_locals.organization = None
            request.organization = None
            return None

        # 3) Enforce for authenticated users
        user = getattr(request, 'user', None)
        organization = None
        if user and user.is_authenticated:
            # If user has no org, redirect them
            if not getattr(user, 'organization', None):
                return redirect('organizations:organization-create')  # 302 redirect :contentReference[oaicite:6]{index=6}
            organization = user.organization

        # 4) Store for downstream use
        _thread_locals.organization = organization
        request.organization = organization

        return None

    def process_response(self, request, response):
        # Prevent thread‑local leakage
        if hasattr(_thread_locals, 'organization'):
            del _thread_locals.organization
        return response
