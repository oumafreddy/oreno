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
    "You are Oreno GRC's AI assistant specializing in Governance, Risk, and Compliance (GRC). "
    "GRC refers specifically to an organization's approach to Governance (leadership and organizational structures), "
    "Risk management (identifying, assessing, and mitigating risks), and Compliance (adhering to laws, regulations, and standards). "
    "Never reveal or speculate about other organizations, users, or private data. "
    "Only answer questions about the current user's organization, the Oreno GRC platform, or general GRC best practices. "
    "Always focus your answers on the Governance, Risk, and Compliance domain. "
    "If unsure, prefer to discuss general GRC principles rather than hallucinate specifics. "
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
    
    # Add GRC-specific context to every prompt to help the model stay on topic
    grc_context = (
        "GRC stands for Governance, Risk, and Compliance.\n"
        "- Governance refers to the management and leadership structures and processes that ensure an organization meets its objectives.\n"
        "- Risk management involves identifying, assessing, and mitigating risks to the organization.\n"
        "- Compliance means ensuring the organization adheres to all relevant laws, regulations, and standards.\n\n"
    )
    
    # Combine the GRC context with the user's prompt
    enhanced_prompt = grc_context + "Question: " + prompt
    
    # Prepare messages
    messages = [
        {"role": "system", "content": SAFE_SYSTEM_PROMPT},
        {"role": "user", "content": enhanced_prompt},
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
