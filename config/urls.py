# C:\Users\ouma.fred\Desktop\GRC\oreno\config\urls.py

from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.http import HttpResponse

from rest_framework_simplejwt.views import (TokenObtainPairView,TokenRefreshView,)

# Define a simple home view
def home(request):
    return HttpResponse("Welcome to Oreno!")


urlpatterns = [
    path('admin/', admin.site.urls),
    path('api/', include('rest_framework.urls')),
    path('', lambda req: HttpResponse("Welcome to Oreno!"), name='home'),
      
    # Home page
    path('', home, name='home'),

    # Web UI for users (register, login, profile, password)
    path('accounts/', include('users.urls', namespace='users')),

    # REST API for users (JWT & OTP)
    path('api/users/', include(('users.urls', 'users'), namespace='users-api')),

    # Organizations
    path('organizations/', include('organizations.urls', namespace='organizations')),       

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
