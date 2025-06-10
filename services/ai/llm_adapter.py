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
    "You are Oreno GRC's AI assistant. Never reveal or speculate about other organizations, users, or private data. "
    "Only answer questions about the current user's organization, the Oreno GRC platform, or general GRC best practices. "
    "If a question asks about other organizations, users, or anything you cannot answer securely, reply: 'Sorry, I can't provide that information.'"
)

SENSITIVE_KEYWORDS = [
    'other organizations', 'list organizations', 'all users', 'user emails', 'user list', 'org list', 'tenants', 'database', 'admin', 'superuser',
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

def ask_llm(prompt: str, user, org, context: str = None) -> str:
    """Main entry point for LLM queries. Uses OpenAI."""
    if not is_safe_prompt(prompt):
        return "Sorry, I can't provide that information."
    
    # Add GRC-specific context to every prompt to help the model stay on topic
    grc_context = (
        "GRC stands for Governance, Risk, and Compliance.\n"
        "- Governance refers to the management and leadership structures and processes that ensure an organization meets its objectives.\n"
        "- Risk management involves identifying, assessing, and mitigating risks to the organization.\n"
        "- Compliance means ensuring the organization adheres to all relevant laws, regulations, and standards.\n\n"
    )
    
    # Combine the GRC context with the user's prompt
    enhanced_prompt = grc_context + "Question: " + prompt
    
    # Use OpenAI
    return ask_openai(enhanced_prompt, user, org, context)


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
