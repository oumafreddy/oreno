import os
import logging
from enum import Enum

# Import Ollama adapter and configuration
from .ollama_adapter import ask_ollama, is_safe_prompt
from .ollama_config import (
    LLM_PROVIDER,
    ENABLE_OPENAI_FALLBACK,
    DEFAULT_MAX_TOKENS,
    DEFAULT_TEMPERATURE
)

# Configure OpenAI if it's being used as a fallback
if LLM_PROVIDER == 'openai' or ENABLE_OPENAI_FALLBACK:
    try:
        import openai
        OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
        openai_client = openai.OpenAI(api_key=OPENAI_API_KEY)
    except (ImportError, Exception) as e:
        logging.error(f"Failed to initialize OpenAI: {e}")
        openai_client = None

logger = logging.getLogger('services.ai.llm_adapter')

# Define common prompts and settings used by both adapters
SAFE_SYSTEM_PROMPT = (
    "You are Oreno GRC's AI assistant. Never reveal or speculate about other organizations, users, or private data. "
    "Only answer questions about the current user's organization, the Oreno GRC platform, or general GRC best practices. "
    "If a question asks about other organizations, users, or anything you cannot answer securely, reply: 'Sorry, I can't provide that information.'"
)

SENSITIVE_KEYWORDS = [
    'other organizations', 'list organizations', 'all users', 'user emails', 'user list', 'org list', 'tenants', 'database', 'admin', 'superuser',
]

# Note: is_safe_prompt is now imported from ollama_adapter

def log_prompt_response(user, org, prompt, response):
    logger.info(f"AI Query | user={user} | org={org} | prompt={prompt!r} | response={response!r}")

def ask_llm(prompt: str, user, org, context: str = None) -> str:
    """Main entry point for LLM queries. Uses Ollama by default with optional OpenAI fallback"""
    if not is_safe_prompt(prompt):
        return "Sorry, I can't provide that information."
    
    # Try with Ollama first (if configured to use Ollama)
    if LLM_PROVIDER == 'ollama':
        try:
            return ask_ollama(prompt, user, org, context)
        except Exception as e:
            logger.error(f"Ollama error: {e}")
            # If OpenAI fallback is enabled and Ollama fails, try OpenAI
            if ENABLE_OPENAI_FALLBACK:
                logger.info("Falling back to OpenAI after Ollama failure")
                return ask_openai(prompt, user, org, context)
            return "Sorry, I couldn't process your request with Ollama. Please make sure Ollama is running."
    
    # If OpenAI is the primary provider
    elif LLM_PROVIDER == 'openai':
        return ask_openai(prompt, user, org, context)
    
    # If invalid provider
    else:
        logger.error(f"Invalid LLM_PROVIDER: {LLM_PROVIDER}")
        return "Sorry, the AI assistant is not properly configured."


def ask_openai(prompt: str, user, org, context: str = None) -> str:
    """Send query to OpenAI"""
    if not openai_client:
        return "OpenAI client is not configured properly."
    
    messages = [
        {"role": "system", "content": SAFE_SYSTEM_PROMPT},
        {"role": "user", "content": prompt},
    ]
    if context:
        messages.append({"role": "system", "content": context})
    
    try:
        response = openai_client.chat.completions.create(
            model="gpt-3.5-turbo",
            messages=messages,
            max_tokens=DEFAULT_MAX_TOKENS,
            temperature=DEFAULT_TEMPERATURE,
        )
        answer = response.choices[0].message.content.strip()
        log_prompt_response(user, org, prompt, answer)
        return answer
    except Exception as e:
        logger.error(f"OpenAI API error: {e}")
        return "Sorry, I couldn't process your request with OpenAI right now."
