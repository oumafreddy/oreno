"""
Ollama configuration settings for the AI service.
This module provides configuration options for the Ollama integration.
"""
import os
from django.conf import settings

# Ollama API settings
OLLAMA_BASE_URL = getattr(settings, 'OLLAMA_BASE_URL', os.getenv('OLLAMA_BASE_URL', 'http://localhost:11434'))
OLLAMA_MODEL = getattr(settings, 'OLLAMA_MODEL', os.getenv('OLLAMA_MODEL', 'llama3'))

# LLM Provider settings
LLM_PROVIDER = getattr(settings, 'LLM_PROVIDER', os.getenv('LLM_PROVIDER', 'ollama')).lower()
ENABLE_OPENAI_FALLBACK = getattr(
    settings, 
    'ENABLE_OPENAI_FALLBACK', 
    os.getenv('ENABLE_OPENAI_FALLBACK', 'false')
).lower() == 'true'

# Model configuration
DEFAULT_MAX_TOKENS = int(getattr(settings, 'OLLAMA_MAX_TOKENS', os.getenv('OLLAMA_MAX_TOKENS', 512)))
DEFAULT_TEMPERATURE = float(getattr(settings, 'OLLAMA_TEMPERATURE', os.getenv('OLLAMA_TEMPERATURE', 0.3)))

# Available Ollama models (add more as needed)
AVAILABLE_MODELS = [
    'llama3',
    'llama3:8b',
    'llama3:70b',
    'mistral',
    'gemma:2b',
    'gemma:7b',
    'phi',
    'phi:2.7b',
    'codellama',
    'neural-chat'
]
