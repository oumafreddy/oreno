from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic import TemplateView, ListView, CreateView, UpdateView, DetailView, DeleteView
from django.urls import reverse_lazy
from django.utils import timezone
from django.contrib import messages
from datetime import timedelta
from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from django.core.exceptions import PermissionDenied

from core.mixins.organization import OrganizationScopedQuerysetMixin
from core.mixins.permissions import OrganizationPermissionMixin
from users.permissions import IsOrgAdmin, IsOrgManagerOrReadOnly, IsOrgStaffOrReadOnly
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
from .forms import (
    ModelAssetForm,
    DatasetAssetForm,
    TestPlanForm,
    TestRunForm,
    TestResultForm,
    MetricForm,
    EvidenceArtifactForm,
    FrameworkForm,
    ClauseForm,
    ComplianceMappingForm,
    ConnectorConfigForm,
    WebhookSubscriptionForm,
)


class GovernanceDashboardView(OrganizationPermissionMixin, LoginRequiredMixin, TemplateView):
    template_name = 'ai_governance/dashboard.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Get organization from request
        org = getattr(self.request, 'organization', None)
        if not org:
            raise PermissionDenied("Organization context is required")
        # --- Period Filter Logic (aligned with Audit) ---
        from django.utils import timezone
        import calendar
        from django.db.models import Q
        org_created = getattr(org, 'created_at', timezone.now()).date()
        today = timezone.now().date()
        years = list(range(org_created.year, today.year + 1))
        months = [(i, calendar.month_name[i]) for i in range(1, 13)]
        selected_years = self.request.GET.getlist('year') or [str(today.year)]
        selected_months = self.request.GET.getlist('month')
        filter_all = 'All' in selected_years
        year_ints = [int(y) for y in selected_years if y.isdigit()]
        month_ints = [int(m) for m in selected_months if m.isdigit()]
        
        # Use performance monitoring for metrics
        from .performance import MetricsCollector
        metrics_collector = MetricsCollector(org.id)
        
        # Get cached dashboard metrics
        dashboard_metrics = metrics_collector.get_dashboard_metrics()
        context.update(dashboard_metrics)
        
        # Get test performance metrics
        test_performance = metrics_collector.get_test_performance_metrics()
        context.update(test_performance)
        
        # Get compliance metrics
        compliance_metrics = metrics_collector.get_compliance_metrics()
        context.update(compliance_metrics)
        
        # Get recent test runs (with performance monitoring)
        from .performance import performance_monitor
        
        @performance_monitor.monitor_query_performance('dashboard_recent_test_runs')
        def get_recent_test_runs():
            qs = TestRun.objects.filter(organization=org).select_related('model_asset', 'test_plan')
            if not filter_all:
                tq = Q(created_at__year__in=year_ints)
                if month_ints:
                    tq &= Q(created_at__month__in=month_ints)
                qs = qs.filter(tq)
            return qs.order_by('-created_at')[:10]
        
        context['recent_test_runs'] = get_recent_test_runs()
        
        # Get test results by category (with performance monitoring)
        @performance_monitor.monitor_query_performance('dashboard_test_categories')
        def get_test_categories():
            recent_results = TestResult.objects.filter(test_run__organization=org)
            if not filter_all:
                rq = Q(test_run__created_at__year__in=year_ints)
                if month_ints:
                    rq &= Q(test_run__created_at__month__in=month_ints)
                recent_results = recent_results.filter(rq)
            
            return {
                'fairness_passed': recent_results.filter(
                    test_name__startswith='demographic_parity'
                ).filter(passed=True).count(),
                'explainability_passed': recent_results.filter(
                    test_name__startswith='shap_'
                ).filter(passed=True).count(),
                'robustness_passed': recent_results.filter(
                    test_name__startswith='adversarial_'
                ).filter(passed=True).count(),
                'privacy_passed': recent_results.filter(
                    test_name__startswith='membership_'
                ).filter(passed=True).count()
            }
        
        test_categories = get_test_categories()
        context.update(test_categories)
        
        # Get SLO metrics
        from .alerts import slo_monitor
        slo_metrics = slo_monitor.get_slo_metrics(org.id)
        context['slo_metrics'] = slo_metrics
        
        # Get available models, datasets, and test plans for the modal
        context['available_models'] = ModelAsset.objects.filter(organization=org)
        context['available_datasets'] = DatasetAsset.objects.filter(organization=org)
        context['available_test_plans'] = TestPlan.objects.filter(organization=org)

        # Get counts for dashboard management cards
        context['total_datasets'] = DatasetAsset.objects.filter(organization=org).count()
        context['total_test_plans'] = TestPlan.objects.filter(organization=org).count()
        context['total_test_results'] = TestResult.objects.filter(organization=org).count()
        context['total_frameworks'] = Framework.objects.filter(organization=org).count()
        context['total_clauses'] = Clause.objects.filter(organization=org).count()
        context['total_mappings'] = ComplianceMapping.objects.filter(organization=org).count()
        context['total_artifacts'] = EvidenceArtifact.objects.filter(organization=org).count()
        context['total_connectors'] = ConnectorConfig.objects.filter(organization=org).count()
        context['total_webhooks'] = WebhookSubscription.objects.filter(organization=org).count()
        context['total_metrics'] = Metric.objects.filter(organization=org).count()

        # Get recent activity for dashboard
        from django.contrib.contenttypes.models import ContentType
        from django.contrib.admin.models import LogEntry
        
        recent_activity = []
        try:
            # Get recent model changes
            recent_models = ModelAsset.objects.filter(organization=org).order_by('-updated_at')[:3]
            for model in recent_models:
                recent_activity.append({
                    'message': f'Model "{model.name}" was updated',
                    'timestamp': model.updated_at
                })
            
            # Get recent test runs
            recent_runs = TestRun.objects.filter(organization=org).order_by('-created_at')[:3]
            for run in recent_runs:
                recent_activity.append({
                    'message': f'Test run for "{run.model_asset.name}" was created',
                    'timestamp': run.created_at
                })
            
            # Sort by timestamp and take the most recent 5
            recent_activity.sort(key=lambda x: x['timestamp'], reverse=True)
            context['recent_activity'] = recent_activity[:5]
        except Exception:
            context['recent_activity'] = []

        # Period filter context
        context['available_years'] = years
        context['available_months'] = months
        context['selected_years'] = selected_years
        context['selected_months'] = selected_months
        context['filter_all'] = filter_all
        
        return context


class ModelAssetViewSet(OrganizationScopedQuerysetMixin, viewsets.ModelViewSet):
    queryset = ModelAsset.objects.all()
    serializer_class = ModelAssetSerializer
    permission_classes = [permissions.IsAuthenticated, IsOrgStaffOrReadOnly]


class DatasetAssetViewSet(OrganizationScopedQuerysetMixin, viewsets.ModelViewSet):
    queryset = DatasetAsset.objects.all()
    serializer_class = DatasetAssetSerializer
    permission_classes = [permissions.IsAuthenticated, IsOrgStaffOrReadOnly]


class TestPlanViewSet(OrganizationScopedQuerysetMixin, viewsets.ModelViewSet):
    queryset = TestPlan.objects.all()
    serializer_class = TestPlanSerializer
    permission_classes = [permissions.IsAuthenticated, IsOrgManagerOrReadOnly]


class TestRunViewSet(OrganizationScopedQuerysetMixin, viewsets.ModelViewSet):
    queryset = TestRun.objects.all()
    serializer_class = TestRunSerializer
    permission_classes = [permissions.IsAuthenticated, IsOrgStaffOrReadOnly]
    
    @action(detail=False, methods=['post'], permission_classes=[permissions.IsAuthenticated, IsOrgManagerOrReadOnly])
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
    permission_classes = [permissions.IsAuthenticated, IsOrgStaffOrReadOnly]


class MetricViewSet(OrganizationScopedQuerysetMixin, viewsets.ModelViewSet):
    queryset = Metric.objects.all()
    serializer_class = MetricSerializer
    permission_classes = [permissions.IsAuthenticated, IsOrgStaffOrReadOnly]


class EvidenceArtifactViewSet(OrganizationScopedQuerysetMixin, viewsets.ModelViewSet):
    queryset = EvidenceArtifact.objects.all()
    serializer_class = EvidenceArtifactSerializer
    permission_classes = [permissions.IsAuthenticated, IsOrgStaffOrReadOnly]


class FrameworkViewSet(OrganizationScopedQuerysetMixin, viewsets.ModelViewSet):
    queryset = Framework.objects.all()
    serializer_class = FrameworkSerializer
    permission_classes = [permissions.IsAuthenticated, IsOrgAdmin]


class ClauseViewSet(OrganizationScopedQuerysetMixin, viewsets.ModelViewSet):
    queryset = Clause.objects.all()
    serializer_class = ClauseSerializer
    permission_classes = [permissions.IsAuthenticated, IsOrgAdmin]


class ComplianceMappingViewSet(OrganizationScopedQuerysetMixin, viewsets.ModelViewSet):
    queryset = ComplianceMapping.objects.all()
    serializer_class = ComplianceMappingSerializer
    permission_classes = [permissions.IsAuthenticated, IsOrgManagerOrReadOnly]


class ConnectorConfigViewSet(OrganizationScopedQuerysetMixin, viewsets.ModelViewSet):
    queryset = ConnectorConfig.objects.all()
    serializer_class = ConnectorConfigSerializer
    permission_classes = [permissions.IsAuthenticated, IsOrgAdmin]


class WebhookSubscriptionViewSet(OrganizationScopedQuerysetMixin, viewsets.ModelViewSet):
    queryset = WebhookSubscription.objects.all()
    serializer_class = WebhookSubscriptionSerializer
    permission_classes = [permissions.IsAuthenticated, IsOrgManagerOrReadOnly]
    
    @action(detail=True, methods=['post'])
    def test_webhook(self, request, pk=None):
        """Test webhook endpoint with a sample payload."""
        from .webhook_service import webhook_service
        
        webhook = self.get_object()
        result = webhook_service.test_webhook(webhook)
        
        if result['success']:
            return Response({
                'message': 'Webhook test successful',
                'details': result['message']
            }, status=status.HTTP_200_OK)
        else:
            return Response({
                'message': 'Webhook test failed',
                'details': result['message']
            }, status=status.HTTP_400_BAD_REQUEST)


# Performance and monitoring API endpoints
@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated, IsOrgStaffOrReadOnly])
def api_performance_metrics(request):
    """Get performance metrics for AI governance."""
    from .performance import MetricsCollector
    
    org = request.organization
    metrics_collector = MetricsCollector(org.id)
    
    metrics = {
        'dashboard': metrics_collector.get_dashboard_metrics(),
        'test_performance': metrics_collector.get_test_performance_metrics(),
        'compliance': metrics_collector.get_compliance_metrics()
    }
    
    return Response(metrics)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated, IsOrgStaffOrReadOnly])
def api_slo_metrics(request):
    """Get SLO metrics for AI governance."""
    from .alerts import slo_monitor
    
    org = request.organization
    slo_metrics = slo_monitor.get_slo_metrics(org.id)
    
    return Response(slo_metrics)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated, IsOrgManagerOrReadOnly])
def api_invalidate_cache(request):
    """Invalidate AI governance cache."""
    from .performance import performance_monitor
    
    org = request.organization
    cache_type = request.data.get('cache_type', 'all')
    
    performance_monitor.invalidate_metrics_cache(org.id, cache_type)
    
    return Response({
        'message': f'Cache invalidated for {cache_type}',
        'organization': org.name
    })


# Web UI Views (following Risk app pattern)
class ModelAssetListView(OrganizationPermissionMixin, LoginRequiredMixin, ListView):
    model = ModelAsset
    template_name = 'ai_governance/modelasset_list.html'
    context_object_name = 'model_assets'
    paginate_by = 20

    def get_queryset(self):
        return ModelAsset.objects.filter(organization=self.request.organization).order_by('-created_at')


class ModelAssetCreateView(OrganizationPermissionMixin, LoginRequiredMixin, CreateView):
    model = ModelAsset
    form_class = ModelAssetForm
    template_name = 'ai_governance/modelasset_form.html'
    success_url = reverse_lazy('ai_governance:model_list')

    def form_valid(self, form):
        form.instance.organization = self.request.organization
        form.instance.created_by = self.request.user
        form.instance.updated_by = self.request.user
        return super().form_valid(form)


class ModelAssetDetailView(OrganizationPermissionMixin, LoginRequiredMixin, DetailView):
    model = ModelAsset
    template_name = 'ai_governance/modelasset_detail.html'
    context_object_name = 'model_asset'

    def get_queryset(self):
        return ModelAsset.objects.filter(organization=self.request.organization)


class ModelAssetUpdateView(OrganizationPermissionMixin, LoginRequiredMixin, UpdateView):
    model = ModelAsset
    form_class = ModelAssetForm
    template_name = 'ai_governance/modelasset_form.html'
    success_url = reverse_lazy('ai_governance:model_list')

    def get_queryset(self):
        return ModelAsset.objects.filter(organization=self.request.organization)

    def form_valid(self, form):
        form.instance.updated_by = self.request.user
        return super().form_valid(form)


class DatasetAssetListView(OrganizationPermissionMixin, LoginRequiredMixin, ListView):
    model = DatasetAsset
    template_name = 'ai_governance/datasetasset_list.html'
    context_object_name = 'dataset_assets'
    paginate_by = 20

    def get_queryset(self):
        return DatasetAsset.objects.filter(organization=self.request.organization).order_by('-created_at')


class DatasetAssetCreateView(OrganizationPermissionMixin, LoginRequiredMixin, CreateView):
    model = DatasetAsset
    form_class = DatasetAssetForm
    template_name = 'ai_governance/datasetasset_form.html'
    success_url = reverse_lazy('ai_governance:dataset_list')

    def form_valid(self, form):
        form.instance.organization = self.request.organization
        form.instance.created_by = self.request.user
        form.instance.updated_by = self.request.user
        return super().form_valid(form)


class DatasetAssetDetailView(OrganizationPermissionMixin, LoginRequiredMixin, DetailView):
    model = DatasetAsset
    template_name = 'ai_governance/datasetasset_detail.html'
    context_object_name = 'dataset_asset'

    def get_queryset(self):
        return DatasetAsset.objects.filter(organization=self.request.organization)


class DatasetAssetUpdateView(OrganizationPermissionMixin, LoginRequiredMixin, UpdateView):
    model = DatasetAsset
    form_class = DatasetAssetForm
    template_name = 'ai_governance/datasetasset_form.html'
    success_url = reverse_lazy('ai_governance:dataset_list')

    def get_queryset(self):
        return DatasetAsset.objects.filter(organization=self.request.organization)

    def form_valid(self, form):
        form.instance.updated_by = self.request.user
        return super().form_valid(form)


class TestPlanListView(OrganizationPermissionMixin, LoginRequiredMixin, ListView):
    model = TestPlan
    template_name = 'ai_governance/testplan_list.html'
    context_object_name = 'test_plans'
    paginate_by = 20

    def get_queryset(self):
        return TestPlan.objects.filter(organization=self.request.organization).order_by('-created_at')


class TestPlanCreateView(OrganizationPermissionMixin, LoginRequiredMixin, CreateView):
    model = TestPlan
    form_class = TestPlanForm
    template_name = 'ai_governance/testplan_form.html'
    success_url = reverse_lazy('ai_governance:testplan_list')

    def form_valid(self, form):
        form.instance.organization = self.request.organization
        form.instance.created_by = self.request.user
        form.instance.updated_by = self.request.user
        return super().form_valid(form)


class TestPlanDetailView(OrganizationPermissionMixin, LoginRequiredMixin, DetailView):
    model = TestPlan
    template_name = 'ai_governance/testplan_detail.html'
    context_object_name = 'test_plan'

    def get_queryset(self):
        return TestPlan.objects.filter(organization=self.request.organization)


class TestPlanUpdateView(OrganizationPermissionMixin, LoginRequiredMixin, UpdateView):
    model = TestPlan
    form_class = TestPlanForm
    template_name = 'ai_governance/testplan_form.html'
    success_url = reverse_lazy('ai_governance:testplan_list')

    def get_queryset(self):
        return TestPlan.objects.filter(organization=self.request.organization)

    def form_valid(self, form):
        form.instance.updated_by = self.request.user
        return super().form_valid(form)


class TestRunListView(OrganizationPermissionMixin, LoginRequiredMixin, ListView):
    model = TestRun
    template_name = 'ai_governance/testrun_list.html'
    context_object_name = 'test_runs'
    paginate_by = 20

    def get_queryset(self):
        return TestRun.objects.filter(organization=self.request.organization).order_by('-created_at')


class TestRunCreateView(OrganizationPermissionMixin, LoginRequiredMixin, CreateView):
    model = TestRun
    form_class = TestRunForm
    template_name = 'ai_governance/testrun_form.html'
    success_url = reverse_lazy('ai_governance:testrun_list')

    def form_valid(self, form):
        form.instance.organization = self.request.organization
        form.instance.created_by = self.request.user
        form.instance.updated_by = self.request.user
        
        # Save the test run first
        response = super().form_valid(form)
        
        # Check if "Run Test" button was clicked
        if 'run_test' in self.request.POST:
            # Import here to avoid circular imports
            from .tasks import execute_test_run
            
            # Start the test execution asynchronously
            execute_test_run.delay(self.object.id)
            
            # Add success message
            messages.success(
                self.request, 
                f'Test run created and started! Test run ID: {self.object.id}'
            )
        
        return response


class TestRunDetailView(OrganizationPermissionMixin, LoginRequiredMixin, DetailView):
    model = TestRun
    template_name = 'ai_governance/testrun_detail.html'
    context_object_name = 'test_run'

    def get_queryset(self):
        return TestRun.objects.filter(organization=self.request.organization)


class TestRunUpdateView(OrganizationPermissionMixin, LoginRequiredMixin, UpdateView):
    model = TestRun
    form_class = TestRunForm
    template_name = 'ai_governance/testrun_form.html'
    success_url = reverse_lazy('ai_governance:testrun_list')

    def get_queryset(self):
        return TestRun.objects.filter(organization=self.request.organization)

    def form_valid(self, form):
        form.instance.updated_by = self.request.user
        
        # Save the test run first
        response = super().form_valid(form)
        
        # Check if "Run Test" button was clicked
        if 'run_test' in self.request.POST:
            # Import here to avoid circular imports
            from .tasks import execute_test_run
            
            # Start the test execution asynchronously
            execute_test_run.delay(self.object.id)
            
            # Add success message
            messages.success(
                self.request, 
                f'Test run updated and started! Test run ID: {self.object.id}'
            )
        
        return response


class ReportsView(OrganizationPermissionMixin, LoginRequiredMixin, TemplateView):
    template_name = 'ai_governance/reports.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        organization = self.request.organization
        
        # Get model assets for filters
        model_assets = ModelAsset.objects.filter(organization=organization)
        context['model_assets'] = model_assets
        context['model_types'] = sorted(list(model_assets.values_list('model_type', flat=True).distinct()))
        
        # Get dataset assets for filters
        dataset_assets = DatasetAsset.objects.filter(organization=organization)
        context['dataset_assets'] = dataset_assets
        context['dataset_roles'] = sorted(list(dataset_assets.values_list('role', flat=True).distinct()))
        
        # Get test plans for filters
        test_plans = TestPlan.objects.filter(organization=organization)
        context['test_plans'] = test_plans
        
        # Get test runs for filters
        test_runs = TestRun.objects.filter(organization=organization)
        context['test_runs'] = test_runs
        context['test_run_statuses'] = sorted(list(test_runs.values_list('status', flat=True).distinct()))
        
        # Get frameworks for filters
        frameworks = Framework.objects.filter(organization=organization)
        context['frameworks'] = frameworks
        context['framework_codes'] = sorted(list(frameworks.values_list('code', flat=True).distinct()))
        
        # Get compliance mappings for filters
        mappings = ComplianceMapping.objects.filter(organization=organization)
        context['test_names'] = sorted(list(mappings.values_list('test_name', flat=True).distinct()))
        
        # Get recent test results for date range filters
        from datetime import datetime, timedelta
        context['date_ranges'] = [
            ('last_7_days', 'Last 7 Days'),
            ('last_30_days', 'Last 30 Days'),
            ('last_90_days', 'Last 90 Days'),
            ('last_year', 'Last Year'),
            ('all_time', 'All Time'),
        ]
        
        return context


# Additional Web UI Views for missing models
class TestResultListView(OrganizationPermissionMixin, LoginRequiredMixin, ListView):
    model = TestResult
    template_name = 'ai_governance/testresult_list.html'
    context_object_name = 'test_results'
    paginate_by = 20

    def get_queryset(self):
        return TestResult.objects.filter(organization=self.request.organization).order_by('-created_at')


class TestResultCreateView(OrganizationPermissionMixin, LoginRequiredMixin, CreateView):
    model = TestResult
    form_class = TestResultForm
    template_name = 'ai_governance/testresult_form.html'
    success_url = reverse_lazy('ai_governance:testresult_list')

    def form_valid(self, form):
        form.instance.organization = self.request.organization
        form.instance.created_by = self.request.user
        form.instance.updated_by = self.request.user
        return super().form_valid(form)


class TestResultDetailView(OrganizationPermissionMixin, LoginRequiredMixin, DetailView):
    model = TestResult
    template_name = 'ai_governance/testresult_detail.html'
    context_object_name = 'test_result'

    def get_queryset(self):
        return TestResult.objects.filter(organization=self.request.organization)


class TestResultUpdateView(OrganizationPermissionMixin, LoginRequiredMixin, UpdateView):
    model = TestResult
    form_class = TestResultForm
    template_name = 'ai_governance/testresult_form.html'
    success_url = reverse_lazy('ai_governance:testresult_list')

    def get_queryset(self):
        return TestResult.objects.filter(organization=self.request.organization)

    def form_valid(self, form):
        form.instance.updated_by = self.request.user
        return super().form_valid(form)


class MetricListView(OrganizationPermissionMixin, LoginRequiredMixin, ListView):
    model = Metric
    template_name = 'ai_governance/metric_list.html'
    context_object_name = 'metrics'
    paginate_by = 20

    def get_queryset(self):
        return Metric.objects.filter(organization=self.request.organization).order_by('-created_at')


class MetricCreateView(OrganizationPermissionMixin, LoginRequiredMixin, CreateView):
    model = Metric
    form_class = MetricForm
    template_name = 'ai_governance/metric_form.html'
    success_url = reverse_lazy('ai_governance:metric_list')

    def form_valid(self, form):
        form.instance.organization = self.request.organization
        form.instance.created_by = self.request.user
        form.instance.updated_by = self.request.user
        return super().form_valid(form)


class MetricDetailView(OrganizationPermissionMixin, LoginRequiredMixin, DetailView):
    model = Metric
    template_name = 'ai_governance/metric_detail.html'
    context_object_name = 'metric'

    def get_queryset(self):
        return Metric.objects.filter(organization=self.request.organization)


class MetricUpdateView(OrganizationPermissionMixin, LoginRequiredMixin, UpdateView):
    model = Metric
    form_class = MetricForm
    template_name = 'ai_governance/metric_form.html'
    success_url = reverse_lazy('ai_governance:metric_list')

    def get_queryset(self):
        return Metric.objects.filter(organization=self.request.organization)

    def form_valid(self, form):
        form.instance.updated_by = self.request.user
        return super().form_valid(form)


class EvidenceArtifactListView(OrganizationPermissionMixin, LoginRequiredMixin, ListView):
    model = EvidenceArtifact
    template_name = 'ai_governance/evidenceartifact_list.html'
    context_object_name = 'evidence_artifacts'
    paginate_by = 20

    def get_queryset(self):
        return EvidenceArtifact.objects.filter(organization=self.request.organization).order_by('-created_at')


class EvidenceArtifactCreateView(OrganizationPermissionMixin, LoginRequiredMixin, CreateView):
    model = EvidenceArtifact
    form_class = EvidenceArtifactForm
    template_name = 'ai_governance/evidenceartifact_form.html'
    success_url = reverse_lazy('ai_governance:evidenceartifact_list')

    def form_valid(self, form):
        form.instance.organization = self.request.organization
        form.instance.created_by = self.request.user
        form.instance.updated_by = self.request.user
        return super().form_valid(form)


class EvidenceArtifactDetailView(OrganizationPermissionMixin, LoginRequiredMixin, DetailView):
    model = EvidenceArtifact
    template_name = 'ai_governance/evidenceartifact_detail.html'
    context_object_name = 'evidence_artifact'

    def get_queryset(self):
        return EvidenceArtifact.objects.filter(organization=self.request.organization)


class EvidenceArtifactUpdateView(OrganizationPermissionMixin, LoginRequiredMixin, UpdateView):
    model = EvidenceArtifact
    form_class = EvidenceArtifactForm
    template_name = 'ai_governance/evidenceartifact_form.html'
    success_url = reverse_lazy('ai_governance:evidenceartifact_list')

    def get_queryset(self):
        return EvidenceArtifact.objects.filter(organization=self.request.organization)

    def form_valid(self, form):
        form.instance.updated_by = self.request.user
        return super().form_valid(form)


class FrameworkListView(OrganizationPermissionMixin, LoginRequiredMixin, ListView):
    model = Framework
    template_name = 'ai_governance/framework_list.html'
    context_object_name = 'frameworks'
    paginate_by = 20

    def get_queryset(self):
        return Framework.objects.filter(organization=self.request.organization).order_by('-created_at')


class FrameworkCreateView(OrganizationPermissionMixin, LoginRequiredMixin, CreateView):
    model = Framework
    form_class = FrameworkForm
    template_name = 'ai_governance/framework_form.html'
    success_url = reverse_lazy('ai_governance:framework_list')

    def form_valid(self, form):
        form.instance.organization = self.request.organization
        form.instance.created_by = self.request.user
        form.instance.updated_by = self.request.user
        return super().form_valid(form)


class FrameworkDetailView(OrganizationPermissionMixin, LoginRequiredMixin, DetailView):
    model = Framework
    template_name = 'ai_governance/framework_detail.html'
    context_object_name = 'framework'

    def get_queryset(self):
        return Framework.objects.filter(organization=self.request.organization)


class FrameworkUpdateView(OrganizationPermissionMixin, LoginRequiredMixin, UpdateView):
    model = Framework
    form_class = FrameworkForm
    template_name = 'ai_governance/framework_form.html'
    success_url = reverse_lazy('ai_governance:framework_list')

    def get_queryset(self):
        return Framework.objects.filter(organization=self.request.organization)

    def form_valid(self, form):
        form.instance.updated_by = self.request.user
        return super().form_valid(form)


class ClauseListView(OrganizationPermissionMixin, LoginRequiredMixin, ListView):
    model = Clause
    template_name = 'ai_governance/clause_list.html'
    context_object_name = 'clauses'
    paginate_by = 20

    def get_queryset(self):
        return Clause.objects.filter(organization=self.request.organization).order_by('-created_at')


class ClauseCreateView(OrganizationPermissionMixin, LoginRequiredMixin, CreateView):
    model = Clause
    form_class = ClauseForm
    template_name = 'ai_governance/clause_form.html'
    success_url = reverse_lazy('ai_governance:clause_list')

    def form_valid(self, form):
        form.instance.organization = self.request.organization
        form.instance.created_by = self.request.user
        form.instance.updated_by = self.request.user
        return super().form_valid(form)


class ClauseDetailView(OrganizationPermissionMixin, LoginRequiredMixin, DetailView):
    model = Clause
    template_name = 'ai_governance/clause_detail.html'
    context_object_name = 'clause'

    def get_queryset(self):
        return Clause.objects.filter(organization=self.request.organization)


class ClauseUpdateView(OrganizationPermissionMixin, LoginRequiredMixin, UpdateView):
    model = Clause
    form_class = ClauseForm
    template_name = 'ai_governance/clause_form.html'
    success_url = reverse_lazy('ai_governance:clause_list')

    def get_queryset(self):
        return Clause.objects.filter(organization=self.request.organization)

    def form_valid(self, form):
        form.instance.updated_by = self.request.user
        return super().form_valid(form)


class ComplianceMappingListView(OrganizationPermissionMixin, LoginRequiredMixin, ListView):
    model = ComplianceMapping
    template_name = 'ai_governance/compliancemapping_list.html'
    context_object_name = 'compliance_mappings'
    paginate_by = 20

    def get_queryset(self):
        return ComplianceMapping.objects.filter(organization=self.request.organization).order_by('-created_at')


class ComplianceMappingCreateView(OrganizationPermissionMixin, LoginRequiredMixin, CreateView):
    model = ComplianceMapping
    form_class = ComplianceMappingForm
    template_name = 'ai_governance/compliancemapping_form.html'
    success_url = reverse_lazy('ai_governance:compliancemapping_list')

    def form_valid(self, form):
        form.instance.organization = self.request.organization
        form.instance.created_by = self.request.user
        form.instance.updated_by = self.request.user
        return super().form_valid(form)


class ComplianceMappingDetailView(OrganizationPermissionMixin, LoginRequiredMixin, DetailView):
    model = ComplianceMapping
    template_name = 'ai_governance/compliancemapping_detail.html'
    context_object_name = 'compliance_mapping'

    def get_queryset(self):
        return ComplianceMapping.objects.filter(organization=self.request.organization)


class ComplianceMappingUpdateView(OrganizationPermissionMixin, LoginRequiredMixin, UpdateView):
    model = ComplianceMapping
    form_class = ComplianceMappingForm
    template_name = 'ai_governance/compliancemapping_form.html'
    success_url = reverse_lazy('ai_governance:compliancemapping_list')

    def get_queryset(self):
        return ComplianceMapping.objects.filter(organization=self.request.organization)

    def form_valid(self, form):
        form.instance.updated_by = self.request.user
        return super().form_valid(form)


class ConnectorConfigListView(OrganizationPermissionMixin, LoginRequiredMixin, ListView):
    model = ConnectorConfig
    template_name = 'ai_governance/connectorconfig_list.html'
    context_object_name = 'connector_configs'
    paginate_by = 20

    def get_queryset(self):
        return ConnectorConfig.objects.filter(organization=self.request.organization).order_by('-created_at')


class ConnectorConfigCreateView(OrganizationPermissionMixin, LoginRequiredMixin, CreateView):
    model = ConnectorConfig
    form_class = ConnectorConfigForm
    template_name = 'ai_governance/connectorconfig_form.html'
    success_url = reverse_lazy('ai_governance:connectorconfig_list')

    def form_valid(self, form):
        form.instance.organization = self.request.organization
        form.instance.created_by = self.request.user
        form.instance.updated_by = self.request.user
        return super().form_valid(form)


class ConnectorConfigDetailView(OrganizationPermissionMixin, LoginRequiredMixin, DetailView):
    model = ConnectorConfig
    template_name = 'ai_governance/connectorconfig_detail.html'
    context_object_name = 'connector_config'

    def get_queryset(self):
        return ConnectorConfig.objects.filter(organization=self.request.organization)


class ConnectorConfigUpdateView(OrganizationPermissionMixin, LoginRequiredMixin, UpdateView):
    model = ConnectorConfig
    form_class = ConnectorConfigForm
    template_name = 'ai_governance/connectorconfig_form.html'
    success_url = reverse_lazy('ai_governance:connectorconfig_list')

    def get_queryset(self):
        return ConnectorConfig.objects.filter(organization=self.request.organization)

    def form_valid(self, form):
        form.instance.updated_by = self.request.user
        return super().form_valid(form)


class WebhookSubscriptionListView(OrganizationPermissionMixin, LoginRequiredMixin, ListView):
    model = WebhookSubscription
    template_name = 'ai_governance/webhooksubscription_list.html'
    context_object_name = 'webhook_subscriptions'
    paginate_by = 20

    def get_queryset(self):
        return WebhookSubscription.objects.filter(organization=self.request.organization).order_by('-created_at')


class WebhookSubscriptionCreateView(OrganizationPermissionMixin, LoginRequiredMixin, CreateView):
    model = WebhookSubscription
    form_class = WebhookSubscriptionForm
    template_name = 'ai_governance/webhooksubscription_form.html'
    success_url = reverse_lazy('ai_governance:webhooksubscription_list')

    def form_valid(self, form):
        form.instance.organization = self.request.organization
        form.instance.created_by = self.request.user
        form.instance.updated_by = self.request.user
        return super().form_valid(form)


class WebhookSubscriptionDetailView(OrganizationPermissionMixin, LoginRequiredMixin, DetailView):
    model = WebhookSubscription
    template_name = 'ai_governance/webhooksubscription_detail.html'
    context_object_name = 'webhook_subscription'

    def get_queryset(self):
        return WebhookSubscription.objects.filter(organization=self.request.organization)


class WebhookSubscriptionUpdateView(OrganizationPermissionMixin, LoginRequiredMixin, UpdateView):
    model = WebhookSubscription
    form_class = WebhookSubscriptionForm
    template_name = 'ai_governance/webhooksubscription_form.html'
    success_url = reverse_lazy('ai_governance:webhooksubscription_list')

    def get_queryset(self):
        return WebhookSubscription.objects.filter(organization=self.request.organization)

    def form_valid(self, form):
        form.instance.updated_by = self.request.user
        return super().form_valid(form)