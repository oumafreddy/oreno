from django.urls import path
from .views import AgentParseView, AgentExecuteView

app_name = 'agent'

urlpatterns = [
    path('parse/', AgentParseView.as_view(), name='parse'),
    path('execute/', AgentExecuteView.as_view(), name='execute'),
]
