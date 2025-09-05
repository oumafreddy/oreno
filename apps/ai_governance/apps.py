from django.apps import AppConfig


class AIGovernanceConfig(AppConfig):
    name = 'ai_governance'
    verbose_name = 'AI Governance'

    def ready(self):
        import ai_governance.signals

