"""
Celery tasks for background AI processing
"""
from celery import shared_task
import logging
from services.ai.ai_service import ai_assistant_answer
from services.ai.models import ChatLog, AIInteraction

logger = logging.getLogger('services.ai.tasks')

@shared_task(bind=True)
def run_ai_query(self, user_id, org_id, prompt, system_prompt=None, session_id=None):
    """
    Background task to process AI queries asynchronously
    
    Args:
        user_id: User ID
        org_id: Organization ID
        prompt: User prompt
        system_prompt: Optional custom system prompt
        session_id: Optional session ID for chat grouping
    
    Returns:
        dict with chat_id and result
    """
    try:
        # Import here to avoid circular imports
        from django.contrib.auth import get_user_model
        from organizations.models import Organization
        
        User = get_user_model()
        user = User.objects.get(id=user_id)  # type: ignore[attr-defined]
        org = Organization.objects.get(id=org_id)  # type: ignore[attr-defined]
        
        # Call AI service with metadata
        response_text, meta = ai_assistant_answer(
            prompt,
            user,
            org,
            system_prompt=system_prompt,  # type: ignore[arg-type]
            return_meta=True
        )
        
        # Type assertion: meta is guaranteed to be a dict when return_meta=True
        from typing import cast, Dict, Any
        meta_dict: Dict[str, Any] = cast(Dict[str, Any], meta)
        
        # Save ChatLog
        chat = ChatLog.objects.create(  # type: ignore[attr-defined]
            user=user,
            organization=org,
            session_id=session_id,
            query=prompt,
            response=response_text,
            metadata=meta_dict
        )
        
        # Save AIInteraction
        AIInteraction.objects.create(  # type: ignore[attr-defined]
            user=user,
            organization=org,
            prompt=prompt,
            system_prompt=system_prompt or '',
            response=response_text,
            model=meta_dict.get('model'),
            provider=meta_dict.get('provider', 'deepseek'),
            tokens_used=meta_dict.get('tokens'),
            extra={'job_id': self.request.id, 'chat_id': chat.id}
        )
        
        logger.info(f"Background AI task completed: chat_id={chat.id}, job_id={self.request.id}")
        
        return {'chat_id': chat.id, 'result': response_text}
        
    except Exception as e:
        logger.error(f"Background AI task failed: {e}")
        raise

