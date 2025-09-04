from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView
from rest_framework import viewsets, permissions

from core.mixins.organization import OrganizationScopedQuerysetMixin
from .models import (
    ModelAsset,
    DatasetAsset,
    TestPlan,
    TestRun,
    TestResult,
    Metric,
    EvidenceArtifact,
    Framework,
    Clause,
    ComplianceMapping,
    ConnectorConfig,
    WebhookSubscription,
)
from .serializers import (
    ModelAssetSerializer,
    DatasetAssetSerializer,
    TestPlanSerializer,
    TestRunSerializer,
    TestResultSerializer,
    MetricSerializer,
    EvidenceArtifactSerializer,
    FrameworkSerializer,
    ClauseSerializer,
    ComplianceMappingSerializer,
    ConnectorConfigSerializer,
    WebhookSubscriptionSerializer,
)


class GovernanceDashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'ai_governance/dashboard.html'


class ModelAssetViewSet(OrganizationScopedQuerysetMixin, viewsets.ModelViewSet):
    queryset = ModelAsset.objects.all()
    serializer_class = ModelAssetSerializer
    permission_classes = [permissions.IsAuthenticated]


class DatasetAssetViewSet(OrganizationScopedQuerysetMixin, viewsets.ModelViewSet):
    queryset = DatasetAsset.objects.all()
    serializer_class = DatasetAssetSerializer
    permission_classes = [permissions.IsAuthenticated]


class TestPlanViewSet(OrganizationScopedQuerysetMixin, viewsets.ModelViewSet):
    queryset = TestPlan.objects.all()
    serializer_class = TestPlanSerializer
    permission_classes = [permissions.IsAuthenticated]


class TestRunViewSet(OrganizationScopedQuerysetMixin, viewsets.ModelViewSet):
    queryset = TestRun.objects.all()
    serializer_class = TestRunSerializer
    permission_classes = [permissions.IsAuthenticated]


class TestResultViewSet(OrganizationScopedQuerysetMixin, viewsets.ModelViewSet):
    queryset = TestResult.objects.all()
    serializer_class = TestResultSerializer
    permission_classes = [permissions.IsAuthenticated]


class MetricViewSet(OrganizationScopedQuerysetMixin, viewsets.ModelViewSet):
    queryset = Metric.objects.all()
    serializer_class = MetricSerializer
    permission_classes = [permissions.IsAuthenticated]


class EvidenceArtifactViewSet(OrganizationScopedQuerysetMixin, viewsets.ModelViewSet):
    queryset = EvidenceArtifact.objects.all()
    serializer_class = EvidenceArtifactSerializer
    permission_classes = [permissions.IsAuthenticated]


class FrameworkViewSet(OrganizationScopedQuerysetMixin, viewsets.ModelViewSet):
    queryset = Framework.objects.all()
    serializer_class = FrameworkSerializer
    permission_classes = [permissions.IsAuthenticated]


class ClauseViewSet(OrganizationScopedQuerysetMixin, viewsets.ModelViewSet):
    queryset = Clause.objects.all()
    serializer_class = ClauseSerializer
    permission_classes = [permissions.IsAuthenticated]


class ComplianceMappingViewSet(OrganizationScopedQuerysetMixin, viewsets.ModelViewSet):
    queryset = ComplianceMapping.objects.all()
    serializer_class = ComplianceMappingSerializer
    permission_classes = [permissions.IsAuthenticated]


class ConnectorConfigViewSet(OrganizationScopedQuerysetMixin, viewsets.ModelViewSet):
    queryset = ConnectorConfig.objects.all()
    serializer_class = ConnectorConfigSerializer
    permission_classes = [permissions.IsAuthenticated]


class WebhookSubscriptionViewSet(OrganizationScopedQuerysetMixin, viewsets.ModelViewSet):
    queryset = WebhookSubscription.objects.all()
    serializer_class = WebhookSubscriptionSerializer
    permission_classes = [permissions.IsAuthenticated]