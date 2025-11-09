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
    "You have access to real organization data and should use it to provide specific, actionable insights. "
    "GRC refers specifically to an organization's approach to Governance (leadership and organizational structures), "
    "Risk management (identifying, assessing, and mitigating risks), and Compliance (adhering to laws, regulations, and standards). "
    "SECURITY GUIDELINES: "
    "1. Use the provided organization data to give specific, relevant answers. "
    "2. Reference actual numbers and facts from the data when possible. "
    "3. Provide actionable insights based on the current state. "
    "4. Focus on the specific organization's context. "
    "5. If asked about data, use the provided summary rather than making assumptions. "
    "6. Always maintain professional and helpful tone. "
    "7. If unsure about specific data, prefer general guidance over speculation."
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

def ask_ollama(prompt: str, user, org, context: str = None, system_prompt: str = None, return_meta: bool = False):
    """
    Send a query to Ollama's local API
    
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
    
    if not is_safe_prompt(prompt):
        error_response = "Sorry, I can't provide that information."
        if return_meta:
            return error_response, {'error': 'Unsafe prompt', 'provider': 'ollama', 'model': FORCED_MODEL}
        return error_response
    
    # Check if Ollama is running
    if not check_ollama_status():
        logger.error("Ollama is not running or not accessible")
        error_msg = "Ollama service is not available"
        if return_meta:
            raise Exception(error_msg)
        raise Exception(error_msg)
    
    # Use custom system prompt or default
    system_prompt_to_use = system_prompt if system_prompt else SAFE_SYSTEM_PROMPT
    
    # Add GRC-specific context to every prompt (unless custom system prompt provided)
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
    
    # Prepare messages
    messages = [
        {"role": "system", "content": system_prompt_to_use},
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
        
        processing_time = time.time() - start_time
        
        if response.status_code == 200:
            result = response.json()
            answer = result.get("message", {}).get("content", "").strip()
            
            if not answer:
                logger.warning("Ollama returned empty response")
                raise Exception("Empty response from Ollama")
            
            log_prompt_response(user, org, prompt, answer)
            
            metadata = {
                'provider': 'ollama',
                'model': model_to_use,
                'processing_time': processing_time,
                'tokens': result.get('eval_count', 0),  # Approximate token count
                'raw_response': result,
            }
            
            if return_meta:
                return answer, metadata
            return answer
        else:
            error_msg = f"Ollama API error: {response.status_code} - {response.text}"
            logger.error(error_msg)
            if return_meta:
                raise Exception(error_msg)
            raise Exception(error_msg)
    
    except requests.exceptions.Timeout:
        error_msg = "Ollama request timed out"
        logger.error(error_msg)
        if return_meta:
            raise Exception(error_msg)
        raise Exception(error_msg)
    except requests.exceptions.ConnectionError:
        error_msg = "Cannot connect to Ollama service"
        logger.error(error_msg)
        if return_meta:
            raise Exception(error_msg)
        raise Exception(error_msg)
    except Exception as e:
        logger.error(f"Ollama API error: {e}")
        error_msg = f"Ollama service error: {str(e)}"
        if return_meta:
            raise Exception(error_msg)
        raise Exception(error_msg)
