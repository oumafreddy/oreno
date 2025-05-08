# C:\Users\ouma.fred\Desktop\GRC\oreno\config\urls.py

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.http import HttpResponse
from django.views.generic import TemplateView
from django.views.defaults import (
    page_not_found,
    server_error,
    permission_denied,
    bad_request
)
from django.shortcuts import render

from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)
from common.views import service_paused
from core.views import AIAssistantAPIView

# Define a simple home view
def home(request):
    return render(request, 'home/dashboard.html')

# Define error handlers
handler400 = 'core.views.bad_request'
handler403 = 'core.views.permission_denied'
handler404 = 'core.views.page_not_found'
handler500 = 'core.views.server_error'

# Define URL patterns
urlpatterns = [
    # Admin URLs
    path('admin/', admin.site.urls),
    
    # API Documentation
    path('api/docs/', TemplateView.as_view(
        template_name='swagger-ui.html',
        extra_context={'schema_url': 'openapi-schema'}
    ), name='swagger-ui'),
    
    # API Authentication
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    
    # API Endpoints
    path('api/', include('rest_framework.urls', namespace='rest_framework')),
    path('api/users/', include(('users.urls', 'users'), namespace='users-api')),
    path('api/organizations/', include(('organizations.urls', 'organizations'), namespace='organizations-api')),
    path('api/audit/', include(('audit.urls', 'audit'), namespace='audit-api')),
    path('api/compliance/', include(('compliance.urls', 'compliance'), namespace='compliance-api')),
    path('api/contracts/', include(('contracts.urls', 'contracts'), namespace='contracts-api')),
    path('api/risk/', include(('risk.urls', 'risk'), namespace='risk-api')),
    path('api/legal/', include(('legal.urls', 'legal'), namespace='legal-api')),
    path('api/ai/ask/', AIAssistantAPIView.as_view(), name='ai-assistant-ask'),
    
    # Web UI URLs
    path('', home, name='home'),
    path('accounts/', include('users.urls', namespace='users')),
    path('organizations/', include('organizations.urls', namespace='organizations')),
    path('audit/', include('audit.urls', namespace='audit')),
    path('compliance/', include(('compliance.urls', 'compliance'), namespace='compliance')),
    path('contracts/', include(('contracts.urls', 'contracts'), namespace='contracts')),
    path('risk/', include(('risk.urls', 'risk'), namespace='risk')),
    path('document_management/', include(('document_management.urls', 'document_management'), namespace='document_management')),
    path('legal/', include(('legal.urls', 'legal'), namespace='legal')),
    
    # CKEditor 5
    path('upload/', include('django_ckeditor_5.urls')),
    
    # Health Check
    path('health/', lambda request: HttpResponse('ok'), name='health'),

    # Service Paused Info Page
    path('service-paused/', service_paused, name='service_paused'),

    # Admin Module
    path('admin-module/', include('admin_module.urls', namespace='admin_module')),

    # Reports
    path('reports/', include('reports.urls', namespace='reports')),

    # Service Info Page
    path('service-info/', TemplateView.as_view(template_name='service_info.html'), name='service_info'),
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
    
    # Debug error pages
    urlpatterns += [
        path('400/', bad_request, kwargs={'exception': Exception('Bad Request')}),
        path('403/', permission_denied, kwargs={'exception': Exception('Permission Denied')}),
        path('404/', page_not_found, kwargs={'exception': Exception('Page not Found')}),
        path('500/', server_error),
    ]
