from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.throttling import UserRateThrottle
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.core.exceptions import ValidationError
from django.utils.html import strip_tags
from django.shortcuts import render
import logging
import re

from .ai_service import ai_assistant_answer

logger = logging.getLogger('services.ai.views')

class AIRateThrottle(UserRateThrottle):
    """Rate limiting for AI requests - 10 requests per minute per user"""
    rate = '10/minute'

@method_decorator(login_required, name='dispatch')
class AIAssistantAPIView(APIView):
    """
    AI Assistant API endpoint that handles user questions and returns AI responses.
    Uses DeepSeek (via Ollama) as the primary LLM.
    """
    throttle_classes = [AIRateThrottle]
    
    def validate_question(self, question: str) -> str:
        """Validate and sanitize the question input"""
        if not question or not isinstance(question, str):
            raise ValidationError("Question must be a non-empty string")
        
        # Strip HTML tags and excessive whitespace
        question = strip_tags(question).strip()
        
        if len(question) < 3:
            raise ValidationError("Question must be at least 3 characters long")
        
        if len(question) > 1000:
            raise ValidationError("Question must be less than 1000 characters")
        
        # Check for potentially malicious patterns
        malicious_patterns = [
            r'<script.*?>.*?</script>',
            r'javascript:',
            r'data:text/html',
            r'vbscript:',
            r'on\w+\s*=',
        ]
        
        for pattern in malicious_patterns:
            if re.search(pattern, question, re.IGNORECASE):
                raise ValidationError("Question contains potentially malicious content")
        
        return question

    def post(self, request):
        try:
            # Validate input
            question = request.data.get('question', '').strip()
            try:
                question = self.validate_question(question)
            except ValidationError as e:
                return Response(
                    {'error': str(e)}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Get user and organization info with enhanced security
            user = request.user
            org = getattr(user, 'organization', None) if user.is_authenticated else None
            
            # Additional organization validation
            if not org:
                return Response(
                    {'error': 'Organization context is required for AI assistance.'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Verify user belongs to the organization
            if hasattr(user, 'organization') and user.organization != org:
                logger.warning(f"User {user.id} attempted to access AI with mismatched organization")
                return Response(
                    {'error': 'Organization access denied.'}, 
                    status=status.HTTP_403_FORBIDDEN
                )
            
            # Log the request for audit purposes
            logger.info(f"AI request from user {user.id} ({user.username}) in org {org.name} (ID: {org.id})")
            
            # Get AI response with metadata
            ai_response, llm_meta = ai_assistant_answer(question, user, org, return_meta=True)
            
            if not ai_response:
                return Response(
                    {'error': 'Unable to generate response. Please try again.'}, 
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
            
            # Log successful response
            logger.info(f"AI response generated successfully for user {user.id} in org {org.name}")
            
            # Get session ID from request
            session_id = request.data.get('session_id') or request.session.session_key
            
            # Save ChatLog
            from services.ai.models import ChatLog, AIInteraction
            from typing import cast, Dict, Any
            
            # Type assertion: llm_meta is guaranteed to be a dict when return_meta=True
            llm_meta_dict: Dict[str, Any] = cast(Dict[str, Any], llm_meta)
            
            chat = ChatLog.objects.create(  # type: ignore[attr-defined]
                user=user,
                organization=org,
                session_id=session_id,
                query=question,
                response=ai_response,
                metadata=llm_meta_dict
            )
            
            # Save AIInteraction for detailed audit trail
            AIInteraction.objects.create(  # type: ignore[attr-defined]
                user=user,
                organization=org,
                prompt=question,
                system_prompt=None,  # Using default system prompt
                response=ai_response,
                model=llm_meta_dict.get('model'),
                provider=llm_meta_dict.get('provider', 'deepseek'),
                tokens_used=llm_meta_dict.get('tokens'),
                extra={'llm_raw': llm_meta_dict.get('raw_response'), 'chat_id': chat.id},
                source=llm_meta_dict.get('provider', 'deepseek'),
                success=True,
                processing_time=llm_meta_dict.get('processing_time'),
                metadata={'organization_id': org.id, 'organization_name': org.name}
            )
            
            return Response({
                'response': ai_response,  # Frontend expects 'response' key
                'question': question,
                'chat_id': chat.id
            })
            
        except Exception as e:
            logger.error(f"AI Assistant error: {e}")
            return Response(
                {'error': 'An error occurred while processing your request. Please try again.'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


class AIAssistantAsyncAPIView(APIView):
    """
    Async AI Assistant API endpoint that enqueues AI queries for background processing.
    Returns job_id immediately, result can be retrieved via job status endpoint.
    """
    throttle_classes = [AIRateThrottle]
    permission_classes = []  # Will use login_required decorator
    
    @method_decorator(login_required)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)
    
    def post(self, request):
        try:
            # Validate input
            question = request.data.get('question', '').strip()
            try:
                # Reuse validation from AIAssistantAPIView
                view = AIAssistantAPIView()
                question = view.validate_question(question)
            except ValidationError as e:
                return Response(
                    {'error': str(e)}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            user = request.user
            org = getattr(user, 'organization', None)
            
            if not org:
                return Response(
                    {'error': 'Organization context is required for AI assistance.'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Import task here to avoid circular imports
            from services.ai.tasks import run_ai_query
            from typing import cast, Any
            
            # Submit to Celery
            session_id = request.data.get('session_id') or request.session.session_key
            system_prompt = request.data.get('system_prompt')
            
            # Celery task delay method is dynamically added, need to cast for type checker
            task_func = cast(Any, run_ai_query)
            job = task_func.delay(  # type: ignore[attr-defined]
                user.id,
                org.id,
                question,
                system_prompt=system_prompt,
                session_id=session_id
            )
            
            logger.info(f"AI query enqueued: job_id={job.id}, user={user.id}, org={org.id}")
            
            return Response({
                'job_id': job.id,
                'status': 'pending',
                'message': 'Query submitted for processing'
            }, status=status.HTTP_202_ACCEPTED)
            
        except Exception as e:
            logger.error(f"AI Assistant async error: {e}")
            return Response(
                {'error': 'An error occurred while enqueueing your request. Please try again.'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )


@login_required
def chat_page(request):
    """Render the chat UI page"""
    return render(request, 'ai/chat.html')
 