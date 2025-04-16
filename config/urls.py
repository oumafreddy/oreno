from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.http import HttpResponse

# Define a simple home view
def home(request):
    return HttpResponse("Welcome to Oreno!")

urlpatterns = [
    # Admin URLs
    path('admin/', admin.site.urls),

    # API URLs (if you plan to use Django REST Framework)
    path('api/', include('rest_framework.urls')),

    # Simple home view
    path('', home, name='home'),
    
    # Uncomment these when you implement the corresponding apps
    # path('organizations/', include('apps.organizations.urls')),
    path('organizations/', include(('apps.organizations.urls', 'organizations'), namespace='organizations')),
    # path('users/', include('apps.users.urls')),
    # path('risk/', include('apps.risk.urls')),
    # path('audit/', include('apps.audit.urls')),
    # path('documents/', include('apps.document_management.urls')),
]

# Debug and static/media file handling for development
if settings.DEBUG:
    # Serve static and media files directly
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

    # Add debug toolbar if it's installed, ensuring that its URLs come first
    if 'debug_toolbar' in settings.INSTALLED_APPS:
        import debug_toolbar
        urlpatterns = [path('__debug__/', include(debug_toolbar.urls))] + urlpatterns
