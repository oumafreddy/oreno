from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
import logging

from .ai_service import ai_assistant_answer

logger = logging.getLogger('services.ai.views')

@method_decorator(login_required, name='dispatch')
class AIAssistantAPIView(APIView):
    """
    AI Assistant API endpoint that handles user questions and returns AI responses.
    Uses Ollama as the primary LLM with OpenAI fallback.
    """

    def post(self, request):
        try:
            question = request.data.get('question', '').strip()
            
            if not question:
                return Response(
                    {'error': 'Question is required'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Get user and organization info
            user = request.user
            org = getattr(user, 'organization', None) if user.is_authenticated else None
            
            # Get AI response
            ai_response = ai_assistant_answer(question, user, org)
            
            if not ai_response:
                return Response(
                    {'error': 'Unable to generate response. Please try again.'}, 
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
            
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