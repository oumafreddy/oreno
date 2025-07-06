import os
import logging
from .ollama_adapter import ask_ollama
# Keep OpenAI as a fallback
from .llm_adapter import ask_llm

logger = logging.getLogger('services.ai.ai_service')

# Example FAQ knowledge base (could be loaded from a file or DB)
FAQ_KB = [
    {
        'question': 'how do i use the legal app',
        'answer': 'The Legal app in Oreno GRC helps you manage contracts and legal documents. You can create, review, and store legal documents securely. To get started, go to the Legal app from the dashboard and follow the on-screen instructions.'
    },
    {
        'question': 'what does the risk app do',
        'answer': 'The Risk app allows you to identify, assess, and monitor risks within your organization. You can create risk registers, assign owners, and track mitigation actions.'
    },
    {
        'question': 'how do i get started',
        'answer': 'Welcome to Oreno GRC! Start by exploring the dashboard. Each app (Audit, Risk, Legal, Compliance, etc.) is accessible from the main menu. Click on any app to see its features and guides.'
    },
    {
        'question': 'what is grc',
        'answer': 'GRC stands for Governance, Risk, and Compliance. Governance refers to management and leadership structures. Risk management involves identifying and mitigating risks. Compliance ensures adherence to laws and regulations. Oreno GRC provides tools to manage all three areas effectively.'
    },
    {
        'question': 'how do i create a workplan',
        'answer': 'To create a workplan in the Audit app: 1) Go to the Audit dashboard, 2) Click "Create Workplan", 3) Fill in the required fields including objectives and description, 4) Save the workplan. You can then add engagements to your workplan.'
    },
    {
        'question': 'how do i add an engagement',
        'answer': 'To add an engagement: 1) Go to your workplan detail page, 2) Click "Add Engagement", 3) Fill in the engagement details including scope and objectives, 4) Save the engagement. You can then add objectives to your engagement.'
    }
]

def find_faq_answer(question: str) -> str:
    """Find a matching FAQ answer for the given question."""
    q = question.lower().strip()
    for entry in FAQ_KB:
        if entry['question'] in q or q in entry['question']:
            return entry['answer']
    return None

def ai_assistant_answer(question: str, user, org) -> str:
    """
    Main AI assistant function that handles user questions.
    Uses FAQ first, then Ollama, with OpenAI as fallback.
    """
    if not question or not question.strip():
        return "Please provide a question to get help."
    
    question = question.strip()
    logger.info(f"AI Assistant query: {question} | User: {user} | Org: {org}")
    
    # 1. Check FAQ first for quick answers
    faq_answer = find_faq_answer(question)
    if faq_answer:
        logger.info("FAQ answer found")
        return faq_answer
    
    # 2. Use Ollama for AI responses with OpenAI fallback
    try:
        logger.info("Attempting Ollama response")
        response = ask_ollama(question, user, org)
        if response and response.strip():
            logger.info("Ollama response successful")
            return response.strip()
        else:
            logger.warning("Ollama returned empty response")
            raise Exception("Empty response from Ollama")
            
    except Exception as e:
        logger.error(f"Ollama error: {e}, falling back to OpenAI")
        try:
            response = ask_llm(question, user, org)
            if response and response.strip():
                logger.info("OpenAI fallback successful")
                return response.strip()
            else:
                logger.error("OpenAI also returned empty response")
                return "I'm sorry, I'm having trouble processing your request right now. Please try again later."
        except Exception as fallback_error:
            logger.error(f"OpenAI fallback also failed: {fallback_error}")
            return "I'm sorry, I'm unable to process your request at the moment. Please try again later or contact support if the problem persists."
