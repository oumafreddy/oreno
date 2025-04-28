# oreno\config\settings\development.py
from .base import *  # noqa: F401, F403
from .tenants import *  # noqa: F401, F403

# ------------------------------------------------------------------------------
# Development-specific settings
# ------------------------------------------------------------------------------

# Debug settings
DEBUG = True
TEMPLATE_DEBUG = DEBUG
DEBUG_TOOLBAR = True

# Security settings for development
ALLOWED_HOSTS = ['localhost', '127.0.0.1', '[::1]']
CORS_ALLOW_ALL_ORIGINS = True
CORS_ALLOW_CREDENTIALS = True
CSRF_TRUSTED_ORIGINS = ['http://localhost:8000', 'http://127.0.0.1:8000']

# Email settings for development
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'
EMAIL_HOST = 'localhost'
EMAIL_PORT = 1025
EMAIL_USE_TLS = False
EMAIL_HOST_USER = ''
EMAIL_HOST_PASSWORD = ''

# Database settings for development
DATABASES = {
    'default': {
        'ENGINE': 'django_tenants.postgresql_backend',
        'NAME': os.getenv('POSTGRES_DB', 'oreno_dev'),
        'USER': os.getenv('POSTGRES_USER', 'postgres'),
        'PASSWORD': os.getenv('POSTGRES_PASSWORD', 'postgres'),
        'HOST': os.getenv('POSTGRES_HOST', 'localhost'),
        'PORT': os.getenv('POSTGRES_PORT', '5432'),
        'CONN_MAX_AGE': 0,  # Disable persistent connections in development
        'OPTIONS': {
            'connect_timeout': 5,  # Shorter timeout for development
        },
    }
}

# Cache settings for development
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'unique-snowflake',
    }
}

# Logging settings for development
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
            'level': 'DEBUG',
            'class': 'logging.StreamHandler',
            'formatter': 'verbose',
        },
        'file': {
            'level': 'DEBUG',
            'class': 'logging.FileHandler',
            'filename': BASE_DIR / 'logs' / 'development.log',
            'formatter': 'verbose',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': True,
        },
        'django.db.backends': {
            'handlers': ['console'],
            'level': 'DEBUG',
            'propagate': False,
        },
        'django_tenants': {
            'handlers': ['console', 'file'],
            'level': 'DEBUG',
            'propagate': True,
        },
    },
}

# Debug toolbar settings
if DEBUG_TOOLBAR:
    INSTALLED_APPS += [
        'debug_toolbar',
        'django_extensions',
    ]
    
    MIDDLEWARE += [
        'debug_toolbar.middleware.DebugToolbarMiddleware',
    ]
    
    DEBUG_TOOLBAR_PANELS = [
        'debug_toolbar.panels.versions.VersionsPanel',
        'debug_toolbar.panels.timer.TimerPanel',
        'debug_toolbar.panels.settings.SettingsPanel',
        'debug_toolbar.panels.headers.HeadersPanel',
        'debug_toolbar.panels.request.RequestPanel',
        'debug_toolbar.panels.sql.SQLPanel',
        'debug_toolbar.panels.staticfiles.StaticFilesPanel',
        'debug_toolbar.panels.templates.TemplatesPanel',
        'debug_toolbar.panels.cache.CachePanel',
        'debug_toolbar.panels.signals.SignalsPanel',
        'debug_toolbar.panels.logging.LoggingPanel',
        'debug_toolbar.panels.redirects.RedirectsPanel',
    ]
    
    DEBUG_TOOLBAR_CONFIG = {
        'INTERCEPT_REDIRECTS': False,
        'SHOW_TOOLBAR_CALLBACK': lambda request: True,
        'SHOW_TEMPLATE_CONTEXT': True,
    }

# Development-specific middleware
MIDDLEWARE += [
    'django.middleware.common.BrokenLinkEmailsMiddleware',
]

# Development-specific apps
INSTALLED_APPS += [
    'django_extensions',
    'django.contrib.admindocs',
]

# Development-specific template settings
TEMPLATES[0]['OPTIONS']['debug'] = DEBUG
TEMPLATES[0]['OPTIONS']['string_if_invalid'] = 'INVALID EXPRESSION: %s'

# Development-specific static files settings
STATICFILES_DIRS = [
    BASE_DIR / 'static',
]

# Development-specific media settings
MEDIA_ROOT = BASE_DIR / 'media'
MEDIA_URL = '/media/'

# Development-specific session settings
SESSION_COOKIE_SECURE = False
CSRF_COOKIE_SECURE = False
SECURE_SSL_REDIRECT = False

# Development-specific tenant settings
TENANT_CREATE_SCHEMA_AUTOMATICALLY = True
TENANT_SYNC_SCHEMA_AUTOMATICALLY = True
TENANT_CREATE_PUBLIC_SCHEMA_AUTOMATICALLY = True
TENANT_CREATE_PUBLIC_TENANT_AUTOMATICALLY = True

# Development-specific API settings
REST_FRAMEWORK['DEFAULT_RENDERER_CLASSES'] += [
    'rest_framework.renderers.BrowsableAPIRenderer',
]
REST_FRAMEWORK['DEFAULT_AUTHENTICATION_CLASSES'] += [
    'rest_framework.authentication.SessionAuthentication',
]

# Development-specific email settings
DEFAULT_FROM_EMAIL = 'development@example.com'
SERVER_EMAIL = 'development@example.com'
ADMINS = [
    ('Development Admin', 'admin@example.com'),
]
MANAGERS = ADMINS

# ------------------------------------------------------------------------------
# Development-Specific Overrides
# ------------------------------------------------------------------------------

# Use a simple secret key for development (override in production)
SECRET_KEY = os.getenv('DJANGO_SECRET_KEY', 'development-secret-key')

# ------------------------------------------------------------------------------
# Development Tools Configuration
# ------------------------------------------------------------------------------

# ------------------------------------------------------------------------------
# Database Configuration (SQLite for development)
# ------------------------------------------------------------------------------
# Already defined in base.py - no need to duplicate unless overriding

# ------------------------------------------------------------------------------
# Email Configuration
# ------------------------------------------------------------------------------
# Already configured in base.py to use console backend

# ------------------------------------------------------------------------------
# Logging Configuration
# ------------------------------------------------------------------------------
# Inherits from base.py but adds development-specific loggers if needed
LOGGING['loggers']['django.db.backends'] = {
    'level': 'DEBUG',
    'handlers': ['console'],
}

# ------------------------------------------------------------------------------
# Deprecation Handling
# ------------------------------------------------------------------------------
# Remove deprecated setting in newer Django versions
if hasattr(globals(), 'USE_L10N'):
    del USE_L10N