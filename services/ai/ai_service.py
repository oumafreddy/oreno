import os
import logging
import json
from typing import Optional, Dict, Any
from .ollama_adapter import ask_ollama
# Keep OpenAI as a fallback
from .llm_adapter import ask_llm

logger = logging.getLogger('services.ai.ai_service')

# Enhanced FAQ knowledge base with categories and metadata
FAQ_KB = [
    {
        'question': 'what is your role',
        'answer': 'I am Oreno GRC\'s AI assistant, designed to help you with Governance, Risk, and Compliance (GRC) questions. I can assist with audit processes, risk management, compliance requirements, and general GRC best practices. I\'m here to provide guidance and answer questions about the Oreno GRC platform and GRC concepts.',
        'category': 'general',
        'keywords': ['role', 'what', 'assistant', 'ai', 'help']
    },
    {
        'question': 'how do i use the legal app',
        'answer': 'The Legal app in Oreno GRC helps you manage contracts and legal documents. You can create, review, and store legal documents securely. To get started, go to the Legal app from the dashboard and follow the on-screen instructions.',
        'category': 'legal',
        'keywords': ['legal', 'contracts', 'documents']
    },
    {
        'question': 'what does the risk app do',
        'answer': 'The Risk app allows you to identify, assess, and monitor risks within your organization. You can create risk registers, assign owners, and track mitigation actions.',
        'category': 'risk',
        'keywords': ['risk', 'assessment', 'mitigation']
    },
    {
        'question': 'how do i get started',
        'answer': 'Welcome to Oreno GRC! Start by exploring the dashboard. Each app (Audit, Risk, Legal, Compliance, etc.) is accessible from the main menu. Click on any app to see its features and guides.',
        'category': 'general',
        'keywords': ['start', 'begin', 'dashboard']
    },
    {
        'question': 'what is grc',
        'answer': 'GRC stands for Governance, Risk, and Compliance. Governance refers to management and leadership structures. Risk management involves identifying and mitigating risks. Compliance ensures adherence to laws and regulations. Oreno GRC provides tools to manage all three areas effectively.',
        'category': 'general',
        'keywords': ['grc', 'governance', 'compliance']
    },
    {
        'question': 'how do i create a workplan',
        'answer': 'To create a workplan in the Audit app: 1) Go to the Audit dashboard, 2) Click "Create Workplan", 3) Fill in the required fields including objectives and description, 4) Save the workplan. You can then add engagements to your workplan.',
        'category': 'audit',
        'keywords': ['workplan', 'audit', 'create']
    },
    {
        'question': 'how do i add an engagement',
        'answer': 'To add an engagement: 1) Go to your workplan detail page, 2) Click "Add Engagement", 3) Fill in the engagement details including scope and objectives, 4) Save the engagement. You can then add objectives to your engagement.',
        'category': 'audit',
        'keywords': ['engagement', 'audit', 'add']
    }
]

def find_faq_answer(question: str, user_context: Dict[str, Any] = None) -> Optional[str]:
    """Find a matching FAQ answer for the given question using improved matching with organization awareness."""
    if not question:
        return None
    
    q = question.lower().strip()
    
    # Filter FAQ entries based on organization context
    available_faqs = FAQ_KB
    
    # If we have organization context, we could filter organization-specific FAQs here
    # For now, we'll use the general FAQ but log the organization context
    if user_context:
        org_name = user_context.get('organization_name', 'Unknown')
        logger.info(f"Searching FAQ for organization: {org_name}")
    
    # First, try exact keyword matching
    for entry in available_faqs:
        if entry['question'] in q or q in entry['question']:
            logger.info(f"FAQ match found: {entry['question']}")
            return entry['answer']
    
    # Then try keyword-based matching with more flexible scoring
    question_words = set(q.split())
    best_match = None
    best_score = 0
    
    for entry in available_faqs:
        entry_keywords = set(entry['keywords'])
        score = len(question_words.intersection(entry_keywords))
        
        # Bonus points for exact word matches
        for word in question_words:
            if word in entry['question'].lower():
                score += 1
        
        if score > best_score:
            best_score = score
            best_match = entry
    
    # Return best match if score is reasonable (at least 1 keyword match)
    if best_match and best_score >= 1:
        logger.info(f"FAQ keyword match found: {best_match['question']} (score: {best_score})")
        return best_match['answer']
    
    return None

def get_user_context(user, org) -> Dict[str, Any]:
    """Get user-specific context for AI responses with enhanced organization scoping."""
    context = {
        'user_role': getattr(user, 'role', 'user'),
        'organization_id': getattr(org, 'id', None) if org else None,
        'organization_name': getattr(org, 'name', 'Unknown') if org else 'Unknown',
        'is_authenticated': user.is_authenticated,
        'user_id': user.id if user.is_authenticated else None,
        'username': user.username if user.is_authenticated else None,
    }
    
    # Add user permissions if available
    if hasattr(user, 'get_all_permissions'):
        context['permissions'] = list(user.get_all_permissions())
    
    # Add organization-specific restrictions
    if org:
        context['organization_restrictions'] = {
            'can_only_access_own_data': True,
            'organization_scope': f"Organization: {org.name} (ID: {org.id})",
            'data_boundary': f"All responses must be scoped to organization '{org.name}' only"
        }
    
    return context

def create_organization_scoped_prompt(question: str, user_context: Dict[str, Any]) -> str:
    """Create a prompt that enforces organization scoping."""
    org_name = user_context.get('organization_name', 'Unknown')
    org_id = user_context.get('organization_id')
    
    scoped_prompt = f"""
You are Oreno GRC's AI assistant for {org_name}. 

ORGANIZATION SCOPE: You are assisting {org_name} (ID: {org_id}). When providing specific information, focus on this organization's context.

USER QUESTION: {question}

Provide a helpful, accurate response about GRC topics, audit processes, risk management, or compliance. If asked about other organizations' data, politely redirect to {org_name}'s context.
"""
    return scoped_prompt.strip()

def validate_ai_response(response: str, user_context: Dict[str, Any] = None) -> bool:
    """Validate AI response for safety and quality with organization scoping."""
    if not response or not isinstance(response, str):
        return False
    
    response_lower = response.lower()
    
    # Check for potentially harmful content - more specific patterns
    harmful_patterns = [
        'password:',
        'api key:',
        'secret:',
        'private data:',
        'other users:',
        'other organizations:',
        'database password',
        'admin password',
        'root password',
    ]
    
    for pattern in harmful_patterns:
        if pattern in response_lower:
            logger.warning(f"AI response contains potentially harmful content: {pattern}")
            return False
    
    # Organization-specific validation - only check for specific data leaks
    if user_context:
        org_name = user_context.get('organization_name', 'Unknown')
        org_id = user_context.get('organization_id')
        
        # Only block responses that explicitly mention other organizations by name
        if org_name != 'Unknown':
            # Look for specific organization names that don't match the user's organization
            # This is a more targeted approach
            if 'organization' in response_lower and org_name.lower() not in response_lower:
                # Only block if it's clearly about other organizations
                if any(word in response_lower for word in ['other org', 'different org', 'another org']):
                    logger.warning(f"AI response may contain references to other organizations")
                    return False
    
    # Check for reasonable response length
    if len(response) < 5 or len(response) > 10000:  # More lenient length limits
        logger.warning(f"AI response length outside acceptable range: {len(response)}")
        return False
    
    return True

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
    faq_answer = find_faq_answer(question, get_user_context(user, org))
    if faq_answer:
        logger.info("FAQ answer found")
        return faq_answer
    
    # 2. Get user context for better responses
    user_context = get_user_context(user, org)
    
    # 3. Create organization-scoped prompt
    scoped_question = create_organization_scoped_prompt(question, user_context)
    
    # 4. Use Ollama for AI responses with OpenAI fallback
    try:
        logger.info("Attempting Ollama response")
        # Pass only the scoped question, not the full context to avoid serialization issues
        response = ask_ollama(scoped_question, user, org)
        
        if response and response.strip():
            # Validate the response
            if validate_ai_response(response, user_context):
                logger.info("Ollama response successful and validated")
                return response.strip()
            else:
                logger.warning("Ollama response failed validation")
                raise Exception("Invalid response from Ollama")
        else:
            logger.warning("Ollama returned empty response")
            raise Exception("Empty response from Ollama")
            
    except Exception as e:
        logger.error(f"Ollama error: {e}, falling back to OpenAI")
        try:
            # Pass only the scoped question, not the full context to avoid serialization issues
            response = ask_llm(scoped_question, user, org)
            if response and response.strip():
                # Validate the response
                if validate_ai_response(response, user_context):
                    logger.info("OpenAI fallback successful and validated")
                    return response.strip()
                else:
                    logger.warning("OpenAI response failed validation")
                    return "I'm sorry, I'm having trouble providing a safe response to your question. Please try rephrasing your question."
            else:
                logger.error("OpenAI also returned empty response")
                return "I'm sorry, I'm having trouble processing your request right now. Please try again later."
        except Exception as fallback_error:
            logger.error(f"OpenAI fallback also failed: {fallback_error}")
            return "I'm sorry, I'm unable to process your request at the moment. Please try again later or contact support if the problem persists."
