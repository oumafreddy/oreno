# apps/core/apps.py
from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _

class CoreConfig(AppConfig):
    name = 'core'
    verbose_name = 'Core'
    default_auto_field = 'django.db.models.BigAutoField'

    def ready(self):
        import core.signals  # noqa
