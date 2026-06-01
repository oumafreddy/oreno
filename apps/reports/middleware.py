"""Security middleware for tenant PDF/report exports."""
import re

from django.conf import settings
from django.http import HttpResponseBadRequest, HttpResponseForbidden
from django.shortcuts import redirect

# Report query params are display filters only — keep them short and HTML-free.
_MAX_PARAM_LEN = 200
_UNSAFE_GET = re.compile(r'[<>"\']|javascript:|data:')


class TenantReportSecurityMiddleware:
    """
    Enforce authentication and sanitize GET parameters for /reports/ exports.
    Cross-tenant access is already handled by OrganizationMiddleware; this adds
    explicit report-path checks and filter hardening.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        path = request.path_info
        if not path.startswith('/reports/'):
            return self.get_response(request)

        if not request.user.is_authenticated:
            return redirect(settings.LOGIN_URL)

        tenant = getattr(request, 'tenant', None)
        if tenant is None:
            return HttpResponseForbidden('Reports require an organization context.')

        user_org = getattr(request.user, 'organization', None)
        if user_org is not None and tenant.pk != user_org.pk:
            return HttpResponseForbidden('You do not have access to this organization.')

        for key, value in request.GET.items():
            if len(key) > 64 or len(value) > _MAX_PARAM_LEN:
                return HttpResponseBadRequest('Invalid report filter parameters.')
            if _UNSAFE_GET.search(value):
                return HttpResponseBadRequest('Invalid report filter parameters.')

        return self.get_response(request)
