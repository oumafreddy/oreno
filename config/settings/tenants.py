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
# Shared apps (public schema only)
# ------------------------------------------------------------------------------
SHARED_APPS = [
    # core tenant machinery
    'django_tenants',

    # Django framework dependencies
    'django.contrib.contenttypes',
    'django.contrib.auth',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.admin',
    'django.contrib.staticfiles',

    # Tenant definition + public models
    'organizations.apps.OrganizationsConfig',  # Tenant and Domain models
    'users.apps.UsersConfig',                  # CustomUser lives here
]

# ------------------------------------------------------------------------------
# Tenant-specific apps (one schema per tenant)
# ------------------------------------------------------------------------------
TENANT_APPS = [
    # Core application logic
    'core.apps.CoreConfig',
    'audit.apps.AuditConfig',
    'admin_module.apps.AdminModuleConfig',
    'compliance.apps.ComplianceConfig',
    'contracts.apps.ContractsConfig',
    'document_management.apps.DocumentManagementConfig',
    'risk.apps.RiskConfig',

    # Third-party integrations
    'rest_framework',
    'crispy_forms',
    'crispy_bootstrap5',
    'django_extensions',
    'django_scopes',
]

# ------------------------------------------------------------------------------
# Combine shared + tenant apps
# ------------------------------------------------------------------------------
INSTALLED_APPS = SHARED_APPS + [app for app in TENANT_APPS if app not in SHARED_APPS]

# ------------------------------------------------------------------------------
# Middleware: ensure TenantMainMiddleware is first and TenantSyncRouter is placed
# ------------------------------------------------------------------------------
"""
MIDDLEWARE = [
    'django_tenants.middleware.TenantMainMiddleware',
] + MIDDLEWARE + [
    'django_tenants.middleware.TenantSyncRouter',
]
"""

"""
# **************************
MIDDLEWARE = [
    # — tenant setup must come first —
    'django_tenants.middleware.TenantMainMiddleware',

    # Standard Django middleware
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',

    # Optional per‑request tenant routing if you need it:
    # 'django_tenants.middleware.TenantMiddleware',

    # Custom/3rd‑party
    # 'django_scopes.middleware.ScopeMiddleware',
    'apps.core.middleware.OrganizationMiddleware',
    'common.middleware.LoginRequiredMiddleware',
]
"""

MIDDLEWARE = [
    'django_tenants.middleware.TenantMainMiddleware',
    *MIDDLEWARE,  # from base.py
    #'django_tenants.middleware.TenantSyncRouter',
]

# **************************
# ------------------------------------------------------------------------------
# Database: use django-tenants PostgreSQL backend
# ------------------------------------------------------------------------------
DATABASES = {
    'default': {
        'ENGINE': 'django_tenants.postgresql_backend',
        'NAME': os.getenv('POSTGRES_DB', 'oreno'),
        'USER': os.getenv('POSTGRES_USER', 'ouma_fred'),
        'PASSWORD': os.getenv('POSTGRES_PASSWORD', '123@Team*'),
        'HOST': os.getenv('POSTGRES_HOST', 'localhost'),
        'PORT': os.getenv('POSTGRES_PORT', '5432'),
    }
}

# ------------------------------------------------------------------------------
# Ensure tenant routing
# ------------------------------------------------------------------------------
DATABASE_ROUTERS = (
    'django_tenants.routers.TenantSyncRouter',
)
