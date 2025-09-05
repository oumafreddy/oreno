from django.apps import AppConfig


class AIGovernanceConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'ai_governance'
    verbose_name = 'AI Governance'

    def ready(self):
        import ai_governance.signals  # noqa

