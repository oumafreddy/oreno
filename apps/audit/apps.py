# apps/audit/apps.py
from django.apps import AppConfig

class AuditConfig(AppConfig):
    name = 'audit'
    # …or…
    # name = 'apps.core'  # if you prefer fully qualified imports without altering sys.path
    verbose_name = 'Audit'

    def ready(self):
        import audit.signals
