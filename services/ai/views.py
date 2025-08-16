from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.decorators import action
from django.contrib.auth.decorators import login_required
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.db import models
import logging

from .ai_service import (
    ai_assistant_answer, 
    get_user_conversations, 
    get_conversation_messages,
    end_conversation,
    get_or_create_user_preferences
)
from .models import AIUserPreference, AIKnowledgeBase, AIAnalytics

logger = logging.getLogger('services.ai.views')

@method_decorator(login_required, name='dispatch')
class AIAssistantAPIView(APIView):
    """
    Enhanced AI Assistant API endpoint with conversation management.
    Uses Ollama as the primary LLM with OpenAI fallback.
    """

    def post(self, request):
        try:
            question = request.data.get('question', '').strip()
            session_id = request.data.get('session_id')
            conversation_id = request.data.get('conversation_id')
            
            if not question:
                return Response(
                    {'error': 'Question is required'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Get user and organization info
            user = request.user
            org = getattr(user, 'organization', None) if user.is_authenticated else None
            
            # Get AI response with conversation management
            ai_response = ai_assistant_answer(
                question=question, 
                user=user, 
                org=org,
                session_id=session_id,
                conversation_id=conversation_id
            )
            
            if not ai_response or not ai_response.get('response'):
                return Response(
                    {'error': 'Unable to generate response. Please try again.'}, 
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR
                )
            
            return Response({
                'response': ai_response['response'],
                'question': question,
                'conversation_id': ai_response.get('conversation_id'),
                'session_id': ai_response.get('session_id'),
                'model_used': ai_response.get('model_used'),
                'response_time': ai_response.get('response_time'),
                'tokens_used': ai_response.get('tokens_used'),
                'source': ai_response.get('source'),
                'category': ai_response.get('category')
            })
            
        except Exception as e:
            logger.error(f"AI Assistant error: {e}")
            return Response(
                {'error': 'An error occurred while processing your request. Please try again.'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

@method_decorator(login_required, name='dispatch')
class AIConversationAPIView(APIView):
    """
    API endpoints for managing AI conversations.
    """

    def get(self, request):
        """Get user's recent conversations."""
        try:
            user = request.user
            org = getattr(user, 'organization', None)
            limit = int(request.GET.get('limit', 20))
            
            conversations = get_user_conversations(user, org, limit)
            
            return Response({
                'conversations': conversations,
                'total': len(conversations)
            })
            
        except Exception as e:
            logger.error(f"Error fetching conversations: {e}")
            return Response(
                {'error': 'Failed to fetch conversations'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def post(self, request):
        """Get messages for a specific conversation."""
        try:
            conversation_id = request.data.get('conversation_id')
            
            if not conversation_id:
                return Response(
                    {'error': 'Conversation ID is required'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            user = request.user
            org = getattr(user, 'organization', None)
            
            messages = get_conversation_messages(conversation_id, user, org)
            
            return Response({
                'messages': messages,
                'conversation_id': conversation_id
            })
            
        except Exception as e:
            logger.error(f"Error fetching conversation messages: {e}")
            return Response(
                {'error': 'Failed to fetch conversation messages'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def delete(self, request):
        """End a conversation."""
        try:
            conversation_id = request.data.get('conversation_id')
            
            if not conversation_id:
                return Response(
                    {'error': 'Conversation ID is required'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            user = request.user
            org = getattr(user, 'organization', None)
            
            success = end_conversation(conversation_id, user, org)
            
            if success:
                return Response({'message': 'Conversation ended successfully'})
            else:
                return Response(
                    {'error': 'Conversation not found or already ended'}, 
                    status=status.HTTP_404_NOT_FOUND
                )
                
        except Exception as e:
            logger.error(f"Error ending conversation: {e}")
            return Response(
                {'error': 'Failed to end conversation'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

@method_decorator(login_required, name='dispatch')
class AIUserPreferencesAPIView(APIView):
    """
    API endpoints for managing user AI preferences.
    """

    def get(self, request):
        """Get user's AI preferences."""
        try:
            user = request.user
            preferences = get_or_create_user_preferences(user)
            
            return Response({
                'preferences': {
                    'preferred_model': preferences.preferred_model,
                    'max_tokens': preferences.max_tokens,
                    'temperature': preferences.temperature,
                    'context_window': preferences.context_window,
                    'auto_save_conversations': preferences.auto_save_conversations,
                    'notifications_enabled': preferences.notifications_enabled
                }
            })
            
        except Exception as e:
            logger.error(f"Error fetching user preferences: {e}")
            return Response(
                {'error': 'Failed to fetch preferences'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

    def post(self, request):
        """Update user's AI preferences."""
        try:
            user = request.user
            preferences = get_or_create_user_preferences(user)
            
            # Update allowed fields
            allowed_fields = [
                'preferred_model', 'max_tokens', 'temperature', 
                'context_window', 'auto_save_conversations', 'notifications_enabled'
            ]
            
            for field in allowed_fields:
                if field in request.data:
                    setattr(preferences, field, request.data[field])
            
            preferences.save()
            
            return Response({
                'message': 'Preferences updated successfully',
                'preferences': {
                    'preferred_model': preferences.preferred_model,
                    'max_tokens': preferences.max_tokens,
                    'temperature': preferences.temperature,
                    'context_window': preferences.context_window,
                    'auto_save_conversations': preferences.auto_save_conversations,
                    'notifications_enabled': preferences.notifications_enabled
                }
            })
            
        except Exception as e:
            logger.error(f"Error updating user preferences: {e}")
            return Response(
                {'error': 'Failed to update preferences'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

@method_decorator(login_required, name='dispatch')
class AIAnalyticsAPIView(APIView):
    """
    API endpoints for AI analytics and insights.
    """

    def get(self, request):
        """Get AI usage analytics for the user."""
        try:
            user = request.user
            org = getattr(user, 'organization', None)
            
            # Get analytics for the last 30 days
            from django.utils import timezone
            from datetime import timedelta
            
            thirty_days_ago = timezone.now() - timedelta(days=30)
            
            analytics = AIAnalytics.objects.filter(
                user=user,
                organization=org,
                created_at__gte=thirty_days_ago
            ).order_by('-created_at')
            
            # Calculate summary statistics
            total_conversations = analytics.filter(event_type='conversation_started').count()
            total_messages = analytics.filter(event_type='message_sent').count()
            total_responses = analytics.filter(event_type='response_received').count()
            total_tokens = sum(analytics.values_list('tokens_used', flat=True))
            avg_response_time = analytics.filter(response_time__isnull=False).aggregate(
                avg_time=models.Avg('response_time')
            )['avg_time'] or 0
            
            # Model usage breakdown
            model_usage = {}
            for event in analytics.filter(event_type='response_received'):
                model = event.model_used
                if model not in model_usage:
                    model_usage[model] = 0
                model_usage[model] += 1
            
            return Response({
                'summary': {
                    'total_conversations': total_conversations,
                    'total_messages': total_messages,
                    'total_responses': total_responses,
                    'total_tokens': total_tokens,
                    'avg_response_time': round(avg_response_time, 2)
                },
                'model_usage': model_usage,
                'recent_events': list(analytics[:10].values(
                    'event_type', 'model_used', 'tokens_used', 'response_time', 'created_at'
                ))
            })
            
        except Exception as e:
            logger.error(f"Error fetching analytics: {e}")
            return Response(
                {'error': 'Failed to fetch analytics'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )

@method_decorator(login_required, name='dispatch')
class AIKnowledgeBaseAPIView(APIView):
    """
    API endpoints for managing AI knowledge base.
    """

    def get(self, request):
        """Get knowledge base entries for the organization."""
        try:
            user = request.user
            org = getattr(user, 'organization', None)
            
            if not org:
                return Response(
                    {'error': 'Organization not found'}, 
                    status=status.HTTP_404_NOT_FOUND
                )
            
            category = request.GET.get('category')
            query = AIKnowledgeBase.objects.filter(
                organization=org,
                is_active=True
            )
            
            if category:
                query = query.filter(category=category)
            
            entries = query.order_by('-priority', '-usage_count')
            
            return Response({
                'entries': list(entries.values(
                    'id', 'title', 'category', 'keywords', 'priority', 'usage_count'
                )),
                'total': entries.count()
            })
            
        except Exception as e:
            logger.error(f"Error fetching knowledge base: {e}")
            return Response(
                {'error': 'Failed to fetch knowledge base'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            ) 