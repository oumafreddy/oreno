# config/settings/base.py

import os
import sys
from pathlib import Path
from datetime import timedelta

from dotenv import load_dotenv
from django.urls import reverse_lazy

# ------------------------------------------------------------------------------
# Base Directory & Environment Loading
# ------------------------------------------------------------------------------
BASE_DIR = Path(__file__).resolve().parent.parent.parent
load_dotenv(BASE_DIR / '.env.oreno')
APPS_DIR = BASE_DIR / 'apps'
sys.path.insert(0, str(APPS_DIR))  # Allow imports from apps/ without prefix

# ------------------------------------------------------------------------------
# Security
# ------------------------------------------------------------------------------
SECRET_KEY = os.getenv('DJANGO_SECRET_KEY')
if not SECRET_KEY:
    raise Exception("DJANGO_SECRET_KEY not set in environment")

DEBUG = os.getenv('DJANGO_DEBUG', 'True').lower() in ('true', '1', 'yes')

ALLOWED_HOSTS = os.environ.get("DJANGO_ALLOWED_HOSTS", "127.0.0.1,localhost").split(",")

# CSRF settings
CSRF_TRUSTED_ORIGINS = [
    'http://localhost:8000',
    'http://127.0.0.1:8000',
    'http://krcs',
    'http://oreno',
    'https://krcs',
    'https://oreno',
    'https://localhost:8000',
    'https://127.0.0.1:8000',
]
# Add any additional domains from ALLOWED_HOSTS with proper schemes
for host in ALLOWED_HOSTS:
    if host != '*':
        CSRF_TRUSTED_ORIGINS.extend([
            f'http://{host}',
            f'https://{host}'
        ])

# Add custom local domains for multi-tenant local development
LOCAL_TENANT_DOMAINS = [
    'org001.localhost',
    'org002.localhost',
    'org003.localhost',
    'org004.localhost',
    'org005.localhost',
    'krcs.localhost',
    'oreno.localhost',
]

# Ensure these are in ALLOWED_HOSTS
for domain in LOCAL_TENANT_DOMAINS:
    if domain not in ALLOWED_HOSTS:
        ALLOWED_HOSTS.append(domain)

# Ensure these are in CSRF_TRUSTED_ORIGINS with both http and https
for domain in LOCAL_TENANT_DOMAINS:
    CSRF_TRUSTED_ORIGINS.extend([
        f'http://{domain}',
        f'https://{domain}',
    ])

# ------------------------------------------------------------------------------
# Installed Applications
# ------------------------------------------------------------------------------
INSTALLED_APPS = [
    # Django core
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'django.contrib.postgres',  # optional PostgreSQL extensions
    'django.contrib.sites',  # Required for email absolute URLs

    # Third-party
    'django_tenants', 
    # 'debug_toolbar',  # Temporarily disabled due to missing templates
    'django_ckeditor_5', 
    'widget_tweaks',
    'reversion',
    'crispy_forms',
    'crispy_bootstrap5',
    'django_extensions',
    'rest_framework',
    'rest_framework_simplejwt',  # JWT authentication
    'django_scopes',
    'rest_framework_simplejwt.token_blacklist',
    'django_csp',  # Content Security Policy
    # Note: django-tenants is loaded in tenants.py

    # Local apps
    'organizations.apps.OrganizationsConfig',
    'users.apps.UsersConfig',
    'core.apps.CoreConfig',
    'audit.apps.AuditConfig',
    'admin_module.apps.AdminModuleConfig',
    'compliance.apps.ComplianceConfig',
    'contracts.apps.ContractsConfig',
    'document_management.apps.DocumentManagementConfig',
    'legal.apps.LegalConfig',
    'risk.apps.RiskConfig',
    'reports.apps.ReportsConfig',
    'ai_governance.apps.AIGovernanceConfig',
    
    # Services
    'services.ai.apps.AIServiceConfig',
]

# Apps that should be audited
AUDIT_ENABLED_APPS = [
    'organizations',
    'users',
    'audit',
    'compliance',
    'contracts',
    'document_management',
    'risk',
]

# Custom user model
AUTH_USER_MODEL = 'users.CustomUser'

# ------------------------------------------------------------------------------
# REST Framework Configuration
# ------------------------------------------------------------------------------
REST_FRAMEWORK = {
    # Authentication classes
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework_simplejwt.authentication.JWTAuthentication',
        'rest_framework.authentication.SessionAuthentication',
    ],
    # Default permission classes
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticated',
    ],
    # Pagination settings
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 25,
    # Throttling settings
    'DEFAULT_THROTTLE_CLASSES': [
        'rest_framework.throttling.AnonRateThrottle',
        'rest_framework.throttling.UserRateThrottle'
    ],
    'DEFAULT_THROTTLE_RATES': {
        'anon': '100/day',
        'user': '1000/day'
    },
    # Renderer settings
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
        'rest_framework.renderers.BrowsableAPIRenderer',
    ] if DEBUG else [
        'rest_framework.renderers.JSONRenderer',
    ],
}

# JWT Settings
SIMPLE_JWT = {
    'ACCESS_TOKEN_LIFETIME': timedelta(minutes=60),
    'REFRESH_TOKEN_LIFETIME': timedelta(days=1),
    'ROTATE_REFRESH_TOKENS': True,
    'BLACKLIST_AFTER_ROTATION': True,
    'UPDATE_LAST_LOGIN': True,
    'ALGORITHM': 'HS256',
    'SIGNING_KEY': SECRET_KEY,
    'AUTH_HEADER_TYPES': ('Bearer',),
    'AUTH_HEADER_NAME': 'HTTP_AUTHORIZATION',
    'USER_ID_FIELD': 'id',
    'USER_ID_CLAIM': 'user_id',
    'AUTH_TOKEN_CLASSES': ('rest_framework_simplejwt.tokens.AccessToken',),
}

# Crispy Forms configuration
CRISPY_ALLOWED_TEMPLATE_PACKS = "bootstrap5"
CRISPY_TEMPLATE_PACK = 'bootstrap5'

# Django Scopes
DJANGO_SCOPES_MIDDLEWARE_ENABLED = True
DJANGO_SCOPES_AUTO_CREATE_VIEWS = True

# ------------------------------------------------------------------------------
# Middleware
# ------------------------------------------------------------------------------
MIDDLEWARE = [
    'django_tenants.middleware.TenantMainMiddleware',  # Must be first
    'apps.common.admin_middleware.AdminTenantMiddleware',  # Handle admin tenant issues
    'django.middleware.security.SecurityMiddleware',
    'common.middleware.CSPNonceMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'apps.core.middleware.OrganizationMiddleware',  # Enhanced tenant access control & org context
    'apps.common.middleware.OrganizationActiveMiddleware',
    'apps.common.middleware.AppAccessControlMiddleware',
    'common.middleware.AjaxLoginRequiredMiddleware',
    'common.middleware.LoginRequiredMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'audit.middleware.OrganizationContextMiddleware',  # Enhanced org context enforcement
    'audit.middleware.NotificationAPIMiddleware',  # Handle notifications API gracefully
    'audit.views.RequestWrapper',  # For HTMX attribute handling
]

# Content Security Policy
CSP_DEFAULT_SRC = ("'self'",)
CSP_STYLE_SRC = (
    "'self'",
    "'unsafe-inline'",
    "https://cdn.jsdelivr.net",
    "https://cdnjs.cloudflare.com",
    "https://cdn.ckeditor.com",
    "https://unpkg.com"
)
CSP_SCRIPT_SRC = (
    "'self'",
    "'unsafe-inline'",
    "'unsafe-eval'",
    "https://cdn.jsdelivr.net",
    "https://code.jquery.com",
    "https://unpkg.com",
    "https://cdn.plot.ly",
    "https://www.googletagmanager.com",
    "https://cdnjs.cloudflare.com",
    "https://cdn.ckeditor.com",
    "https://org001.localhost:8000",
    "https://org001.localhost",
    "http://org001.localhost:8000",
    "http://org001.localhost"
)
CSP_IMG_SRC = ("'self'", "data:", "https:")
CSP_FONT_SRC = (
    "'self'",
    "https://cdn.jsdelivr.net",
    "https://cdnjs.cloudflare.com",
    "https://cdn.ckeditor.com",
    "https://unpkg.com"
)
CSP_CONNECT_SRC = ("'self'", "https://api.example.com")
CSP_MEDIA_SRC = ("'self'",)
CSP_OBJECT_SRC = ("'none'",)
CSP_FRAME_SRC = ("'self'",)
CSP_BASE_URI = ("'self'",)
CSP_FORM_ACTION = ("'self'",)
CSP_FRAME_ANCESTORS = ("'self'",)
CSP_BLOCK_ALL_MIXED_CONTENT = True
CSP_INCLUDE_NONCE_IN = ['script-src', 'style-src']

# Enable debug toolbar in debug mode - temporarily disabled due to missing templates
# if DEBUG and 'debug_toolbar' in INSTALLED_APPS:
#    MIDDLEWARE.insert(1, 'debug_toolbar.middleware.DebugToolbarMiddleware')

# ------------------------------------------------------------------------------
# URL & WSGI/ASGI
# ------------------------------------------------------------------------------
ROOT_URLCONF = 'config.urls'
WSGI_APPLICATION = 'config.wsgi.application'
ASGI_APPLICATION = 'config.asgi.application'

# ------------------------------------------------------------------------------
# Templates
# ------------------------------------------------------------------------------
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [
            BASE_DIR / 'templates',
        ],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
                'common.context_processors.csp_nonce',
            ],
        },
    },
]

# -------------------------------------------------------------------
# Database (defaults to SQLite, override via environment for Postgres)
# -------------------------------------------------------------------
DATABASES = {
    'default': {
        # use DB_ENGINE for all backends (Postgres, SQLite, etc.)
        'ENGINE':   os.getenv('DB_ENGINE', 'django.db.backends.sqlite3'),
        # fall back to sqlite3 file if DB_NAME isn't set
        'NAME':     os.getenv('DB_NAME',   BASE_DIR / 'db.sqlite3'),
        # use the same vars you put in .env
        'USER':     os.getenv('DB_USER',   ''),
        'PASSWORD': os.getenv('DB_PASS',   ''),
        'HOST':     os.getenv('DB_HOST',   ''),
        'PORT':     os.getenv('DB_PORT',   '5432'),
        'CONN_MAX_AGE': 60 if not DEBUG else 0,
        'OPTIONS': {
            'connect_timeout': int(os.getenv('DB_CONNECT_TIMEOUT', '10')),
        },
    }
}

DATABASE_ROUTERS = []

# ------------------------------------------------------------------------------
# Caches
# ------------------------------------------------------------------------------
#CACHES = {
#    "default": {
#        "BACKEND": "django_redis.cache.RedisCache",
#        "LOCATION": "redis://127.0.0.1:6379/1",
#        "OPTIONS": {
#            "CLIENT_CLASS": "django_redis.client.DefaultClient",
#        }
#    }
#}

# ------------------------------------------------------------------------------
# Password validation
# ------------------------------------------------------------------------------
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
        'OPTIONS': {
            'max_similarity': 0.7,
        }
    },
    {
        'NAME': 'users.validators.EnhancedPasswordStrengthValidator',
        'OPTIONS': {
            'min_length': 12,
            'max_length': 128,
        }
    },
    {
        'NAME': 'users.validators.PasswordComplexityValidator',
        'OPTIONS': {
            'require_uppercase': True,
            'require_lowercase': True,
            'require_digits': True,
            'require_special': True,
            'min_length': 12,
        }
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
    {
        'NAME': 'users.validators.PasswordHistoryValidator',
        'OPTIONS': {
            'history_count': 8,
            'min_age_days': 1,
        }
    },
    {
        'NAME': 'users.validators.PasswordBreachValidator',
        'OPTIONS': {
            'min_breach_count': 1,
        }
    },
]

# Enhanced password hashers with Argon2 as primary
PASSWORD_HASHERS = [
    'django.contrib.auth.hashers.Argon2PasswordHasher',
    'django.contrib.auth.hashers.PBKDF2PasswordHasher',
    'django.contrib.auth.hashers.PBKDF2SHA1PasswordHasher',
]

# Password policy settings
PASSWORD_POLICY = {
    'DEFAULT_MIN_LENGTH': 12,
    'DEFAULT_MAX_LENGTH': 128,
    'DEFAULT_HISTORY_COUNT': 8,
    'DEFAULT_EXPIRATION_DAYS': 90,
    'DEFAULT_WARNING_DAYS': 14,
    'DEFAULT_MAX_FAILED_ATTEMPTS': 5,
    'DEFAULT_LOCKOUT_DURATION_MINUTES': 15,
    'ENABLE_BREACH_DETECTION': True,
    'ENABLE_PASSWORD_EXPIRATION': True,
    'ENABLE_ACCOUNT_LOCKOUT': True,
}

# Security settings
SECURITY_SETTINGS = {
    'SESSION_COOKIE_SECURE': True,
    'SESSION_COOKIE_HTTPONLY': True,
    'SESSION_COOKIE_SAMESITE': 'Lax',
    'CSRF_COOKIE_SECURE': True,
    'CSRF_COOKIE_HTTPONLY': True,
    'CSRF_COOKIE_SAMESITE': 'Lax',
    'SECURE_BROWSER_XSS_FILTER': True,
    'SECURE_CONTENT_TYPE_NOSNIFF': True,
    'X_FRAME_OPTIONS': 'DENY',
    'SECURE_HSTS_SECONDS': 31536000,  # 1 year
    'SECURE_HSTS_INCLUDE_SUBDOMAINS': True,
    'SECURE_HSTS_PRELOAD': True,
}

# ------------------------------------------------------------------------------
# Internationalization
# ------------------------------------------------------------------------------
LANGUAGE_CODE = 'en-us'
TIME_ZONE = os.getenv('DJANGO_TIME_ZONE', 'UTC')
USE_I18N = True
USE_L10N = True
USE_TZ = True

# ------------------------------------------------------------------------------
# Static & Media files
# ------------------------------------------------------------------------------
STATIC_URL = '/static/'
STATICFILES_DIRS = [
    BASE_DIR / 'static',
]
STATIC_ROOT = BASE_DIR / 'staticfiles'

# Static files finders
STATICFILES_FINDERS = [
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
]

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / 'media'

# CKEditor settings
CKEDITOR_UPLOAD_PATH = 'uploads/'
CKEDITOR_IMAGE_BACKEND = 'pillow'
CKEDITOR_CONFIGS = {
    'extends': {
        'skin': 'moono-lisa',
        'toolbar_Basic': [
            ['Source', '-', 'Bold', 'Italic']
        ],
        'toolbar_Full': [
            ['Styles', 'Format', 'Bold', 'Italic', 'Underline', 'Strike', 'SpellChecker', 'Undo', 'Redo'],
            ['Link', 'Unlink', 'Anchor'],
            ['Image', 'Flash', 'Table', 'HorizontalRule'],
            ['TextColor', 'BGColor'],
            ['Smiley', 'SpecialChar'], ['Source'],
        ],
        'toolbar': 'Full',
        'height': 291,
        'width': '100%',
        'filebrowserWindowWidth': 940,
        'filebrowserWindowHeight': 725,
    }
}

# CKEditor static files
CKEDITOR_BASEPATH = '/static/django_ckeditor_5/'

# ------------------------------------------------------------------------------
# Security headers
# ------------------------------------------------------------------------------
if not DEBUG:
    SECURE_BROWSER_XSS_FILTER = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    X_FRAME_OPTIONS = 'DENY'
    SECURE_HSTS_SECONDS = int(os.getenv('SECURE_HSTS_SECONDS', 3600))
    SECURE_SSL_REDIRECT = os.getenv('SECURE_SSL_REDIRECT', 'True').lower() in ('true','1','yes')

# Session settings
SESSION_COOKIE_AGE = 3600  # 1 hour
SESSION_SAVE_EVERY_REQUEST = True
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SAMESITE = 'Lax'

# CSRF settings
CSRF_COOKIE_HTTPONLY = False
CSRF_COOKIE_SAMESITE = 'Lax'

# ------------------------------------------------------------------------------
# Debug toolbar
# ------------------------------------------------------------------------------
INTERNAL_IPS = ['127.0.0.1']

# ------------------------------------------------------------------------------
# Logging
# ------------------------------------------------------------------------------
LOG_DIR = BASE_DIR / 'config' / 'logs'
LOG_DIR.mkdir(parents=True, exist_ok=True)

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'standard': {
            'format': '[%(asctime)s] %(levelname)s %(name)s: %(message)s',
            'datefmt': '%Y-%m-%d %H:%M:%S'
        },
        'verbose': {
            'format': '[%(asctime)s] %(levelname)s [%(name)s:%(lineno)s] %(message)s',
            'datefmt': '%Y-%m-%d %H:%M:%S'
        },
    },
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
            'formatter': 'standard',
        },
        'file': {
            'level': 'INFO',
            'class': 'logging.handlers.WatchedFileHandler',
            'formatter': 'verbose',
            'filename': str(LOG_DIR / 'django.log'),
            'encoding': 'utf-8',
        },
        'error_file': {
            'level': 'ERROR',
            'class': 'logging.handlers.WatchedFileHandler',
            'formatter': 'verbose',
            'filename': str(LOG_DIR / 'error.log'),
            'encoding': 'utf-8',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['console', 'file', 'error_file'],
            'level': 'INFO',
            'propagate': True,
        },
        **{app: {
            'handlers': ['file', 'error_file'],
            'level': 'DEBUG',
            'propagate': False,
        } for app in [
            'organizations','users','core','audit','admin_module',
            'compliance','contracts','document_management','risk'
        ]},
    }
}

# ------------------------------------------------------------------------------
# Default primary key field
# ------------------------------------------------------------------------------
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# ------------------------------------------------------------------------------
# Email Configuration
# ------------------------------------------------------------------------------
EMAIL_BACKEND = os.getenv('EMAIL_BACKEND', 'django.core.mail.backends.console.EmailBackend')
EMAIL_HOST = os.getenv('EMAIL_HOST', 'localhost')
EMAIL_PORT = int(os.getenv('EMAIL_PORT', 25))
EMAIL_HOST_USER = os.getenv('EMAIL_HOST_USER', '')
EMAIL_HOST_PASSWORD = os.getenv('EMAIL_HOST_PASSWORD', '')
EMAIL_USE_TLS = os.getenv('EMAIL_USE_TLS', 'True').lower() in ('true', '1', 'yes')
DEFAULT_FROM_EMAIL = os.getenv('DEFAULT_FROM_EMAIL', 'info@oreno.tech')
EMAIL_TIMEOUT = 30  # seconds


# ------------------------------------------------------------------------------
# Login redirection
# ------------------------------------------------------------------------------
LOGIN_REDIRECT_URL = '/'
LOGIN_URL = '/accounts/login/'
LOGOUT_REDIRECT_URL = '/accounts/logout/'
LOGIN_REQUIRED_EXEMPT_URLS = [
    '/accounts/login/',         # login view
    '/accounts/logout/',        # logout view
    '/admin/',
    '/accounts/register/',     # your registration view
    '/accounts/password-reset/',   # if applicable
    '/accounts/password-reset/done/',
    '/accounts/password-reset/confirm/',
    '/accounts/password-reset/complete/',
    '/static/', '/media/', '/favicon.ico',
    '/organizations/create/',
    '/',                       # home page
]

# ------------------------------------------------------------------------------
# File Upload Settings
# ------------------------------------------------------------------------------
FILE_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024  # 10MB
DATA_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024  # 10MB
DATA_UPLOAD_MAX_NUMBER_FIELDS = 1000

# ------------------------------------------------------------------------------
# Custom Settings
# ------------------------------------------------------------------------------
# Maximum number of failed login attempts before account is locked
MAX_LOGIN_ATTEMPTS = 5
# Time in minutes to lock account after max attempts
LOGIN_LOCKOUT_TIME = 15

# OTP settings
OTP_EXPIRY_MINUTES = 5
OTP_MAX_ATTEMPTS = 3

# Organization settings
DEFAULT_ORGANIZATION_ROLE = 'staff'
ORGANIZATION_ADMIN_ROLES = ['admin', 'manager']

#*****************************************New Era*********************************
# ------------------------------------------------------------------------------
# Third-party App Configurations
# ------------------------------------------------------------------------------

# Custom color palette for tables and other features
customColorPalette = [
    {
        'color': 'hsl(4, 90%, 58%)',
        'label': 'Red'
    },
    {
        'color': 'hsl(340, 82%, 52%)',
        'label': 'Pink'
    },
    {
        'color': 'hsl(291, 64%, 42%)',
        'label': 'Purple'
    },
    {
        'color': 'hsl(262, 52%, 47%)',
        'label': 'Deep Purple'
    },
    {
        'color': 'hsl(231, 48%, 48%)',
        'label': 'Indigo'
    },
    {
        'color': 'hsl(207, 90%, 54%)',
        'label': 'Blue'
    },
]

# CKEditor 5 configuration
CKEDITOR_5_CONFIGS = {
    'default': {
        'toolbar': ['heading', '|', 'bold', 'italic', 'link',
                    'bulletedList', 'numberedList', 'blockQuote', ],
    },
    'extends': {
        'blockToolbar': [
            'paragraph', 'heading1', 'heading2', 'heading3',
            '|',
            'bulletedList', 'numberedList',
            '|',
            'blockQuote',
        ],
        'toolbar': ['heading', '|', 'outdent', 'indent', '|', 'bold', 'italic', 'link', 'underline', 'strikethrough',
                    'code', 'subscript', 'superscript', 'highlight', '|',
                    'bulletedList', 'numberedList', 'todoList', '|', 'blockQuote', 'imageUpload', '|',
                    'fontSize', 'fontFamily', 'fontColor', 'fontBackgroundColor', 'mediaEmbed', 'removeFormat',
                    'insertTable', ],
        'image': {
            'toolbar': ['imageTextAlternative', '|', 'imageStyle:alignLeft',
                        'imageStyle:alignRight', 'imageStyle:alignCenter', 'imageStyle:side', '|'],
            'styles': [
                'full',
                'side',
                'alignLeft',
                'alignRight',
                'alignCenter',
            ]
        },
        'table': {
            'contentToolbar': ['tableColumn', 'tableRow', 'mergeTableCells',
                               'tableProperties', 'tableCellProperties'],
        },
        'heading': {
            'options': [
                {'model': 'paragraph', 'title': 'Paragraph', 'class': 'ck-heading_paragraph'},
                {'model': 'heading1', 'view': 'h1', 'title': 'Heading 1', 'class': 'ck-heading_heading1'},
                {'model': 'heading2', 'view': 'h2', 'title': 'Heading 2', 'class': 'ck-heading_heading2'},
                {'model': 'heading3', 'view': 'h3', 'title': 'Heading 3', 'class': 'ck-heading_heading3'}
            ]
        },

    },
    'list': {
        'properties': {
            'styles': 'true',
            'startIndex': 'true',
            'reversed': 'true',
        }
    }
}

# CKEditor 5 file storage
CKEDITOR_5_FILE_STORAGE = "django.core.files.storage.FileSystemStorage"

# Absolute site URL for building links in emails, etc.
SITE_URL = "http://org001.localhost:8000"

# Django Sites framework configuration
SITE_ID = 1  # Default site ID
SITE_DOMAIN = os.getenv('SITE_DOMAIN', 'org001.localhost:8000')
