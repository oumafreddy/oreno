from django.apps import AppConfig


class AIGovernanceConfig(AppConfig):
    name = 'ai_governance'
    verbose_name = 'AI Governance'

    def ready(self):
        # Import signals if/when added
        try:
            from . import signals  # noqa: F401
        except Exception:
            pass
