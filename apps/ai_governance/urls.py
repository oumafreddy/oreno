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
)

app_name = 'ai_governance'

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
    path('dashboard/', GovernanceDashboardView.as_view(), name='dashboard'),
    path('api/', include(router.urls)),
    path('api/test-runs/create/', TestRunViewSet.as_view({'post': 'create_test_run'}), name='api-test-runs'),
]
