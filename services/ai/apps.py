from django.apps import AppConfig


class AIServiceConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'services.ai'
    verbose_name = 'AI Service'
    
    def ready(self):
        """Initialize AI service when Django starts"""
        try:
            # Import and initialize AI service components
            from . import ai_service
            from . import ollama_adapter
            from . import llm_adapter
            
            # Log successful initialization
            import logging
            logger = logging.getLogger('services.ai.apps')
            logger.info('AI Service initialized successfully')
            
        except Exception as e:
            import logging
            logger = logging.getLogger('services.ai.apps')
            logger.error(f'Failed to initialize AI Service: {e}')
