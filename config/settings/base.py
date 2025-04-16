import os
import sys
from pathlib import Path

from dotenv import load_dotenv


# ------------------------------------------------------------------------------
# Base Directories and System Path Modification
# ------------------------------------------------------------------------------

BASE_DIR = Path(__file__).resolve().parent.parent.parent
load_dotenv(BASE_DIR / '.env')  # Explicitly load from the root
APPS_DIR = BASE_DIR / 'apps'
# Ensure apps are discoverable without having to prefix them with 'apps.' in imports
sys.path.append(str(APPS_DIR))

# ------------------------------------------------------------------------------
# Security Configuration
# ------------------------------------------------------------------------------

# Secret Key: Raise an exception if not set to ensure secure operations in production.
SECRET_KEY = os.getenv('DJANGO_SECRET_KEY')
if not SECRET_KEY:
    raise Exception("DJANGO_SECRET_KEY environment variable not set. Set this variable for secure operation.")

# DEBUG: Handles boolean conversion robustly. In production, ensure this is False.
DEBUG = os.getenv('DJANGO_DEBUG', 'True').lower() in ['true', '1', 'yes']

# Allowed Hosts: Default to '*' for development, but production should override this.
ALLOWED_HOSTS = os.getenv('DJANGO_ALLOWED_HOSTS', '*').split(',')

# ------------------------------------------------------------------------------
# Application Definition
# ------------------------------------------------------------------------------

INSTALLED_APPS = [
    # Django defaults
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',

    # Optional Django PostgreSQL features for future use.
    'django.contrib.postgres',

    # Third-party apps (include as needed)
    'debug_toolbar',         # Only during development
    'crispy_forms',
    'crispy_bootstrap5',
    'django_extensions',     # Useful for debugging tools and graph models
    'rest_framework',        # For API integrations

    # Local Apps (order matters for dependencies)
    'apps.organizations',    # Manages tenant organization details
    'apps.users',            # Custom user model should be declared here
    'apps.audit',
    'apps.core',             # Base models, utilities, and middleware
    'apps.admin_module',
    'apps.compliance',
    'apps.contracts',
    'apps.document_management',
    'apps.risk',
]

# Custom user model
AUTH_USER_MODEL = 'users.CustomUser'

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

# Optional: Path to custom CSS file for CKEditor

# Or use default storage
CKEDITOR_5_FILE_STORAGE = "django.core.files.storage.FileSystemStorage"

# CKEditor configuration
CKEDITOR_5_CONFIGS = {
    'default': {
        'toolbar': ['heading', '|', 'bold', 'italic', 'link',
                    'bulletedList', 'numberedList', 'blockQuote', 'imageUpload', ],
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
                    'code', 'subscript', 'superscript', 'highlight', '|', 'codeBlock', 'sourceEditing', 'insertImage',
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
            'tableProperties': {
                'borderColors': customColorPalette,
                'backgroundColors': customColorPalette
            },
            'tableCellProperties': {
                'borderColors': customColorPalette,
                'backgroundColors': customColorPalette
            }
        },
        'heading': {
            'options': [
                {'model': 'paragraph', 'title': 'Paragraph', 'class': 'ck-heading_paragraph'},
                {'model': 'heading1', 'view': 'h1', 'title': 'Heading 1', 'class': 'ck-heading_heading1'},
                {'model': 'heading2', 'view': 'h2', 'title': 'Heading 2', 'class': 'ck-heading_heading2'},
                {'model': 'heading3', 'view': 'h3', 'title': 'Heading 3', 'class': 'ck-heading_heading3'}
            ]
        }
    },
    'list': {
        'properties': {
            'styles': 'true',
            'startIndex': 'true',
            'reversed': 'true',
        }
    }
}

# Crispy Forms configuration
CRISPY_ALLOWED_TEMPLATE_PACKS = "bootstrap5"
CRISPY_TEMPLATE_PACK = 'bootstrap5'

# ------------------------------------------------------------------------------
# Middleware Configuration
# ------------------------------------------------------------------------------
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'debug_toolbar.middleware.DebugToolbarMiddleware',  # Should be enabled in dev only
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    # Set tenant organization context early on.
    'apps.core.middleware.OrganizationMiddleware',
    # Enforces login for protected views.
    'common.middleware.LoginRequiredMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

# ------------------------------------------------------------------------------
# URL and WSGI/ASGI Application Settings
# ------------------------------------------------------------------------------

ROOT_URLCONF = 'config.urls'
WSGI_APPLICATION = 'config.wsgi.application'
# If using ASGI, uncomment and configure:
# ASGI_APPLICATION = 'config.asgi.application'

# ------------------------------------------------------------------------------
# Templates Configuration
# ------------------------------------------------------------------------------

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,  # Auto-discovers template directories in installed apps.
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',  # Adds 'request' to the context.
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

# ------------------------------------------------------------------------------
# Database Configuration
# ------------------------------------------------------------------------------
# Using SQLite for development; override this in production with a robust database.
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'db.sqlite3',
    }
}

# ------------------------------------------------------------------------------
# Password Validators
# ------------------------------------------------------------------------------

AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# ------------------------------------------------------------------------------
# Internationalization
# ------------------------------------------------------------------------------
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_L10N = True  # Note: Consider removing for Django 4.x and newer as it's deprecated.
USE_TZ = True

# ------------------------------------------------------------------------------
# Static and Media Files
# ------------------------------------------------------------------------------
STATIC_URL = '/static/'
STATICFILES_DIRS = [BASE_DIR / "static"]
STATIC_ROOT = BASE_DIR / "staticfiles"

MEDIA_URL = '/media/'
MEDIA_ROOT = BASE_DIR / "media"

# ------------------------------------------------------------------------------
# Security Headers (Enhanced for Production)
# ------------------------------------------------------------------------------
if not DEBUG:
    SECURE_BROWSER_XSS_FILTER = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    X_FRAME_OPTIONS = 'DENY'

# ------------------------------------------------------------------------------
# Debug Toolbar Configuration
# ------------------------------------------------------------------------------
INTERNAL_IPS = ['127.0.0.1']

# ------------------------------------------------------------------------------
# Logging Configuration (Includes Console and Rotating File Handler)
# ------------------------------------------------------------------------------
# Create logs directory if it doesn't exist
LOG_DIR = BASE_DIR / 'config' / 'logs'
LOG_DIR.mkdir(parents=True, exist_ok=True)

LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'handlers': {
        'console': {
            'class': 'logging.StreamHandler',
        },
        'file': {
            'level': 'INFO',
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': LOG_DIR / 'django.log',
            'maxBytes': 1024 * 1024 * 5,  # 5MB per file
            'backupCount': 5,
        },
    },
    'loggers': {
        'django': {
            'handlers': ['console', 'file'],
            'level': 'INFO',
            'propagate': True,
        },
        # Example of more granular logging for specific apps
        'apps.core': {
            'handlers': ['console', 'file'],
            'level': 'DEBUG',
            'propagate': False,
        },
    },
}


# ------------------------------------------------------------------------------
# Default Primary Key Field Type
# ------------------------------------------------------------------------------
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# ------------------------------------------------------------------------------
# Additional Application Settings
# ------------------------------------------------------------------------------

# Multi-Tenancy Settings: For future use with django-tenants or similar multi-tenant packages.
TENANT_MODEL = "organizations.Organization"

# File Upload Settings: Limit upload sizes to 10MB.
ENABLE_VIRUS_SCANNING = os.getenv('ENABLE_VIRUS_SCANNING', 'False').lower() == 'true'
FILE_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024  # 10MB
DATA_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024  # 10MB

# Session Configuration: Adjust session lifetime and behavior.
SESSION_COOKIE_AGE = 86400  # Session lasts for 24 hours
SESSION_SAVE_EVERY_REQUEST = True

# Email Backend: Use console email backend during development.
EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

#--------------------------------------------------------------------------------------------
LOGIN_URL = '/accounts/login/'  # or wherever your login page is

LOGIN_REQUIRED_EXEMPT_URLS = [
    '/accounts/login/',
    '/accounts/signup/',
    '/admin/',           # Exempts all admin URLs
    '/static/',          # Always allow static files
    # Add other paths that should be publicly accessible
]