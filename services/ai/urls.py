from django.urls import path
from .views import AIAssistantAPIView, AIAssistantAsyncAPIView, chat_page

urlpatterns = [
    path('ask/', AIAssistantAPIView.as_view(), name='ai_assistant_ask'),
    path('ask-async/', AIAssistantAsyncAPIView.as_view(), name='ai_assistant_ask_async'),
    path('chat/', chat_page, name='ai_chat'),
] 