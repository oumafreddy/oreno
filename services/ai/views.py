from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.throttling import UserRateThrottle
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.core.exceptions import ValidationError
from django.utils.html import strip_tags
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
    Uses Ollama as the primary LLM with OpenAI fallback.
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
            
            # Get AI response
            ai_response = ai_assistant_answer(question, user, org)
            
            if not ai_response:
                return Response(
                    {'error': 'Unable to generate response. Please try again.'}, 
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
            
            # Log successful response
            logger.info(f"AI response generated successfully for user {user.id} in org {org.name}")
            
            # TODO: Track AI interaction in database for audit purposes
            # This would create an AIInteraction record with organization context
            # from services.ai.models import AIInteraction
            # AIInteraction.objects.create(
            #     user=user,
            #     question=question,
            #     response=ai_response,
            #     source='ollama',  # or 'openai' or 'faq'
            #     success=True,
            #     metadata={'organization_id': org.id, 'organization_name': org.name}
            # )
            
            return Response({
                'response': ai_response,
                'question': question
            })
            
        except Exception as e:
            logger.error(f"AI Assistant error: {e}")
            return Response(
                {'error': 'An error occurred while processing your request. Please try again.'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            ) 