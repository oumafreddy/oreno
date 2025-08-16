from django.urls import path
from .views import AIAssistantAPIView

urlpatterns = [
    path('ask/', AIAssistantAPIView.as_view(), name='ai_assistant_ask'),
] 