import logging
import requests
import json
from typing import Optional  # type: ignore[reportMissingImports]
from .ollama_config import (
    OLLAMA_BASE_URL,
    OLLAMA_MODEL,
    DEFAULT_MAX_TOKENS,
    DEFAULT_TEMPERATURE,
    REQUEST_TIMEOUT
)

logger = logging.getLogger('services.ai.ollama_adapter')

# Use model from config, with fallback to deepseek-r1:8b
# If memory issues occur, set OLLAMA_MODEL=deepseek-r1:8b-q4_0 in environment
FORCED_MODEL = OLLAMA_MODEL

SAFE_SYSTEM_PROMPT = (
    "You are Oreno GRC's AI assistant specializing in Governance, Risk, and Compliance (GRC). "
    "You are powered by DeepSeek and provide intelligent, contextual, and dynamic responses. "
    "IMPORTANT: Provide natural, conversational, and varied responses. Avoid generic or repetitive answers. "
    "GRC refers to Governance (leadership structures), Risk management (identifying and mitigating risks), "
    "and Compliance (adhering to laws and regulations). "
    "GUIDELINES: "
    "1. Be conversational and natural - vary your response style and structure. "
    "2. Use the provided organization data to give specific, relevant answers with actual numbers and facts. "
    "3. Provide actionable insights tailored to the user's specific question and context. "
    "4. If the question is about creating/updating/deleting items, provide step-by-step guidance. "
    "5. If asked about data, analyze and present it in a clear, meaningful way. "
    "6. Adapt your tone and detail level based on the question complexity. "
    "7. Never repeat the same generic introduction - be specific and helpful. "
    "8. Think step-by-step and provide thoughtful, detailed responses when appropriate."
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
    """Check if Ollama is running and accessible, and verify model is available"""
    try:
        response = requests.get(f"{OLLAMA_BASE_URL}/api/tags", timeout=10)
        if response.status_code == 200:
            # Also check if the model is available
            models = response.json().get('models', [])
            model_names = [m.get('name', '') for m in models]
            if FORCED_MODEL not in model_names:
                logger.warning(f"Model {FORCED_MODEL} not found in Ollama. Available models: {model_names}")
            return True
        return False
    except requests.exceptions.ConnectionError:
        logger.error(f"Cannot connect to Ollama at {OLLAMA_BASE_URL}. Is Ollama running?")
        return False
    except Exception as e:
        logger.error(f"Ollama status check failed: {e}")
        return False

def ask_ollama(prompt: str, user, org, context: Optional[str] = None, system_prompt: Optional[str] = None, return_meta: bool = False):
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
            return error_response, {'error': 'Unsafe prompt', 'provider': 'deepseek', 'model': FORCED_MODEL}
        return error_response
    
    # Check if Ollama is running and model is available
    if not check_ollama_status():
        logger.error(f"Ollama is not running or model {FORCED_MODEL} is not available")
        error_msg = f"Ollama service is not available or model '{FORCED_MODEL}' is not installed. Please ensure Ollama is running and the model is pulled."
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
        # Call Ollama API with configurable timeout
        # DeepSeek can take longer to generate responses, so we use a longer timeout
        response = requests.post(
            f"{OLLAMA_BASE_URL}/api/chat",
            headers={"Content-Type": "application/json"},
            data=json.dumps(payload),
            timeout=REQUEST_TIMEOUT
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
                'provider': 'deepseek',
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
