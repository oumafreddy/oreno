from django.apps import AppConfig

class LegalConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'legal'
    verbose_name = 'Legal Case Management'

    def ready(self):
        import legal.signals  # noqa 