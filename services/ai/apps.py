from django.apps import AppConfig


class AIConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'services.ai'
    verbose_name = 'AI Assistant'
    
    def ready(self):
        """Import signals when the app is ready."""
        try:
            import services.ai.signals  # noqa
        except ImportError:
            pass
