import os
from pathlib import Path

from .base import *  # noqa: F401, F403

# ------------------------------------------------------------------------------
# django-tenants configuration
# ------------------------------------------------------------------------------
# Which model represents your tenant (must inherit TenantMixin)
TENANT_MODEL = "organizations.Organization"
# Which model holds the domains for each tenant
TENANT_DOMAIN_MODEL = "organizations.Domain"

# ------------------------------------------------------------------------------
# Tenant Schema Configuration
# ------------------------------------------------------------------------------
# Schema name format for new tenants
TENANT_SCHEMA_NAME_FORMAT = "{schema_name}"
# Whether to create schema automatically when creating a tenant
TENANT_CREATE_SCHEMA_AUTOMATICALLY = True
# Whether to sync schema automatically when creating a tenant
TENANT_SYNC_SCHEMA_AUTOMATICALLY = True
# Whether to create public schema automatically
TENANT_CREATE_PUBLIC_SCHEMA_AUTOMATICALLY = True
# Whether to create public tenant automatically
TENANT_CREATE_PUBLIC_TENANT_AUTOMATICALLY = True

# ------------------------------------------------------------------------------
# Tenant URL Configuration
# ------------------------------------------------------------------------------
# URL pattern for tenant-specific URLs
TENANT_URL_PATTERN = r"^(?P<tenant>[\w-]+)/"
# Whether to show public schema if no tenant is found
SHOW_PUBLIC_IF_NO_TENANT_FOUND = True
# URL configuration for public schema
PUBLIC_SCHEMA_URLCONF = 'config.urls_public'

# ------------------------------------------------------------------------------
# Tenant Database Configuration
# ------------------------------------------------------------------------------
# Database engine for tenant schemas
TENANT_DB_ENGINE = 'django_tenants.postgresql_backend'
# Database name for tenant schemas
TENANT_DB_NAME = os.getenv('DB_NAME', ' ')
# Database user for tenant schemash 
TENANT_DB_USER = os.getenv('DB_USER', ' ')
# Database password for tenant schemas
TENANT_DB_PASSWORD = os.getenv('DB_PASS', ' ')
# Database host for tenant schemas
TENANT_DB_HOST = os.getenv('DB_HOST', 'db')
# Database port for tenant schemas
TENANT_DB_PORT = os.getenv('DB_PORT', '5432')

# ------------------------------------------------------------------------------
# Shared Apps (public schema only)
# ------------------------------------------------------------------------------
SHARED_APPS = [
    # Core tenant machinery
    'django_tenants',

    # Django framework dependencies
    'django.contrib.contenttypes',
    'django.contrib.auth',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.admin',
    'django.contrib.staticfiles',
    'django.contrib.sitemaps',

    'reversion',          # Version control
    'django_ckeditor_5',  # Rich text editor

    # Tenant definition + public models
    'organizations.apps.OrganizationsConfig',  # Tenant and Domain models
    'users.apps.UsersConfig',  
    'core.apps.CoreConfig',    # Core functionality including audit logging
]

# ------------------------------------------------------------------------------
# Tenant-specific Apps (one schema per tenant)
# ------------------------------------------------------------------------------
TENANT_APPS = [
    'reversion',
    'django_ckeditor_5',  # Rich text editor
    # Core application logic
    'core.apps.CoreConfig',  # Core functionality in tenant context
    'audit.apps.AuditConfig',  # Audit management (workplans, engagements, issues)
    'admin_module.apps.AdminModuleConfig',
    'compliance.apps.ComplianceConfig',
    'contracts.apps.ContractsConfig',
    'document_management.apps.DocumentManagementConfig',
    'legal.apps.LegalConfig',
    'risk.apps.RiskConfig',
    'ai_governance.apps.AIGovernanceConfig',
    'services.agent.apps.AgentConfig',

    # Third-party integrations
    'rest_framework',
    'crispy_forms',    
    'crispy_bootstrap5',    
    'django_scopes',
]

# ------------------------------------------------------------------------------
# Combine shared + tenant apps
# ------------------------------------------------------------------------------
INSTALLED_APPS = SHARED_APPS + [app for app in TENANT_APPS if app not in SHARED_APPS]

# ------------------------------------------------------------------------------
# Middleware: inherit from base.py, do not prepend TenantMainMiddleware again
MIDDLEWARE = [
    *MIDDLEWARE,  # from base.py
    # Add any tenant-specific middleware here if needed
]

# ------------------------------------------------------------------------------
# Database: use django-tenants PostgreSQL backend
# ------------------------------------------------------------------------------
DATABASES = {
    'default': {
        'ENGINE': TENANT_DB_ENGINE,
        'NAME': TENANT_DB_NAME,
        'USER': TENANT_DB_USER,
        'PASSWORD': TENANT_DB_PASSWORD,
        'HOST': TENANT_DB_HOST,
        'PORT': TENANT_DB_PORT,
        'CONN_MAX_AGE': 60 if not DEBUG else 0,  # Persistent connections in production
        'OPTIONS': {
            'connect_timeout': 10,  # Connection timeout in seconds
        },
    }
}

# ------------------------------------------------------------------------------
# Ensure tenant routing
# ------------------------------------------------------------------------------
DATABASE_ROUTERS = (
    'django_tenants.routers.TenantSyncRouter',
)

# ------------------------------------------------------------------------------
# Tenant Cache Configuration
# ------------------------------------------------------------------------------
# Cache prefix for tenant-specific caches
TENANT_CACHE_PREFIX = 'tenant_{schema_name}_'
# Whether to use tenant-specific cache
TENANT_USE_CACHE = True
# Cache timeout for tenant-specific caches
TENANT_CACHE_TIMEOUT = 300  # 5 minutes

# ------------------------------------------------------------------------------
# Tenant Media Configuration
# ------------------------------------------------------------------------------
# Media root for tenant-specific media
TENANT_MEDIA_ROOT = BASE_DIR / 'media' / 'tenants'
# Media URL for tenant-specific media
TENANT_MEDIA_URL = '/media/tenants/'
# Whether to use tenant-specific media
TENANT_USE_MEDIA = True

# ------------------------------------------------------------------------------
# Tenant Static Configuration
# ------------------------------------------------------------------------------
# Static root for tenant-specific static files
TENANT_STATIC_ROOT = BASE_DIR / 'static' / 'tenants'
# Static URL for tenant-specific static files
TENANT_STATIC_URL = '/static/tenants/'
# Whether to use tenant-specific static files
TENANT_USE_STATIC = True

# ------------------------------------------------------------------------------
# Tenant Email Configuration
# ------------------------------------------------------------------------------
# Email backend for tenant-specific emails
TENANT_EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
# Email host for tenant-specific emails
TENANT_EMAIL_HOST = os.getenv('TENANT_EMAIL_HOST', EMAIL_HOST)
# Email port for tenant-specific emails
TENANT_EMAIL_PORT = int(os.getenv('TENANT_EMAIL_PORT', EMAIL_PORT))
# Email user for tenant-specific emails
TENANT_EMAIL_HOST_USER = os.getenv('TENANT_EMAIL_HOST_USER', EMAIL_HOST_USER)
# Email password for tenant-specific emails
TENANT_EMAIL_HOST_PASSWORD = os.getenv('TENANT_EMAIL_HOST_PASSWORD', EMAIL_HOST_PASSWORD)
# Whether to use TLS for tenant-specific emails
TENANT_EMAIL_USE_TLS = os.getenv('TENANT_EMAIL_USE_TLS', 'False').lower() in ('true', '1', 'yes')
# Whether to use SSL for tenant-specific emails
TENANT_EMAIL_USE_SSL = os.getenv('TENANT_EMAIL_USE_SSL', 'True').lower() in ('true', '1', 'yes')
# Default from email for tenant-specific emails
TENANT_DEFAULT_FROM_EMAIL = os.getenv('TENANT_DEFAULT_FROM_EMAIL', DEFAULT_FROM_EMAIL)
# Email timeout for tenant-specific emails
TENANT_EMAIL_TIMEOUT = 30  # seconds

# ------------------------------------------------------------------------------
# Tenant Logging Configuration
# ------------------------------------------------------------------------------
# Log directory for tenant-specific logs
TENANT_LOG_DIR = BASE_DIR / 'config' / 'logs' / 'tenants'
# Whether to use tenant-specific logging
TENANT_USE_LOGGING = True
# Log format for tenant-specific logs
TENANT_LOG_FORMAT = '[%(asctime)s] %(levelname)s [%(name)s:%(lineno)s] [%(tenant)s] %(message)s'
# Log date format for tenant-specific logs
TENANT_LOG_DATE_FORMAT = '%Y-%m-%d %H:%M:%S'