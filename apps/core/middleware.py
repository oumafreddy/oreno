# GRC/oreno/apps/core/middleware.py

import threading
from django.shortcuts import redirect
from django.utils.deprecation import MiddlewareMixin
from django.core.exceptions import ImproperlyConfigured
from django.urls import resolve

from apps.organizations.models import Organization  # Ensure import is valid

_thread_locals = threading.local()


def get_current_user():
    """Retrieve the current user from thread-local storage."""
    return getattr(_thread_locals, 'user', None)


def get_current_organization():
    """Retrieve the current organization from thread-local storage."""
    return getattr(_thread_locals, 'organization', None)


class CurrentUserMiddleware(MiddlewareMixin):
    """
    Stores the current user in thread-local storage for use in models and other places.
    Useful for audit logging (created_by/updated_by).
    """
    def process_request(self, request):
        _thread_locals.user = getattr(request, 'user', None)


class OrganizationMiddleware(MiddlewareMixin):
    """
    Stores the current user's organization in thread-local storage and on the request.
    Handles missing or inactive organizations gracefully.
    """
    EXEMPT_URL_NAMES = {
        'admin:login', 'admin:logout', 'admin:index',
        'password_reset', 'password_reset_done',
    }

    EXEMPT_PATH_PREFIXES = (
        '/admin/', '/accounts/login/', '/accounts/logout/', '/static/', '/media/',
    )

    def process_request(self, request):
        user = getattr(request, 'user', None)
        organization = None

        # Allow access to exempt paths (admin, login, etc.) without error
        if self._is_exempt_path(request.path_info):
            _thread_locals.organization = None
            request.organization = None
            return

        if user and user.is_authenticated:
            try:
                organization = user.organization
                if organization is None:
                    raise ImproperlyConfigured("Authenticated user has no organization.")
                if not organization.is_active:
                    raise ImproperlyConfigured("User's organization is inactive.")
            except Organization.DoesNotExist:
                pass  # Superusers or special cases

        _thread_locals.organization = organization
        request.organization = organization  # For use in views, templates, etc.

    def process_response(self, request, response):
        # Clean up to prevent thread leakage in long-running workers
        if hasattr(_thread_locals, 'organization'):
            del _thread_locals.organization
        return response

    def _is_exempt_path(self, path):
        """
        Determine if the given request path is exempt from organization validation.
        """
        return any(path.startswith(prefix) for prefix in self.EXEMPT_PATH_PREFIXES)
