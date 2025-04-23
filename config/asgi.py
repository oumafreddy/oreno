# config/asgi.py

import os
from django.core.asgi import get_asgi_application

# Use tenant‑aware settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.tenants')

application = get_asgi_application()

# Optional sanity check: verify URL patterns
try:
    from django.urls import get_resolver
    resolver = get_resolver()
    if not resolver.url_patterns:
        raise RuntimeError("No URL patterns found. Check your urls.py configuration.")
except Exception as e:
    print(f"ASGI Configuration Error: {e}")
    raise
