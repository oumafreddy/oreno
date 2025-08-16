import os
import logging
import time
import uuid
from typing import Optional, List, Dict, Any
from django.db import transaction
from django.utils import timezone
from .ollama_adapter import ask_ollama
from .llm_adapter import ask_llm
from .models import AIConversation, AIMessage, AIUserPreference, AIKnowledgeBase, AIAnalytics

logger = logging.getLogger('services.ai.ai_service')

# Enhanced FAQ knowledge base with better structure
ENHANCED_FAQ_KB = [
    {
        'question': 'how do i use the legal app',
        'keywords': ['legal', 'contracts', 'documents', 'legal app'],
        'category': 'platform',
        'answer': 'The Legal app in Oreno GRC helps you manage contracts and legal documents. You can create, review, and store legal documents securely. To get started, go to the Legal app from the dashboard and follow the on-screen instructions.',
        'priority': 5
    },
    {
        'question': 'what does the risk app do',
        'keywords': ['risk', 'risk management', 'risk app', 'risk assessment'],
        'category': 'risk',
        'answer': 'The Risk app allows you to identify, assess, and monitor risks within your organization. You can create risk registers, assign owners, and track mitigation actions.',
        'priority': 5
    },
    {
        'question': 'how do i get started',
        'keywords': ['start', 'begin', 'getting started', 'first time'],
        'category': 'platform',
        'answer': 'Welcome to Oreno GRC! Start by exploring the dashboard. Each app (Audit, Risk, Legal, Compliance, etc.) is accessible from the main menu. Click on any app to see its features and guides.',
        'priority': 10
    },
    {
        'question': 'what is grc',
        'keywords': ['grc', 'governance', 'risk', 'compliance', 'definition'],
        'category': 'grc_general',
        'answer': 'GRC stands for Governance, Risk, and Compliance. Governance refers to management and leadership structures. Risk management involves identifying and mitigating risks. Compliance ensures adherence to laws and regulations. Oreno GRC provides tools to manage all three areas effectively.',
        'priority': 10
    },
    {
        'question': 'how do i create a workplan',
        'keywords': ['workplan', 'audit workplan', 'create workplan', 'annual workplan'],
        'category': 'audit',
        'answer': 'To create a workplan in the Audit app: 1) Go to the Audit dashboard, 2) Click "Create Workplan", 3) Fill in the required fields including objectives and description, 4) Save the workplan. You can then add engagements to your workplan.',
        'priority': 8
    },
    {
        'question': 'how do i add an engagement',
        'keywords': ['engagement', 'audit engagement', 'add engagement', 'create engagement'],
        'category': 'audit',
        'answer': 'To add an engagement: 1) Go to your workplan detail page, 2) Click "Add Engagement", 3) Fill in the engagement details including scope and objectives, 4) Save the engagement. You can then add objectives to your engagement.',
        'priority': 8
    }
]

def get_or_create_user_preferences(user) -> AIUserPreference:
    """Get or create user preferences for AI interactions."""
    preferences, created = AIUserPreference.objects.get_or_create(
        user=user,
        defaults={
            'preferred_model': 'llama3:8b',
            'max_tokens': 2048,
            'temperature': 0.7,
            'context_window': 10,
            'auto_save_conversations': True,
            'notifications_enabled': True
        }
    )
    return preferences

def find_knowledge_base_answer(question: str, organization=None) -> Optional[Dict[str, Any]]:
    """Find a matching knowledge base answer for the given question."""
    if not question or not question.strip():
        return None
    
    q = question.lower().strip()
    
    # First check database knowledge base
    if organization:
        kb_entries = AIKnowledgeBase.objects.filter(
            organization=organization,
            is_active=True
        ).order_by('-priority', '-usage_count')
        
        for entry in kb_entries:
            # Check keywords
            if any(keyword.lower() in q for keyword in entry.keywords):
                # Increment usage count
                entry.usage_count += 1
                entry.save(update_fields=['usage_count'])
                return {
                    'answer': entry.content,
                    'source': 'database',
                    'title': entry.title,
                    'category': entry.category
                }
            
            # Check question patterns
            for pattern in entry.question_patterns:
                if pattern.lower() in q:
                    entry.usage_count += 1
                    entry.save(update_fields=['usage_count'])
                    return {
                        'answer': entry.content,
                        'source': 'database',
                        'title': entry.title,
                        'category': entry.category
                    }
    
    # Then check hardcoded FAQ
    for entry in ENHANCED_FAQ_KB:
        if entry['question'] in q or q in entry['question']:
            return {
                'answer': entry['answer'],
                'source': 'faq',
                'title': entry['question'],
                'category': entry['category']
            }
        
        # Check keywords
        if any(keyword.lower() in q for keyword in entry['keywords']):
            return {
                'answer': entry['answer'],
                'source': 'faq',
                'title': entry['question'],
                'category': entry['category']
            }
    
    return None

def get_conversation_context(conversation: AIConversation, max_messages: int = 10) -> List[Dict[str, str]]:
    """Get conversation context for AI model."""
    messages = conversation.messages.order_by('-created_at')[:max_messages]
    context = []
    
    for message in reversed(messages):  # Reverse to get chronological order
        context.append({
            'role': message.role,
            'content': message.content
        })
    
    return context

def create_ai_analytics(user, event_type: str, model_used: str, tokens_used: int = 0, 
                       response_time: float = None, metadata: Dict = None):
    """Create analytics entry for AI interactions."""
    try:
        AIAnalytics.objects.create(
            user=user,
            organization=getattr(user, 'organization', None),
            event_type=event_type,
            model_used=model_used,
            tokens_used=tokens_used,
            response_time=response_time,
            metadata=metadata or {}
        )
    except Exception as e:
        logger.error(f"Failed to create AI analytics: {e}")

def estimate_tokens(text: str) -> int:
    """Rough estimate of tokens in text (4 characters per token average)."""
    return len(text) // 4

@transaction.atomic
def ai_assistant_answer(question: str, user, org, session_id: str = None, 
                       conversation_id: str = None) -> Dict[str, Any]:
    """
    Enhanced AI assistant function with conversation history and context awareness.
    """
    if not question or not question.strip():
        return {
            'response': "Please provide a question to get help.",
            'conversation_id': None,
            'session_id': None
        }
    
    question = question.strip()
    start_time = time.time()
    
    # Get user preferences
    preferences = get_or_create_user_preferences(user)
    
    # Generate session ID if not provided
    if not session_id:
        session_id = str(uuid.uuid4())
    
    # Get or create conversation
    conversation = None
    if conversation_id:
        try:
            conversation = AIConversation.objects.get(
                id=conversation_id,
                user=user,
                organization=org
            )
        except AIConversation.DoesNotExist:
            pass
    
    if not conversation:
        conversation = AIConversation.objects.create(
            user=user,
            organization=org,
            session_id=session_id,
            title=question[:50] + "..." if len(question) > 50 else question,
            model_used=preferences.preferred_model
        )
        create_ai_analytics(user, 'conversation_started', preferences.preferred_model)
    
    # Save user message
    user_message = AIMessage.objects.create(
        conversation=conversation,
        role='user',
        content=question,
        tokens_used=estimate_tokens(question),
        model_used=preferences.preferred_model,
        organization=org
    )
    
    logger.info(f"AI Assistant query: {question} | User: {user} | Org: {org} | Session: {session_id}")
    
    # 1. Check knowledge base first for quick answers
    kb_answer = find_knowledge_base_answer(question, org)
    if kb_answer:
        logger.info(f"Knowledge base answer found: {kb_answer['source']}")
        
        # Save assistant message
        assistant_message = AIMessage.objects.create(
            conversation=conversation,
            role='assistant',
            content=kb_answer['answer'],
            tokens_used=estimate_tokens(kb_answer['answer']),
            model_used='knowledge_base',
            response_time=time.time() - start_time,
            metadata={'source': kb_answer['source'], 'category': kb_answer['category']},
            organization=org
        )
        
        # Update conversation
        conversation.total_tokens += user_message.tokens_used + assistant_message.tokens_used
        conversation.save(update_fields=['total_tokens'])
        
        create_ai_analytics(user, 'response_received', 'knowledge_base', 
                          assistant_message.tokens_used, assistant_message.response_time)
        
        return {
            'response': kb_answer['answer'],
            'conversation_id': conversation.id,
            'session_id': session_id,
            'source': kb_answer['source'],
            'category': kb_answer['category']
        }
    
    # 2. Get conversation context for AI model
    context_messages = []
    if preferences.auto_save_conversations:
        context_messages = get_conversation_context(conversation, preferences.context_window)
    
    # 3. Use Ollama for AI responses with OpenAI fallback
    response = None
    model_used = preferences.preferred_model
    error_occurred = False
    
    try:
        logger.info("Attempting Ollama response")
        response = ask_ollama(question, user, org, context_messages)
        if response and response.strip():
            logger.info("Ollama response successful")
            response = response.strip()
        else:
            logger.warning("Ollama returned empty response")
            raise Exception("Empty response from Ollama")
            
    except Exception as e:
        logger.error(f"Ollama error: {e}, falling back to OpenAI")
        error_occurred = True
        try:
            response = ask_llm(question, user, org, context_messages)
            if response and response.strip():
                logger.info("OpenAI fallback successful")
                response = response.strip()
                model_used = 'openai'
            else:
                logger.error("OpenAI also returned empty response")
                response = "I'm sorry, I'm having trouble processing your request right now. Please try again later."
                model_used = 'error'
        except Exception as fallback_error:
            logger.error(f"OpenAI fallback also failed: {fallback_error}")
            response = "I'm sorry, I'm unable to process your request at the moment. Please try again later or contact support if the problem persists."
            model_used = 'error'
    
    # Save assistant message
    response_time = time.time() - start_time
    assistant_message = AIMessage.objects.create(
        conversation=conversation,
        role='assistant',
        content=response,
        tokens_used=estimate_tokens(response),
        model_used=model_used,
        response_time=response_time,
        metadata={'error_occurred': error_occurred},
        organization=org
    )
    
    # Update conversation
    conversation.total_tokens += user_message.tokens_used + assistant_message.tokens_used
    conversation.model_used = model_used
    conversation.save(update_fields=['total_tokens', 'model_used'])
    
    # Create analytics
    event_type = 'error_occurred' if error_occurred else 'response_received'
    create_ai_analytics(user, event_type, model_used, 
                       assistant_message.tokens_used, response_time)
    
    return {
        'response': response,
        'conversation_id': conversation.id,
        'session_id': session_id,
        'model_used': model_used,
        'response_time': response_time,
        'tokens_used': assistant_message.tokens_used
    }

def get_user_conversations(user, org, limit: int = 20) -> List[Dict[str, Any]]:
    """Get user's recent conversations."""
    conversations = AIConversation.objects.filter(
        user=user,
        organization=org
    ).order_by('-created_at')[:limit]
    
    result = []
    for conv in conversations:
        result.append({
            'id': conv.id,
            'title': conv.title,
            'created_at': conv.created_at,
            'total_tokens': conv.total_tokens,
            'model_used': conv.model_used,
            'is_active': conv.is_active,
            'message_count': conv.messages.count()
        })
    
    return result

def get_conversation_messages(conversation_id: str, user, org) -> List[Dict[str, Any]]:
    """Get messages for a specific conversation."""
    try:
        conversation = AIConversation.objects.get(
            id=conversation_id,
            user=user,
            organization=org
        )
        
        messages = conversation.messages.order_by('created_at')
        result = []
        
        for message in messages:
            result.append({
                'id': message.id,
                'role': message.role,
                'content': message.content,
                'created_at': message.created_at,
                'tokens_used': message.tokens_used,
                'model_used': message.model_used,
                'response_time': message.response_time
            })
        
        return result
    except AIConversation.DoesNotExist:
        return []

def end_conversation(conversation_id: str, user, org) -> bool:
    """Mark a conversation as ended."""
    try:
        conversation = AIConversation.objects.get(
            id=conversation_id,
            user=user,
            organization=org
        )
        conversation.is_active = False
        conversation.save(update_fields=['is_active'])
        
        create_ai_analytics(user, 'conversation_ended', conversation.model_used)
        return True
    except AIConversation.DoesNotExist:
        return False
