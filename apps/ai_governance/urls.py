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