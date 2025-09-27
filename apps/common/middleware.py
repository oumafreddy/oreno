from django.shortcuts import redirect
from django.urls import reverse
from django.contrib.auth import logout

class OrganizationActiveMiddleware:
    """
    Blocks access for users whose organization (tenant) is inactive.
    """
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        user = request.user
        tenant = getattr(request, 'tenant', None)
        if user.is_authenticated and tenant and hasattr(tenant, 'is_active'):
            if not tenant.is_active:
                logout(request)
                return redirect(reverse('service_paused'))
        return self.get_response(request)

class AppAccessControlMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Only check for authenticated users and tenant organizations
        if hasattr(request, 'tenant'):
            org = request.tenant
            app_label = self.get_app_label(request)
            path = request.path or '/'

            # Allow essential account/auth routes for all roles
            auth_allowed_prefixes = (
                '/accounts/login',
                '/accounts/logout',
                '/accounts/password',
                '/accounts/first-time-setup',
                '/accounts/resend-otp-setup',
            )
            if any(path.startswith(p) for p in auth_allowed_prefixes):
                return self.get_response(request)

            # Enforce strict app-level access for Risk Champion
            # Risk Champions must only access the 'risk' app namespace
            if request.user.is_authenticated and getattr(request.user, 'role', None) == 'risk_champion':
                if app_label and app_label != 'risk':
                    from django.http import HttpResponseForbidden
                    return HttpResponseForbidden('Permission denied: Risk Champion is restricted to Risk module only.')

            if app_label and not self.is_app_subscribed(org, app_label):
                if not request.path.startswith(reverse('service_info')):
                    return redirect(reverse('service_info') + f'?app={app_label}')
        return self.get_response(request)

    def get_app_label(self, request):
        # Preferred: namespace from resolver
        if hasattr(request, 'resolver_match') and request.resolver_match:
            ns = request.resolver_match.namespace
            if ns:
                return ns
        # Fallback: infer from first path segment
        try:
            first = (request.path or '/').lstrip('/').split('/', 1)[0]
        except Exception:
            first = ''
        # Map well-known URL prefixes to app labels
        segment_map = {
            'audit': 'audit',
            'risk': 'risk',
            'compliance': 'compliance',
            'contracts': 'contracts',
            'legal': 'legal',
            'documents': 'document_management',
            'document-management': 'document_management',
            'ai-governance': 'ai_governance',
            'accounts': 'users',
            'users': 'users',
        }
        return segment_map.get(first)

    def is_app_subscribed(self, org, app_label):
        return app_label in getattr(org.settings, 'subscribed_apps', []) 