from django.urls import path
from .views import AgentParseView, AgentExecuteView
from .schema_views import (
    SchemaListView, SchemaDetailView, FieldDetailView,
    SerializerInfoView, FormInfoView, SchemaRebuildView, SchemaSearchView
)
from .form_views import PrefillFormView, SuggestFieldView

app_name = 'agent'

urlpatterns = [
    # Intent parsing and execution
    path('parse/', AgentParseView.as_view(), name='parse'),
    path('execute/', AgentExecuteView.as_view(), name='execute'),
    
    # Schema intelligence endpoints
    path('schema/', SchemaListView.as_view(), name='schema-list'),
    path('schema/rebuild/', SchemaRebuildView.as_view(), name='schema-rebuild'),
    path('schema/search/', SchemaSearchView.as_view(), name='schema-search'),
    path('schema/<str:model_path>/', SchemaDetailView.as_view(), name='schema-detail'),
    path('schema/<str:model_path>/fields/<str:field_name>/', FieldDetailView.as_view(), name='field-detail'),
    path('schema/<str:model_path>/serializer/', SerializerInfoView.as_view(), name='serializer-info'),
    path('schema/<str:model_path>/form/', FormInfoView.as_view(), name='form-info'),
    
    # Form agent endpoints (intelligent form pre-filling)
    path('prefill/', PrefillFormView.as_view(), name='prefill-form'),
    path('suggest/<str:model_path>/<str:field_name>/', SuggestFieldView.as_view(), name='suggest-field'),
]
