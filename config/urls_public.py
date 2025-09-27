# config/urls_public.py

from django.contrib import admin
from django.contrib.sitemaps.views import sitemap
from django.urls import path, include, re_path
from django.http import HttpResponse, HttpResponseNotFound
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import TemplateView
from django.views.defaults import (
    page_not_found,
    server_error,
    permission_denied,
    bad_request
)
from django.views.generic import TemplateView
from django.urls import path

from .sitemaps import PublicSitemap, StaticSitemap

# Define error handlers for public schema
handler400 = 'core.views.bad_request'
handler403 = 'core.views.permission_denied'
handler404 = 'core.views.page_not_found'
handler500 = 'core.views.server_error'

class PublicHomeView(TemplateView):
    """Public home page view"""
    template_name = 'public/home.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Home - Hashrate Solutions'
        return context

class PrivacyPolicyView(TemplateView):
    """Privacy policy page"""
    template_name = 'public/privacy.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Privacy Policy - Hashrate Solutions'
        return context

class CookiePolicyView(TemplateView):
    """Cookie policy page"""
    template_name = 'public/cookies.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = 'Cookie Policy - Hashrate Solutions'
        return context

# Local simple 404 view for blocked admin path (public schema)
def _blocked_admin_404(request, *args, **kwargs):
    return HttpResponseNotFound('Not Found')

# Sitemap configuration
sitemaps = {
    'public': PublicSitemap,
    'static': StaticSitemap,
}

# Define URL patterns for public schema
urlpatterns = [
    # Public Admin - mount only at secret path
    path(settings.ADMIN_URL, admin.site.urls),
    # Block default /admin/
    re_path(r'^admin(/.*)?$', _blocked_admin_404),
    
    # Sitemap
    path('sitemap.xml', sitemap, {'sitemaps': sitemaps}, name='django.contrib.sitemaps.views.sitemap'),
    
    # Public Pages
    path('', PublicHomeView.as_view(), name='public-home'),
    path('privacy-policy/', PrivacyPolicyView.as_view(), name='public-privacy'),
    path('cookie-policy/', CookiePolicyView.as_view(), name='public-cookies'),
    
    # Public Documentation
    path('docs/', TemplateView.as_view(
        template_name='public/docs.html'
    ), name='public-docs'),
    
    # Public Authentication - BLOCKED (tenant-specific only)
    # Note: Authentication should only be available on tenant sites
    re_path(r'^accounts(/.*)?$', _blocked_admin_404, name='blocked-accounts'),
    re_path(r'^organizations(/.*)?$', _blocked_admin_404, name='blocked-organizations'),
    
    # Public API Documentation
    path('api/docs/', TemplateView.as_view(
        template_name='swagger-ui.html',
        extra_context={'schema_url': 'public-api-schema'}
    ), name='public-swagger-ui'),
    
    # Public API Endpoints - BLOCKED (tenant-specific only)
    # Note: User and organization APIs should only be available on tenant sites
    re_path(r'^api/users(/.*)?$', _blocked_admin_404, name='blocked-api-users'),
    re_path(r'^api/organizations(/.*)?$', _blocked_admin_404, name='blocked-api-organizations'),
    re_path(r'^api/auth(/.*)?$', _blocked_admin_404, name='blocked-api-auth'),
    
    # Public Health Check
    path('health/', lambda r: HttpResponse('OK'), name='public-health-check'),
    
    # Robots.txt
    path('robots.txt', lambda r: HttpResponse(
        'User-agent: *\n'
        'Allow: /\n'
        'Allow: /privacy-policy/\n'
        'Allow: /cookie-policy/\n'
        'Allow: /docs/\n'
        'Allow: /health/\n'
        'Disallow: /admin/\n'
        'Disallow: /accounts/\n'
        'Disallow: /organizations/\n'
        'Disallow: /api/\n'
        'Sitemap: http://127.0.0.1:8000/sitemap.xml\n'
        'Sitemap: https://oreno.tech/sitemap.xml\n',
        content_type='text/plain'
    ), name='robots-txt'),
    
    # Public Error Pages (for testing in development)
    path('400/', bad_request, kwargs={'exception': Exception('Bad Request')}),
    path('403/', permission_denied, kwargs={'exception': Exception('Permission Denied')}),
    path('404/', page_not_found, kwargs={'exception': Exception('Page not Found')}),
    path('500/', server_error),
]

# Debug-specific URL patterns
if settings.DEBUG:
    # Serve static and media files directly
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    
    # Debug toolbar
    if 'debug_toolbar' in settings.INSTALLED_APPS:
        import debug_toolbar
        urlpatterns = [
            path('__debug__/', include(debug_toolbar.urls)),
        ] + urlpatterns
