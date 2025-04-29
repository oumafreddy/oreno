# config/urls_public.py

from django.contrib import admin
from django.urls import path, include
from django.http import HttpResponse
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import TemplateView
from django.views.defaults import (
    page_not_found,
    server_error,
    permission_denied,
    bad_request
)

# Define error handlers for public schema
handler400 = 'core.views.bad_request'
handler403 = 'core.views.permission_denied'
handler404 = 'core.views.page_not_found'
handler500 = 'core.views.server_error'

def public_home(request):
    """Public home page view"""
    return HttpResponse("Welcome to the public Oreno site!")

# Define URL patterns for public schema
urlpatterns = [
    # Public Admin
    path('admin/', admin.site.urls),
    
    # Public Home and Documentation
    path('', public_home, name='public-home'),
    path('docs/', TemplateView.as_view(
        template_name='public/docs.html'
    ), name='public-docs'),
    
    # Public Authentication
    path('accounts/', include('users.urls', namespace='public-users')),
    path('organizations/', include('organizations.urls', namespace='organizations')),
    
    # Public API Documentation
    path('api/docs/', TemplateView.as_view(
        template_name='swagger-ui.html',
        extra_context={'schema_url': 'public-api-schema'}
    ), name='public-swagger-ui'),
    
    # Public API Endpoints
    path('api/', include('rest_framework.urls', namespace='public-rest-framework')),
    path('api/users/', include(('users.urls', 'users'), namespace='public-users-api')),
    path('api/organizations/', include(('organizations.urls', 'organizations'), namespace='public-organizations-api')),
    
    # Public Health Check
    path('health/', lambda r: HttpResponse('OK'), name='public-health-check'),
    
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
