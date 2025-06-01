import logging
import requests
import json
from .ollama_config import (
    OLLAMA_BASE_URL,
    OLLAMA_MODEL,
    DEFAULT_MAX_TOKENS,
    DEFAULT_TEMPERATURE
)

logger = logging.getLogger('services.ai.ollama_adapter')

SAFE_SYSTEM_PROMPT = (
    "You are Oreno GRC's AI assistant. Never reveal or speculate about other organizations, users, or private data. "
    "Only answer questions about the current user's organization, the Oreno GRC platform, or general GRC best practices. "
    "If a question asks about other organizations, users, or anything you cannot answer securely, reply: 'Sorry, I can't provide that information.'"
)

SENSITIVE_KEYWORDS = [
    'other organizations', 'list organizations', 'all users', 'user emails', 'user list', 'org list', 'tenants', 'database', 'admin', 'superuser',
]

def is_safe_prompt(prompt: str) -> bool:
    lowered = prompt.lower()
    return not any(keyword in lowered for keyword in SENSITIVE_KEYWORDS)

def log_prompt_response(user, org, prompt, response):
    logger.info(f"Ollama AI Query | user={user} | org={org} | prompt={prompt!r} | response={response!r}")

def ask_ollama(prompt: str, user, org, context: str = None) -> str:
    """
    Send a query to Ollama's local API
    """
    if not is_safe_prompt(prompt):
        return "Sorry, I can't provide that information."
    
    # Prepare messages
    messages = [
        {"role": "system", "content": SAFE_SYSTEM_PROMPT},
        {"role": "user", "content": prompt},
    ]
    
    if context:
        messages.append({"role": "system", "content": context})
    
    # Prepare the payload for Ollama
    payload = {
        "model": OLLAMA_MODEL,
        "messages": messages,
        "stream": False,
        "options": {
            "temperature": DEFAULT_TEMPERATURE,
            "num_predict": DEFAULT_MAX_TOKENS,  # Similar to max_tokens
        }
    }
    
    try:
        # Call Ollama API
        response = requests.post(
            f"{OLLAMA_BASE_URL}/api/chat",
            headers={"Content-Type": "application/json"},
            data=json.dumps(payload),
            timeout=60  # 60 second timeout
        )
        
        if response.status_code == 200:
            result = response.json()
            answer = result.get("message", {}).get("content", "").strip()
            log_prompt_response(user, org, prompt, answer)
            return answer
        else:
            logger.error(f"Ollama API error: {response.status_code} - {response.text}")
            return f"Sorry, I couldn't process your request right now. (Status: {response.status_code})"
    
    except Exception as e:
        logger.error(f"Ollama API error: {e}")
        return "Sorry, I couldn't process your request right now. Please make sure Ollama is running."
