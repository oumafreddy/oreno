"""
Test settings for pytest.

Goals:
- Keep the test environment lightweight and deterministic
- Avoid optional developer tooling (e.g. debug toolbar) interfering with responses
- Avoid expensive tenant schema creation/migrations during unit tests
"""

from .development import *  # noqa

# ---------------------------------------------------------------------------
# Make tests stable: no debug toolbar, no extra middleware side effects
# ---------------------------------------------------------------------------
DEBUG_TOOLBAR = False

# Remove debug-toolbar middleware/app if development.py enabled it
INSTALLED_APPS = [app for app in INSTALLED_APPS if app != "debug_toolbar"]  # type: ignore[name-defined]
MIDDLEWARE = [mw for mw in MIDDLEWARE if mw != "debug_toolbar.middleware.DebugToolbarMiddleware"]  # type: ignore[name-defined]

# ---------------------------------------------------------------------------
# Tenant behavior: keep pytest fast (no schema create/migrate per tenant)
# ---------------------------------------------------------------------------
TENANT_CREATE_SCHEMA_AUTOMATICALLY = False
TENANT_SYNC_SCHEMA_AUTOMATICALLY = False

