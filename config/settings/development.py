from .base import *

# ------------------------------------------------------------------------------
# Development-Specific Overrides
# ------------------------------------------------------------------------------

DEBUG = True

# Use a simple secret key for development (override in production)
SECRET_KEY = os.getenv('DJANGO_SECRET_KEY', 'development-secret-key')

ALLOWED_HOSTS = ["localhost", "127.0.0.1"]

# ------------------------------------------------------------------------------
# Development Tools Configuration
# ------------------------------------------------------------------------------

# Add debug_toolbar only in development
INSTALLED_APPS += [
    "debug_toolbar",
]

# Insert Debug Toolbar middleware early in the chain
MIDDLEWARE.insert(
    1,  # Position after SecurityMiddleware
    "debug_toolbar.middleware.DebugToolbarMiddleware"
)

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