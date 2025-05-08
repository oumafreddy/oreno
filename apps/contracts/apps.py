# apps/contracts/apps.py
from django.apps import AppConfig

class ContractsConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'contracts'
    verbose_name = "Contracts"

    def ready(self):
        import contracts.signals  # noqa
