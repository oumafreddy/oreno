# apps/core/apps.py
from django.apps import AppConfig

class RiskConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'risk'

    def ready(self):
        import risk.signals  # noqa
    # …or…
    # name = 'apps.core'  # if you prefer fully qualified imports without altering sys.path
