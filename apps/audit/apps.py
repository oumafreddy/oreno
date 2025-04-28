# apps/audit/apps.py
from django.apps import AppConfig

class AuditConfig(AppConfig):
    name = 'audit'        # if using sys.path hack and __init__.py added
    # …or…
    # name = 'apps.core'  # if you prefer fully qualified imports without altering sys.path
    verbose_name = 'Audit Management'

    def ready(self):
        import audit.signals  # noqa
