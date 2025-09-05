from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView
from django.utils import timezone
from datetime import timedelta
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response

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
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get organization from request
        org = getattr(self.request, 'organization', None)
        if not org:
            return context
        
        # Get basic metrics
        context['total_models'] = ModelAsset.objects.filter(organization=org).count()
        context['total_test_runs'] = TestRun.objects.filter(organization=org).count()
        
        # Get recent test runs
        context['recent_test_runs'] = TestRun.objects.filter(
            organization=org
        ).select_related('model_asset', 'test_plan').order_by('-created_at')[:10]
        
        # Calculate test results
        recent_results = TestResult.objects.filter(
            test_run__organization=org,
            test_run__created_at__gte=timezone.now() - timedelta(days=30)
        )
        
        context['passed_tests'] = recent_results.filter(passed=True).count()
        context['total_recent_tests'] = recent_results.count()
        
        # Calculate compliance score (simplified)
        if context['total_recent_tests'] > 0:
            context['compliance_score'] = round(
                (context['passed_tests'] / context['total_recent_tests']) * 100
            )
        else:
            context['compliance_score'] = 0
        
        # Get test results by category
        context['fairness_passed'] = recent_results.filter(
            test_name__startswith='demographic_parity'
        ).filter(passed=True).count()
        
        context['explainability_passed'] = recent_results.filter(
            test_name__startswith='shap_'
        ).filter(passed=True).count()
        
        context['robustness_passed'] = recent_results.filter(
            test_name__startswith='adversarial_'
        ).filter(passed=True).count()
        
        context['privacy_passed'] = recent_results.filter(
            test_name__startswith='membership_'
        ).filter(passed=True).count()
        
        # Mock compliance framework scores (in real implementation, these would be calculated)
        context['eu_ai_act_score'] = 85
        context['oecd_score'] = 78
        context['nist_score'] = 92
        
        # Get available models, datasets, and test plans for the modal
        context['available_models'] = ModelAsset.objects.filter(organization=org)
        context['available_datasets'] = DatasetAsset.objects.filter(organization=org)
        context['available_test_plans'] = TestPlan.objects.filter(organization=org)
        
        return context


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
    
    @action(detail=False, methods=['post'])
    def create_test_run(self, request):
        """Create a new test run with specified test categories."""
        try:
            # Get organization from request
            org = getattr(request, 'organization', None)
            if not org:
                return Response(
                    {'error': 'Organization context required'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Extract data from request
            model_asset_id = request.data.get('model_asset')
            dataset_asset_id = request.data.get('dataset_asset')
            test_plan_id = request.data.get('test_plan')
            test_categories = request.data.get('test_categories', [])
            
            if not model_asset_id:
                return Response(
                    {'error': 'Model asset is required'}, 
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Get model asset
            try:
                model_asset = ModelAsset.objects.get(id=model_asset_id, organization=org)
            except ModelAsset.DoesNotExist:
                return Response(
                    {'error': 'Model asset not found'}, 
                    status=status.HTTP_404_NOT_FOUND
                )
            
            # Get dataset asset if provided
            dataset_asset = None
            if dataset_asset_id:
                try:
                    dataset_asset = DatasetAsset.objects.get(id=dataset_asset_id, organization=org)
                except DatasetAsset.DoesNotExist:
                    return Response(
                        {'error': 'Dataset asset not found'}, 
                        status=status.HTTP_404_NOT_FOUND
                    )
            
            # Get test plan if provided
            test_plan = None
            if test_plan_id:
                try:
                    test_plan = TestPlan.objects.get(id=test_plan_id, organization=org)
                except TestPlan.DoesNotExist:
                    return Response(
                        {'error': 'Test plan not found'}, 
                        status=status.HTTP_404_NOT_FOUND
                    )
            
            # Create test configuration based on categories
            test_config = self._create_test_config(test_categories, model_asset.model_type)
            
            # Create test run
            test_run = TestRun.objects.create(
                organization=org,
                model_asset=model_asset,
                dataset_asset=dataset_asset,
                test_plan=test_plan,
                parameters=test_config,
                status='pending'
            )
            
            # Queue test execution
            from .tasks import execute_test_run
            execute_test_run.delay(test_run.id)
            
            return Response({
                'success': True,
                'test_run_id': test_run.id,
                'message': 'Test run created and queued for execution'
            })
            
        except Exception as exc:
            return Response(
                {'error': f'Failed to create test run: {str(exc)}'}, 
                status=status.HTTP_500_INTERNAL_SERVER_ERROR
            )
    
    def _create_test_config(self, test_categories, model_type):
        """Create test configuration based on selected categories."""
        config = {
            'tests': {},
            'model_type': model_type,
            'categories': test_categories
        }
        
        # Define available tests for each category
        category_tests = {
            'fairness': [
                'demographic_parity',
                'equal_opportunity',
                'disparate_impact'
            ],
            'explainability': [
                'shap_feature_importance',
                'permutation_importance',
                'partial_dependence'
            ],
            'robustness': [
                'adversarial_noise',
                'input_perturbation',
                'stability_test'
            ],
            'privacy': [
                'membership_inference',
                'data_leakage',
                'attribute_inference'
            ]
        }
        
        # Add tests for selected categories
        for category in test_categories:
            if category in category_tests:
                for test_name in category_tests[category]:
                    config['tests'][test_name] = {
                        'enabled': True,
                        'parameters': {},
                        'thresholds': self._get_default_thresholds(test_name),
                        'metadata': {'category': category}
                    }
        
        return config
    
    def _get_default_thresholds(self, test_name):
        """Get default thresholds for a test."""
        thresholds = {
            'demographic_parity': {'demographic_parity': 0.1},
            'equal_opportunity': {'equal_opportunity': 0.1},
            'disparate_impact': {'disparate_impact': 0.8},
            'shap_feature_importance': {'explanation_consistency': 0.7},
            'permutation_importance': {'stability_score': 0.7},
            'partial_dependence': {'average_smoothness': 0.6},
            'adversarial_noise': {'overall_robustness': 0.8},
            'input_perturbation': {'overall_robustness': 0.7},
            'stability_test': {'overall_stability': 0.8},
            'membership_inference': {'privacy_score': 0.6},
            'data_leakage': {'privacy_score': 0.7},
            'attribute_inference': {'privacy_score': 0.5}
        }
        
        return thresholds.get(test_name, {})


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