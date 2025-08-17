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

# Force the model to be llama3:8b since that's what the user has installed
FORCED_MODEL = "llama3:8b"

SAFE_SYSTEM_PROMPT = (
    "You are Oreno GRC's AI assistant specializing in Governance, Risk, and Compliance (GRC). "
    "GRC refers specifically to an organization's approach to Governance (leadership and organizational structures), "
    "Risk management (identifying, assessing, and mitigating risks), and Compliance (adhering to laws, regulations, and standards). "
    "SECURITY GUIDELINES: "
    "1. Be helpful and informative about GRC topics, audit processes, and compliance. "
    "2. If asked about other organizations' specific data, politely redirect to the user's organization context. "
    "3. Focus on general GRC best practices and platform guidance. "
    "4. Always maintain professional and helpful tone. "
    "5. If unsure about specific data, prefer general guidance over speculation."
)

SENSITIVE_KEYWORDS = [
    'list all organizations', 'show all users', 'user emails', 'user list', 'org list', 'tenants', 'database', 'admin', 'superuser',
    'password', 'api key', 'secret key', 'private data', 'other organizations data',
]

def is_safe_prompt(prompt: str) -> bool:
    """Check if the prompt is safe to send to the LLM"""
    if not prompt or not isinstance(prompt, str):
        return False
        
    lowered = prompt.lower()
    return not any(keyword in lowered for keyword in SENSITIVE_KEYWORDS)

def log_prompt_response(user, org, prompt, response):
    """Log the prompt and response for debugging"""
    logger.info(f"Ollama AI Query | user={user} | org={org} | prompt={prompt!r} | response={response!r}")

def check_ollama_status():
    """Check if Ollama is running and accessible"""
    try:
        response = requests.get(f"{OLLAMA_BASE_URL}/api/tags", timeout=5)
        return response.status_code == 200
    except Exception as e:
        logger.error(f"Ollama status check failed: {e}")
        return False

def ask_ollama(prompt: str, user, org, context: str = None) -> str:
    """
    Send a query to Ollama's local API
    """
    if not is_safe_prompt(prompt):
        return "Sorry, I can't provide that information."
    
    # Check if Ollama is running
    if not check_ollama_status():
        logger.error("Ollama is not running or not accessible")
        raise Exception("Ollama service is not available")
    
    # Add GRC-specific context to every prompt
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
    
    # Prepare messages
    messages = [
        {"role": "system", "content": SAFE_SYSTEM_PROMPT},
        {"role": "user", "content": enhanced_prompt},
    ]
    
    if context:
        messages.append({"role": "system", "content": context})
    
    # Use the forced model to ensure we use llama3:8b
    model_to_use = FORCED_MODEL
    logger.info(f"Using model: {model_to_use} (forced from config: {OLLAMA_MODEL})")
    
    # Prepare the payload for Ollama
    payload = {
        "model": model_to_use,
        "messages": messages,
        "stream": False,
        "options": {
            "temperature": DEFAULT_TEMPERATURE,
            "num_predict": DEFAULT_MAX_TOKENS,
        }
    }
    
    logger.info(f"Sending request to Ollama: {OLLAMA_BASE_URL}/api/chat with model {model_to_use}")
    
    try:
        # Call Ollama API
        response = requests.post(
            f"{OLLAMA_BASE_URL}/api/chat",
            headers={"Content-Type": "application/json"},
            data=json.dumps(payload),
            timeout=60
        )
        
        if response.status_code == 200:
            result = response.json()
            answer = result.get("message", {}).get("content", "").strip()
            
            if not answer:
                logger.warning("Ollama returned empty response")
                raise Exception("Empty response from Ollama")
            
            log_prompt_response(user, org, prompt, answer)
            return answer
        else:
            error_msg = f"Ollama API error: {response.status_code} - {response.text}"
            logger.error(error_msg)
            raise Exception(error_msg)
    
    except requests.exceptions.Timeout:
        error_msg = "Ollama request timed out"
        logger.error(error_msg)
        raise Exception(error_msg)
    except requests.exceptions.ConnectionError:
        error_msg = "Cannot connect to Ollama service"
        logger.error(error_msg)
        raise Exception(error_msg)
    except Exception as e:
        logger.error(f"Ollama API error: {e}")
        raise Exception(f"Ollama service error: {str(e)}")
