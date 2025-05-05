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
        if hasattr(request, 'tenant') and request.user.is_authenticated:
            org = request.tenant
            app_label = self.get_app_label(request)
            if app_label and not self.is_app_subscribed(org, app_label):
                if not request.path.startswith(reverse('service_info')):
                    return redirect(reverse('service_info') + f'?app={app_label}')
        return self.get_response(request)

    def get_app_label(self, request):
        if hasattr(request, 'resolver_match') and request.resolver_match:
            return request.resolver_match.namespace
        return None

    def is_app_subscribed(self, org, app_label):
        return app_label in getattr(org.settings, 'subscribed_apps', []) 