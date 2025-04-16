# config/wsgi.py
import os
from django.core.wsgi import get_wsgi_application

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.base')

application = get_wsgi_application()

# Verify WSGI application is correctly configured
try:
    from django.urls import get_resolver
    resolver = get_resolver()
    if not resolver.url_patterns:
        raise RuntimeError("No URL patterns found. Check your urls.py configuration.")
except Exception as e:
    print(f"WSGI Configuration Error: {e}")
    raise