from django.urls import path, include
from rest_framework.routers import DefaultRouter

from .views import (
    GovernanceDashboardView,
    ModelAssetViewSet,
    DatasetAssetViewSet,
    TestPlanViewSet,
    TestRunViewSet,
    TestResultViewSet,
    MetricViewSet,
    EvidenceArtifactViewSet,
    FrameworkViewSet,
    ClauseViewSet,
    ComplianceMappingViewSet,
    ConnectorConfigViewSet,
    WebhookSubscriptionViewSet,
    api_performance_metrics,
    api_slo_metrics,
    api_invalidate_cache,
    # Web UI Views
    ModelAssetListView,
    ModelAssetCreateView,
    ModelAssetDetailView,
    ModelAssetUpdateView,
    DatasetAssetListView,
    DatasetAssetCreateView,
    DatasetAssetDetailView,
    DatasetAssetUpdateView,
    TestPlanListView,
    TestPlanCreateView,
    TestPlanDetailView,
    TestPlanUpdateView,
    TestRunListView,
    TestRunCreateView,
    TestRunDetailView,
    TestRunUpdateView,
    TestResultListView,
    TestResultCreateView,
    TestResultDetailView,
    TestResultUpdateView,
    MetricListView,
    MetricCreateView,
    MetricDetailView,
    MetricUpdateView,
    EvidenceArtifactListView,
    EvidenceArtifactCreateView,
    EvidenceArtifactDetailView,
    EvidenceArtifactUpdateView,
    FrameworkListView,
    FrameworkCreateView,
    FrameworkDetailView,
    FrameworkUpdateView,
    ClauseListView,
    ClauseCreateView,
    ClauseDetailView,
    ClauseUpdateView,
    ComplianceMappingListView,
    ComplianceMappingCreateView,
    ComplianceMappingDetailView,
    ComplianceMappingUpdateView,
    ConnectorConfigListView,
    ConnectorConfigCreateView,
    ConnectorConfigDetailView,
    ConnectorConfigUpdateView,
    WebhookSubscriptionListView,
    WebhookSubscriptionCreateView,
    WebhookSubscriptionDetailView,
    WebhookSubscriptionUpdateView,
    ReportsView,
)

app_name = 'ai_governance'

# DRF Router for API endpoints
router = DefaultRouter()
router.register(r'model-assets', ModelAssetViewSet, basename='model-asset')
router.register(r'dataset-assets', DatasetAssetViewSet, basename='dataset-asset')
router.register(r'test-plans', TestPlanViewSet, basename='test-plan')
router.register(r'test-runs', TestRunViewSet, basename='test-run')
router.register(r'test-results', TestResultViewSet, basename='test-result')
router.register(r'metrics', MetricViewSet, basename='metric')
router.register(r'artifacts', EvidenceArtifactViewSet, basename='artifact')
router.register(r'frameworks', FrameworkViewSet, basename='framework')
router.register(r'clauses', ClauseViewSet, basename='clause')
router.register(r'mappings', ComplianceMappingViewSet, basename='mapping')
router.register(r'connectors', ConnectorConfigViewSet, basename='connector')
router.register(r'webhooks', WebhookSubscriptionViewSet, basename='webhook')

urlpatterns = [
    # Dashboard
    path('dashboard/', GovernanceDashboardView.as_view(), name='dashboard'),
    
    # Web UI Views (following Risk app pattern)
    # Model Assets
    path('models/', ModelAssetListView.as_view(), name='model_list'),
    path('models/create/', ModelAssetCreateView.as_view(), name='model_create'),
    path('models/<int:pk>/', ModelAssetDetailView.as_view(), name='model_detail'),
    path('models/<int:pk>/update/', ModelAssetUpdateView.as_view(), name='model_update'),
    
    # Dataset Assets
    path('datasets/', DatasetAssetListView.as_view(), name='dataset_list'),
    path('datasets/create/', DatasetAssetCreateView.as_view(), name='dataset_create'),
    path('datasets/<int:pk>/', DatasetAssetDetailView.as_view(), name='dataset_detail'),
    path('datasets/<int:pk>/update/', DatasetAssetUpdateView.as_view(), name='dataset_update'),
    
    # Test Plans
    path('test-plans/', TestPlanListView.as_view(), name='testplan_list'),
    path('test-plans/create/', TestPlanCreateView.as_view(), name='testplan_create'),
    path('test-plans/<int:pk>/', TestPlanDetailView.as_view(), name='testplan_detail'),
    path('test-plans/<int:pk>/update/', TestPlanUpdateView.as_view(), name='testplan_update'),
    
    # Test Runs
    path('test-runs/', TestRunListView.as_view(), name='testrun_list'),
    path('test-runs/create/', TestRunCreateView.as_view(), name='testrun_create'),
    path('test-runs/<int:pk>/', TestRunDetailView.as_view(), name='testrun_detail'),
    path('test-runs/<int:pk>/update/', TestRunUpdateView.as_view(), name='testrun_update'),
    
    # Test Results
    path('test-results/', TestResultListView.as_view(), name='testresult_list'),
    path('test-results/create/', TestResultCreateView.as_view(), name='testresult_create'),
    path('test-results/<int:pk>/', TestResultDetailView.as_view(), name='testresult_detail'),
    path('test-results/<int:pk>/update/', TestResultUpdateView.as_view(), name='testresult_update'),
    
    # Metrics
    path('metrics/', MetricListView.as_view(), name='metric_list'),
    path('metrics/create/', MetricCreateView.as_view(), name='metric_create'),
    path('metrics/<int:pk>/', MetricDetailView.as_view(), name='metric_detail'),
    path('metrics/<int:pk>/update/', MetricUpdateView.as_view(), name='metric_update'),
    
    # Evidence Artifacts
    path('evidence-artifacts/', EvidenceArtifactListView.as_view(), name='evidenceartifact_list'),
    path('evidence-artifacts/create/', EvidenceArtifactCreateView.as_view(), name='evidenceartifact_create'),
    path('evidence-artifacts/<int:pk>/', EvidenceArtifactDetailView.as_view(), name='evidenceartifact_detail'),
    path('evidence-artifacts/<int:pk>/update/', EvidenceArtifactUpdateView.as_view(), name='evidenceartifact_update'),
    
    # Frameworks
    path('frameworks/', FrameworkListView.as_view(), name='framework_list'),
    path('frameworks/create/', FrameworkCreateView.as_view(), name='framework_create'),
    path('frameworks/<int:pk>/', FrameworkDetailView.as_view(), name='framework_detail'),
    path('frameworks/<int:pk>/update/', FrameworkUpdateView.as_view(), name='framework_update'),
    
    # Clauses
    path('clauses/', ClauseListView.as_view(), name='clause_list'),
    path('clauses/create/', ClauseCreateView.as_view(), name='clause_create'),
    path('clauses/<int:pk>/', ClauseDetailView.as_view(), name='clause_detail'),
    path('clauses/<int:pk>/update/', ClauseUpdateView.as_view(), name='clause_update'),
    
    # Compliance Mappings
    path('compliance-mappings/', ComplianceMappingListView.as_view(), name='compliancemapping_list'),
    path('compliance-mappings/create/', ComplianceMappingCreateView.as_view(), name='compliancemapping_create'),
    path('compliance-mappings/<int:pk>/', ComplianceMappingDetailView.as_view(), name='compliancemapping_detail'),
    path('compliance-mappings/<int:pk>/update/', ComplianceMappingUpdateView.as_view(), name='compliancemapping_update'),
    
    # Connector Configs
    path('connector-configs/', ConnectorConfigListView.as_view(), name='connectorconfig_list'),
    path('connector-configs/create/', ConnectorConfigCreateView.as_view(), name='connectorconfig_create'),
    path('connector-configs/<int:pk>/', ConnectorConfigDetailView.as_view(), name='connectorconfig_detail'),
    path('connector-configs/<int:pk>/update/', ConnectorConfigUpdateView.as_view(), name='connectorconfig_update'),
    
    # Webhook Subscriptions
    path('webhook-subscriptions/', WebhookSubscriptionListView.as_view(), name='webhooksubscription_list'),
    path('webhook-subscriptions/create/', WebhookSubscriptionCreateView.as_view(), name='webhooksubscription_create'),
    path('webhook-subscriptions/<int:pk>/', WebhookSubscriptionDetailView.as_view(), name='webhooksubscription_detail'),
    path('webhook-subscriptions/<int:pk>/update/', WebhookSubscriptionUpdateView.as_view(), name='webhooksubscription_update'),
    
    # Reports
    path('reports/', ReportsView.as_view(), name='reports'),
    
    # API endpoints
    path('api/', include(router.urls)),
    
    # Custom API actions
    path('api/test-runs/create/', TestRunViewSet.as_view({'post': 'create_test_run'}), name='api-test-runs'),
    path('api/webhooks/<int:pk>/test/', WebhookSubscriptionViewSet.as_view({'post': 'test_webhook'}), name='api-webhook-test'),
    
    # Performance and monitoring API endpoints
    path('api/performance/metrics/', api_performance_metrics, name='api-performance-metrics'),
    path('api/slo/metrics/', api_slo_metrics, name='api-slo-metrics'),
    path('api/cache/invalidate/', api_invalidate_cache, name='api-invalidate-cache'),
]