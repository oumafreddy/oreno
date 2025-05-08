# apps/core/apps.py
from django.apps import AppConfig

class DocumentManagementConfig(AppConfig):
    name = 'document_management'
    verbose_name = "Document Management"
    # …or…
    # name = 'apps.core'  # if you prefer fully qualified imports without altering sys.path

    def ready(self):
        import document_management.signals  # noqa
