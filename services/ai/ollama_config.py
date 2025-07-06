"""
Configuration for Ollama integration
"""

import os
from django.conf import settings

# Ollama API configuration
OLLAMA_BASE_URL = os.getenv('OLLAMA_BASE_URL', 'http://localhost:11434')

# Model configuration - use llama3:8b as the primary model
OLLAMA_MODEL = os.getenv('OLLAMA_MODEL', 'llama3:8b')

# Available models (only include what the user actually has installed)
AVAILABLE_MODELS = [
    'llama3:8b',
]

# Generation parameters
DEFAULT_MAX_TOKENS = int(os.getenv('OLLAMA_MAX_TOKENS', '2048'))
DEFAULT_TEMPERATURE = float(os.getenv('OLLAMA_TEMPERATURE', '0.7'))

# Timeout settings
REQUEST_TIMEOUT = int(os.getenv('OLLAMA_TIMEOUT', '60'))

# Logging configuration
LOG_LEVEL = os.getenv('OLLAMA_LOG_LEVEL', 'INFO')

# LLM Provider settings
LLM_PROVIDER = getattr(settings, 'LLM_PROVIDER', os.getenv('LLM_PROVIDER', 'ollama')).lower()
ENABLE_OPENAI_FALLBACK = getattr(
    settings, 
    'ENABLE_OPENAI_FALLBACK', 
    os.getenv('ENABLE_OPENAI_FALLBACK', 'true')
).lower() == 'true'
