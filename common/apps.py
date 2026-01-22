# common/apps.py
from django.apps import AppConfig
from django.utils.translation import gettext_lazy as _


class CommonConfig(AppConfig):
    name = 'common'
    verbose_name = _('Common')
    default_auto_field = 'django.db.models.BigAutoField'

    def ready(self):
        # Import any signals or initialization code here if needed
        pass
