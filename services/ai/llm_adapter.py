import os
import logging
from enum import Enum

# Configure with direct environment variables to avoid circular imports
DEFAULT_MAX_TOKENS = int(os.getenv('OLLAMA_MAX_TOKENS', 512))
DEFAULT_TEMPERATURE = float(os.getenv('OLLAMA_TEMPERATURE', 0.1))
LLM_PROVIDER = os.getenv('LLM_PROVIDER', 'openai')  # Default to OpenAI
ENABLE_OPENAI_FALLBACK = os.getenv('ENABLE_OPENAI_FALLBACK', 'false').lower() == 'true'

# Configure OpenAI client
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
    "You are Oreno GRC's AI assistant specializing in Governance, Risk, and Compliance (GRC). "
    "You have access to real organization data and should use it to provide specific, actionable insights. "
    "Be helpful and informative about GRC topics, audit processes, and compliance. "
    "Use the provided organization data to give specific, relevant answers. "
    "Reference actual numbers and facts from the data when possible. "
    "Provide actionable insights based on the current state. "
    "Focus on the specific organization's context."
)

SENSITIVE_KEYWORDS = [
    'list all organizations', 'show all users', 'user emails', 'user list', 'org list', 'tenants', 'database', 'admin', 'superuser',
    'password', 'api key', 'secret key', 'private data', 'other organizations data',
]

def is_safe_prompt(prompt: str) -> bool:
    """Check if the prompt is safe to send to the LLM"""
    if not prompt or not isinstance(prompt, str):
        return False
        
    # Check for sensitive keywords
    prompt_lower = prompt.lower()
    for keyword in SENSITIVE_KEYWORDS:
        if keyword.lower() in prompt_lower:
            return False
            
    return True

def log_prompt_response(user, org, prompt, response):
    logger.info(f"AI Query | user={user} | org={org} | prompt={prompt!r} | response={response!r}")

def ask_llm(prompt: str, user, org, context: str = None, system_prompt: str = None, return_meta: bool = False):
    """
    Main entry point for LLM queries. Uses OpenAI.
    
    Args:
        prompt: User prompt
        user: User object
        org: Organization object
        context: Additional context string
        system_prompt: Custom system prompt (overrides default)
        return_meta: If True, returns tuple (response, metadata_dict), else just response string
    
    Returns:
        str if return_meta=False, tuple (str, dict) if return_meta=True
    """
    if not is_safe_prompt(prompt):
        error_response = "Sorry, I can't provide that information."
        if return_meta:
            return error_response, {'error': 'Unsafe prompt', 'provider': 'openai'}
        return error_response
    
    # Add GRC-specific context to every prompt to help the model stay on topic (unless custom system prompt)
    if not system_prompt:
        grc_context = (
            "GRC stands for Governance, Risk, and Compliance.\n"
            "- Governance refers to the management and leadership structures and processes that ensure an organization meets its objectives.\n"
            "- Risk management involves identifying, assessing, and mitigating risks to the organization.\n"
            "- Compliance means ensuring the organization adheres to all relevant laws, regulations, and standards.\n\n"
        )
        
        # Add organization context if available
        org_context = ""
        if org:
            org_context = f"\nORGANIZATION CONTEXT: You are assisting {org.name} (ID: {org.id}). Only provide information relevant to this organization.\n"
        
        # Combine the GRC context with the user's prompt
        enhanced_prompt = grc_context + org_context + "Question: " + prompt
    else:
        enhanced_prompt = prompt
    
    # Use OpenAI
    return ask_openai(enhanced_prompt, user, org, context, system_prompt, return_meta)


def ask_openai(prompt: str, user, org, context: str = None, system_prompt: str = None, return_meta: bool = False):
    """
    Send query to OpenAI
    
    Args:
        prompt: User prompt
        user: User object
        org: Organization object
        context: Additional context string
        system_prompt: Custom system prompt (overrides default)
        return_meta: If True, returns tuple (response, metadata_dict), else just response string
    
    Returns:
        str if return_meta=False, tuple (str, dict) if return_meta=True
    """
    import time
    start_time = time.time()
    
    if not openai_client:
        error_response = "OpenAI client is not configured properly."
        if return_meta:
            return error_response, {'error': 'Client not configured', 'provider': 'openai'}
        return error_response
    
    system_prompt_to_use = system_prompt if system_prompt else SAFE_SYSTEM_PROMPT
    
    messages = [
        {"role": "system", "content": system_prompt_to_use},
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
        
        processing_time = time.time() - start_time
        
        metadata = {
            'provider': 'openai',
            'model': 'gpt-3.5-turbo',
            'processing_time': processing_time,
            'tokens': response.usage.total_tokens if hasattr(response, 'usage') else None,
            'raw_response': {
                'id': response.id,
                'model': response.model,
            },
        }
        
        if return_meta:
            return answer, metadata
        return answer
    except Exception as e:
        logger.error(f"OpenAI API error: {e}")
        error_response = "Sorry, I couldn't process your request with OpenAI right now."
        if return_meta:
            return error_response, {'error': str(e), 'provider': 'openai'}
        return error_response
