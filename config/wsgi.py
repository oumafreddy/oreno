# config/wsgi.py

import os
from django.core.wsgi import get_wsgi_application

# Use tenant‑aware settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.tenants')

application = get_wsgi_application()

# Optional sanity check: verify URL patterns
try:
    from django.urls import get_resolver
    resolver = get_resolver()
    if not resolver.url_patterns:
        raise RuntimeError("No URL patterns found. Check your urls.py configuration.")
except Exception as e:
    # Print and re‑raise so that the container logs the failure
    print(f"WSGI Configuration Error: {e}")
    raise
