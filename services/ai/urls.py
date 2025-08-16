from django.urls import path
from .views import (
    AIAssistantAPIView, 
    AIConversationAPIView, 
    AIUserPreferencesAPIView,
    AIAnalyticsAPIView,
    AIKnowledgeBaseAPIView
)

urlpatterns = [
    # Main AI Assistant endpoint
    path('ask/', AIAssistantAPIView.as_view(), name='ai_assistant_ask'),
    
    # Conversation management
    path('conversations/', AIConversationAPIView.as_view(), name='ai_conversations'),
    
    # User preferences
    path('preferences/', AIUserPreferencesAPIView.as_view(), name='ai_preferences'),
    
    # Analytics and insights
    path('analytics/', AIAnalyticsAPIView.as_view(), name='ai_analytics'),
    
    # Knowledge base management
    path('knowledge-base/', AIKnowledgeBaseAPIView.as_view(), name='ai_knowledge_base'),
] 