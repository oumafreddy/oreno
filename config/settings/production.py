# oreno\config\settings\production.py
import os
from .base import *

import sentry_sdk
from sentry_sdk.integrations.django import DjangoIntegration

# Do not run in debug mode in production
DEBUG = False

# Enable HSTS for one year (31,536,000 seconds)
SECURE_HSTS_SECONDS = 31536000  
# Also apply HSTS to all subdomains (if every subdomain serves HTTPS)
SECURE_HSTS_INCLUDE_SUBDOMAINS = True  
# Allow adding your site to browser preload lists (careful—irreversible)
SECURE_HSTS_PRELOAD = True  

# In production.py
SECURE_SSL_REDIRECT = False

# In production.py
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True

SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_BROWSER_XSS_FILTER = True


# SECRET_KEY must be set in the environment—raise exception if missing
SECRET_KEY = os.getenv("DJANGO_SECRET_KEY")
if not SECRET_KEY:
    raise Exception("DJANGO_SECRET_KEY environment variable must be set in production.")

# Allowed hosts: split on comma, trim whitespace, and ignore empty items
ALLOWED_HOSTS = [host.strip() for host in os.getenv("DJANGO_ALLOWED_HOSTS", "").split(",") if host.strip()]

# PostgreSQL configuration using environment variables
DATABASES = {
    "default": {
        "ENGINE": "django.db.backends.postgresql",
        "NAME": os.getenv("POSTGRES_DB"),
        "USER": os.getenv("POSTGRES_USER"),
        "PASSWORD": os.getenv("POSTGRES_PASSWORD"),
        "HOST": os.getenv("POSTGRES_HOST", "localhost"),
        "PORT": os.getenv("POSTGRES_PORT", "5432"),
    }
}

# Secure settings
SECURE_HSTS_SECONDS = 3600  # Consider increasing this value once tested
SECURE_SSL_REDIRECT = True
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True

# Email configuration
EMAIL_BACKEND = "django.core.mail.backends.smtp.EmailBackend"
EMAIL_HOST = os.getenv("EMAIL_HOST", "smtp.your-provider.com")
EMAIL_PORT = int(os.getenv("EMAIL_PORT", 587))
EMAIL_HOST_USER = os.getenv("EMAIL_USER")
EMAIL_HOST_PASSWORD = os.getenv("EMAIL_PASS")
EMAIL_USE_TLS = True

# Static and Media files
STATIC_ROOT = BASE_DIR / "staticfiles"
MEDIA_ROOT = BASE_DIR / "media"

# Logging configuration: basic console logging
LOGGING = {
    "version": 1,
    "disable_existing_loggers": False,
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
        },
    },
    "root": {
        "handlers": ["console"],
        "level": "INFO",
    },
}

CACHES = {
    "default": {
        "BACKEND": "django_redis.cache.RedisCache",
        "LOCATION": os.getenv("REDIS_URL", "redis://127.0.0.1:6379/1"),
        "OPTIONS": {
            "CLIENT_CLASS": "django_redis.client.DefaultClient",
        },
    },
}


MIDDLEWARE.insert(
    1,
    'whitenoise.middleware.WhiteNoiseMiddleware'
)

STATICFILES_STORAGE = 'whitenoise.storage.CompressedManifestStaticFilesStorage'

sentry_sdk.init(
    dsn=os.getenv('SENTRY_DSN'),
    integrations=[DjangoIntegration()],
    traces_sample_rate=0.1,
    send_default_pii=False,
)