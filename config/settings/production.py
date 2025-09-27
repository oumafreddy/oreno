# oreno\config\settings\production.py
import os
from .base import *  # noqa: F401, F403
from .tenants import *  # noqa: F401, F403

import sentry_sdk
from sentry_sdk.integrations.django import DjangoIntegration

# ------------------------------------------------------------------------------
# Production-specific settings
# ------------------------------------------------------------------------------

# Debug settings
DEBUG = False
TEMPLATE_DEBUG = False

# Security settings
ALLOWED_HOSTS = os.getenv('DJANGO_ALLOWED_HOSTS', '').split(',')
CORS_ALLOWED_ORIGINS = os.getenv('CORS_ALLOWED_ORIGINS', '').split(',')
CORS_ALLOW_CREDENTIALS = True
CSRF_TRUSTED_ORIGINS = os.getenv('CSRF_TRUSTED_ORIGINS', '').split(',')

# Security middleware settings
SECURE_SSL_REDIRECT = True
SECURE_HSTS_SECONDS = 31536000  # 1 year
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True
SECURE_CONTENT_TYPE_NOSNIFF = True
SECURE_BROWSER_XSS_FILTER = True
X_FRAME_OPTIONS = 'DENY'
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
CSRF_COOKIE_HTTPONLY = False
SESSION_COOKIE_HTTPONLY = True
SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

# Database settings
DATABASES = {
    'default': {
        'ENGINE': 'django_tenants.postgresql_backend',
        'NAME': os.getenv('POSTGRES_DB'),
        'USER': os.getenv('POSTGRES_USER'),
        'PASSWORD': os.getenv('POSTGRES_PASSWORD'),
        'HOST': os.getenv('POSTGRES_HOST'),
        'PORT': os.getenv('POSTGRES_PORT', '5432'),
        'CONN_MAX_AGE': 60,  # Persistent connections
        'OPTIONS': {
            'connect_timeout': 10,
            'sslmode': 'require',
        },
    }
}

###################################################################

# Cache settings
CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': os.getenv('REDIS_URL', 'redis://127.0.0.1:6379/1'),
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
            'SOCKET_CONNECT_TIMEOUT': 5,
            'SOCKET_TIMEOUT': 5,
            'RETRY_ON_TIMEOUT': True,
            'CONNECTION_POOL_KWARGS': {'max_connections': 1000},
        },
        'KEY_PREFIX': 'oreno',
    }
}

##########################################################################
# Logging settings
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
        'file': {
            'level': 'ERROR',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': BASE_DIR / 'logs' / 'production.log',
            'maxBytes': 1024 * 1024 * 5,  # 5 MB
            'backupCount': 5,
            'formatter': 'verbose',
        },
        'mail_admins': {
            'level': 'ERROR',
            'class': 'django.utils.log.AdminEmailHandler',
            'include_html': True,
        },
    },
    'loggers': {
        'django': {
            'handlers': ['console', 'file', 'mail_admins'],
            'level': 'INFO',
            'propagate': True,
        },
        'django.db.backends': {
            'handlers': ['console'],
            'level': 'ERROR',
            'propagate': False,
        },
        'django_tenants': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': True,
        },
    },
}

# Email settings
#EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
EMAIL_HOST = os.getenv('EMAIL_HOST')
EMAIL_PORT = int(os.getenv('EMAIL_PORT', 587))
EMAIL_USE_TLS = True
EMAIL_HOST_USER = os.getenv('EMAIL_HOST_USER')
EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD')
DEFAULT_FROM_EMAIL = os.getenv('DEFAULT_FROM_EMAIL', 'info@oreno.tech')
SERVER_EMAIL = os.getenv('SERVER_EMAIL', 'info@oreno.tech')

# Admin settings
ADMINS = [
    (os.getenv('ADMIN_NAME', 'Admin'), os.getenv('ADMIN_EMAIL', 'info@oreno.tech')),
]
MANAGERS = ADMINS

# Static and media files
STATIC_ROOT = BASE_DIR / 'staticfiles'
STATICFILES_STORAGE = 'django.contrib.staticfiles.storage.ManifestStaticFilesStorage'
MEDIA_ROOT = BASE_DIR / 'media'
MEDIA_URL = '/media/'

# Tenant settings
TENANT_CREATE_SCHEMA_AUTOMATICALLY = False
TENANT_SYNC_SCHEMA_AUTOMATICALLY = False
TENANT_CREATE_PUBLIC_SCHEMA_AUTOMATICALLY = False
TENANT_CREATE_PUBLIC_TENANT_AUTOMATICALLY = False

# API settings
REST_FRAMEWORK['DEFAULT_RENDERER_CLASSES'] = [
    'rest_framework.renderers.JSONRenderer',
]
REST_FRAMEWORK['DEFAULT_AUTHENTICATION_CLASSES'] = [
    'rest_framework_simplejwt.authentication.JWTAuthentication',
    'rest_framework.authentication.SessionAuthentication',
]

# Performance settings
# TEMPLATES[0]['OPTIONS']['loaders'] = [
#     ('django.template.loaders.cached.Loader', [
#         'django.template.loaders.filesystem.Loader',
#         'django.template.loaders.app_directories.Loader',
#     ]),
# ]

# Session settings
SESSION_ENGINE = 'django.contrib.sessions.backends.cache'
SESSION_CACHE_ALIAS = 'default'

# Cache settings for sessions
CACHES['sessions'] = {
    'BACKEND': 'django.core.cache.backends.redis.RedisCache',
    'LOCATION': os.getenv('REDIS_URL', 'redis://localhost:6379/2'),
    'OPTIONS': {
        'socket_connect_timeout': 5,
        'socket_timeout': 5,
        'retry_on_timeout': True,
        'max_connections': 1000,
    },
    'KEY_PREFIX': 'sessions',
}

# Celery settings
CELERY_BROKER_URL = os.getenv('CELERY_BROKER_URL', 'redis://localhost:6379/0')
CELERY_RESULT_BACKEND = os.getenv('CELERY_RESULT_BACKEND', 'redis://localhost:6379/0')
CELERY_ACCEPT_CONTENT = ['json']
CELERY_TASK_SERIALIZER = 'json'
CELERY_RESULT_SERIALIZER = 'json'
CELERY_TIMEZONE = TIME_ZONE
CELERY_TASK_TRACK_STARTED = True
CELERY_TASK_TIME_LIMIT = 30 * 60  # 30 minutes
CELERY_WORKER_MAX_TASKS_PER_CHILD = 1000

# SECRET_KEY must be set in the environment—raise exception if missing
SECRET_KEY = os.getenv("DJANGO_SECRET_KEY")
if not SECRET_KEY:
    raise Exception("DJANGO_SECRET_KEY environment variable must be set in production.")

MIDDLEWARE.insert(
    1,
    'whitenoise.middleware.WhiteNoiseMiddleware'
)

sentry_sdk.init(
    dsn=os.getenv('SENTRY_DSN'),
    integrations=[DjangoIntegration()],
    traces_sample_rate=0.1,
    send_default_pii=False,
)

# For local development/testing, allow .localhost tenant domains
LOCAL_TENANT_DOMAINS = [
    'org001.localhost',
    'org002.localhost',
    'org003.localhost',
    'org004.localhost',
    'org005.localhost',
    'krcs.localhost',
    'krcs.oreno.tech',
    'org001.oreno.tech',
    'org002.oreno.tech',
    'org003.oreno.tech',
    'org004.oreno.tech',
    'org005.oreno.tech',    
    'oreno.localhost',
]

if DEBUG or any(domain.endswith('.localhost') for domain in ALLOWED_HOSTS):
    for domain in LOCAL_TENANT_DOMAINS:
        if domain not in ALLOWED_HOSTS:
            ALLOWED_HOSTS.append(domain)
    for domain in LOCAL_TENANT_DOMAINS:
        CSRF_TRUSTED_ORIGINS.extend([
            f'http://{domain}',
            f'https://{domain}',
        ])
