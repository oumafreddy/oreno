# apps/risk/views.py

from django.shortcuts import render
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.urls import reverse_lazy
from core.middleware import get_current_organization
from rest_framework import viewsets
from django_scopes import scope
from core.mixins.permissions import OrganizationPermissionMixin
from django.http import JsonResponse, HttpResponse
from django.db.models import Count, Q, Max
from django.utils import timezone
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from django.core.paginator import Paginator
import csv
try:
    import pandas as pd
except ImportError:
    pd = None
from users.permissions import IsOrgAdmin, IsOrgManagerOrReadOnly, HasOrgAdminAccess

from .models import Risk, RiskRegister, RiskMatrixConfig, Control, KRI, RiskAssessment
from .serializers import (
    RiskSerializer, SummaryCardSerializer, TopRiskSerializer, KRIStatusSerializer,
    RecentActivitySerializer, AssessmentTimelinePointSerializer,
    RiskCategoryDistributionSerializer, RiskStatusDistributionSerializer, ControlEffectivenessSerializer, KRIStatusCountSerializer, AssessmentTypeCountSerializer, RiskAssessmentSerializer
)
from .forms import RiskRegisterForm, RiskMatrixConfigForm, RiskForm, ControlForm, KRIForm, RiskAssessmentForm


@scope(provider=get_current_organization, name="organization")
class RiskScopedViewSet(viewsets.ModelViewSet):
    """
    Option A: Row‑level isolation via django‑scopes.
    All queries automatically limited by the active organization scope.
    """
    queryset = Risk.objects.all()
    serializer_class = RiskSerializer
    permission_classes = [IsOrgManagerOrReadOnly]


class RiskListView(OrganizationPermissionMixin, LoginRequiredMixin, ListView):
    """
    Web listing of Risks, automatically filtered to request.organization.
    """
    model = Risk
    template_name = 'risk/risk_list.html'
    context_object_name = 'risks'
    paginate_by = 20
    def get_queryset(self):
        qs = super().get_queryset()
        return qs.filter(organization=self.request.tenant)


class RiskDetailView(OrganizationPermissionMixin, LoginRequiredMixin, DetailView):
    """
    Web detail view of a single Risk, 404s if not in request.organization.
    """
    model = Risk
    template_name = 'risk/risk_detail.html'
    context_object_name = 'risk'
    def get_queryset(self):
        qs = super().get_queryset()
        return qs.filter(organization=self.request.tenant)


# --- RiskRegister Views ---
class RiskRegisterListView(OrganizationPermissionMixin, LoginRequiredMixin, ListView):
    model = RiskRegister
    template_name = 'risk/riskregister_list.html'
    context_object_name = 'riskregisters'
    paginate_by = 20
    def get_queryset(self):
        qs = super().get_queryset()
        return qs.filter(organization=self.request.tenant)


class RiskRegisterCreateView(OrganizationPermissionMixin, LoginRequiredMixin, CreateView):
    model = RiskRegister
    form_class = RiskRegisterForm
    template_name = 'risk/riskregister_form.html'
    success_url = reverse_lazy('risk:riskregister_list')
    def form_valid(self, form):
        form.instance.organization = self.request.tenant
        return super().form_valid(form)
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['organization'] = self.request.tenant
        return kwargs


class RiskRegisterUpdateView(OrganizationPermissionMixin, LoginRequiredMixin, UpdateView):
    model = RiskRegister
    form_class = RiskRegisterForm
    template_name = 'risk/riskregister_form.html'
    success_url = reverse_lazy('risk:riskregister_list')
    def form_valid(self, form):
        form.instance.organization = self.request.tenant
        return super().form_valid(form)
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['organization'] = self.request.tenant
        return kwargs


class RiskRegisterDetailView(OrganizationPermissionMixin, LoginRequiredMixin, DetailView):
    model = RiskRegister
    template_name = 'risk/riskregister_detail.html'
    context_object_name = 'riskregister'
    def get_queryset(self):
        qs = super().get_queryset()
        return qs.filter(organization=self.request.tenant)


class RiskRegisterDeleteView(OrganizationPermissionMixin, LoginRequiredMixin, DeleteView):
    model = RiskRegister
    template_name = 'risk/riskregister_confirm_delete.html'
    success_url = reverse_lazy('risk:riskregister_list')


# --- RiskMatrixConfig Views ---
class RiskMatrixConfigListView(OrganizationPermissionMixin, LoginRequiredMixin, ListView):
    model = RiskMatrixConfig
    template_name = 'risk/riskmatrixconfig_list.html'
    context_object_name = 'matrixconfigs'
    paginate_by = 20
    def get_queryset(self):
        qs = super().get_queryset()
        return qs.filter(organization=self.request.tenant)


class RiskMatrixConfigCreateView(OrganizationPermissionMixin, LoginRequiredMixin, CreateView):
    model = RiskMatrixConfig
    form_class = RiskMatrixConfigForm
    template_name = 'risk/riskmatrixconfig_form.html'
    success_url = reverse_lazy('risk:riskmatrixconfig_list')
    def form_valid(self, form):
        form.instance.organization = self.request.tenant
        return super().form_valid(form)
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['organization'] = self.request.tenant
        return kwargs


class RiskMatrixConfigUpdateView(OrganizationPermissionMixin, LoginRequiredMixin, UpdateView):
    model = RiskMatrixConfig
    form_class = RiskMatrixConfigForm
    template_name = 'risk/riskmatrixconfig_form.html'
    success_url = reverse_lazy('risk:riskmatrixconfig_list')
    def form_valid(self, form):
        form.instance.organization = self.request.tenant
        return super().form_valid(form)
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['organization'] = self.request.tenant
        return kwargs


class RiskMatrixConfigDetailView(OrganizationPermissionMixin, LoginRequiredMixin, DetailView):
    model = RiskMatrixConfig
    template_name = 'risk/riskmatrixconfig_detail.html'
    context_object_name = 'matrixconfig'
    def get_queryset(self):
        qs = super().get_queryset()
        return qs.filter(organization=self.request.tenant)


class RiskMatrixConfigDeleteView(OrganizationPermissionMixin, LoginRequiredMixin, DeleteView):
    model = RiskMatrixConfig
    template_name = 'risk/riskmatrixconfig_confirm_delete.html'
    success_url = reverse_lazy('risk:riskmatrixconfig_list')


# --- Risk Views ---
class RiskCreateView(OrganizationPermissionMixin, LoginRequiredMixin, CreateView):
    model = Risk
    form_class = RiskForm
    template_name = 'risk/risk_form.html'
    success_url = reverse_lazy('risk:risk_list')
    def form_valid(self, form):
        form.instance.organization = self.request.tenant
        return super().form_valid(form)
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['organization'] = self.request.tenant
        return kwargs


class RiskUpdateView(OrganizationPermissionMixin, LoginRequiredMixin, UpdateView):
    model = Risk
    form_class = RiskForm
    template_name = 'risk/risk_form.html'
    success_url = reverse_lazy('risk:risk_list')
    def form_valid(self, form):
        form.instance.organization = self.request.tenant
        return super().form_valid(form)
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['organization'] = self.request.tenant
        return kwargs


class RiskDeleteView(OrganizationPermissionMixin, LoginRequiredMixin, DeleteView):
    model = Risk
    template_name = 'risk/risk_confirm_delete.html'
    success_url = reverse_lazy('risk:risk_list')


# --- Control Views ---
class ControlListView(OrganizationPermissionMixin, LoginRequiredMixin, ListView):
    model = Control
    template_name = 'risk/control_list.html'
    context_object_name = 'controls'
    paginate_by = 20
    def get_queryset(self):
        qs = super().get_queryset()
        return qs.filter(organization=self.request.tenant)


class ControlCreateView(OrganizationPermissionMixin, LoginRequiredMixin, CreateView):
    model = Control
    form_class = ControlForm
    template_name = 'risk/control_form.html'
    success_url = reverse_lazy('risk:control_list')
    def form_valid(self, form):
        form.instance.organization = self.request.tenant
        return super().form_valid(form)
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['organization'] = self.request.tenant
        return kwargs


class ControlUpdateView(OrganizationPermissionMixin, LoginRequiredMixin, UpdateView):
    model = Control
    form_class = ControlForm
    template_name = 'risk/control_form.html'
    success_url = reverse_lazy('risk:control_list')
    def form_valid(self, form):
        form.instance.organization = self.request.tenant
        return super().form_valid(form)
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['organization'] = self.request.tenant
        return kwargs


class ControlDetailView(OrganizationPermissionMixin, LoginRequiredMixin, DetailView):
    model = Control
    template_name = 'risk/control_detail.html'
    context_object_name = 'control'
    def get_queryset(self):
        qs = super().get_queryset()
        return qs.filter(organization=self.request.tenant)


class ControlDeleteView(OrganizationPermissionMixin, LoginRequiredMixin, DeleteView):
    model = Control
    template_name = 'risk/control_confirm_delete.html'
    success_url = reverse_lazy('risk:control_list')


# --- KRI Views ---
class KRIListView(OrganizationPermissionMixin, LoginRequiredMixin, ListView):
    model = KRI
    template_name = 'risk/kri_list.html'
    context_object_name = 'kris'
    paginate_by = 20
    def get_queryset(self):
        qs = super().get_queryset()
        return qs.filter(risk__organization=self.request.tenant)


class KRICreateView(OrganizationPermissionMixin, LoginRequiredMixin, CreateView):
    model = KRI
    form_class = KRIForm
    template_name = 'risk/kri_form.html'
    success_url = reverse_lazy('risk:kri_list')
    def form_valid(self, form):
        form.instance.organization = self.request.tenant
        return super().form_valid(form)
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['organization'] = self.request.tenant
        return kwargs


class KRIUpdateView(OrganizationPermissionMixin, LoginRequiredMixin, UpdateView):
    model = KRI
    form_class = KRIForm
    template_name = 'risk/kri_form.html'
    success_url = reverse_lazy('risk:kri_list')
    def form_valid(self, form):
        form.instance.organization = self.request.tenant
        return super().form_valid(form)
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['organization'] = self.request.tenant
        return kwargs


class KRIDetailView(OrganizationPermissionMixin, LoginRequiredMixin, DetailView):
    model = KRI
    template_name = 'risk/kri_detail.html'
    context_object_name = 'kri'
    def get_queryset(self):
        qs = super().get_queryset()
        return qs.filter(risk__organization=self.request.tenant)


class KRIDeleteView(OrganizationPermissionMixin, LoginRequiredMixin, DeleteView):
    model = KRI
    template_name = 'risk/kri_confirm_delete.html'
    success_url = reverse_lazy('risk:kri_list')


# --- RiskAssessment Views ---
class RiskAssessmentListView(OrganizationPermissionMixin, LoginRequiredMixin, ListView):
    model = RiskAssessment
    template_name = 'risk/riskassessment_list.html'
    context_object_name = 'riskassessments'
    paginate_by = 20
    def get_queryset(self):
        qs = super().get_queryset()
        return qs.filter(organization=self.request.tenant)


class RiskAssessmentCreateView(OrganizationPermissionMixin, LoginRequiredMixin, CreateView):
    model = RiskAssessment
    form_class = RiskAssessmentForm
    template_name = 'risk/riskassessment_form.html'
    success_url = reverse_lazy('risk:riskassessment_list')
    def form_valid(self, form):
        form.instance.organization = self.request.tenant
        return super().form_valid(form)
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['organization'] = self.request.tenant
        return kwargs


class RiskAssessmentUpdateView(OrganizationPermissionMixin, LoginRequiredMixin, UpdateView):
    model = RiskAssessment
    form_class = RiskAssessmentForm
    template_name = 'risk/riskassessment_form.html'
    success_url = reverse_lazy('risk:riskassessment_list')
    def form_valid(self, form):
        form.instance.organization = self.request.tenant
        return super().form_valid(form)
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['organization'] = self.request.tenant
        return kwargs


class RiskAssessmentDetailView(OrganizationPermissionMixin, LoginRequiredMixin, DetailView):
    model = RiskAssessment
    template_name = 'risk/riskassessment_detail.html'
    context_object_name = 'riskassessment'
    def get_queryset(self):
        qs = super().get_queryset()
        return qs.filter(organization=self.request.tenant)


class RiskAssessmentDeleteView(OrganizationPermissionMixin, LoginRequiredMixin, DeleteView):
    model = RiskAssessment
    template_name = 'risk/riskassessment_confirm_delete.html'
    success_url = reverse_lazy('risk:riskassessment_list')


def get_active_matrix_config(org):
    return RiskMatrixConfig.objects.filter(organization=org, is_active=True).first()

class RiskDashboardView(OrganizationPermissionMixin, LoginRequiredMixin, ListView):
    template_name = 'risk/list.html'
    context_object_name = 'dashboard'
    def get_queryset(self):
        return []  # Not used
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        org = self.request.tenant
        selected_register = self.request.GET.get('register')
        riskregisters = RiskRegister.objects.filter(organization=org)
        risks = Risk.objects.filter(organization=org)
        if selected_register:
            risks = risks.filter(risk_register_id=selected_register)
        controls = Control.objects.filter(organization=org)
        kris = KRI.objects.filter(risk__organization=org)
        assessments = RiskAssessment.objects.filter(risk__organization=org)
        matrix = get_active_matrix_config(org)
        # Advanced analytics
        from collections import Counter
        # Risks by category
        category_dist = risks.values_list('category', flat=True)
        context['risk_category_dist'] = dict(Counter(category_dist))
        # Risks by status
        status_dist = risks.values_list('status', flat=True)
        context['risk_status_dist'] = dict(Counter(status_dist))
        # Risks by owner
        owner_dist = risks.values_list('risk_owner', flat=True)
        context['risk_owner_dist'] = dict(Counter(owner_dist))
        # Risks by register
        register_dist = risks.values_list('risk_register__register_name', flat=True)
        context['risk_register_dist'] = dict(Counter(register_dist))
        # KRI status breakdown
        kri_status_dist = [kri.get_status() for kri in kris]
        context['kri_status_dist'] = dict(Counter(kri_status_dist))
        # Control effectiveness
        control_effectiveness_dist = controls.values_list('effectiveness_rating', flat=True)
        context['control_effectiveness_dist'] = dict(Counter(control_effectiveness_dist))
        # Risk trend: count by month
        from django.db.models.functions import TruncMonth
        risk_trend = risks.annotate(month=TruncMonth('date_identified')).values('month').annotate(count=Count('id')).order_by('month')
        context['risk_trend'] = [{'month': r['month'].strftime('%Y-%m') if r['month'] else '', 'count': r['count']} for r in risk_trend]
        # Summary cards
        context['riskregisters'] = riskregisters
        context['selected_register'] = int(selected_register) if selected_register else None
        context['total_risks'] = risks.count()
        context['total_controls'] = controls.count()
        context['total_kris'] = kris.count()
        context['total_assessments'] = assessments.count()
        context['high_critical_risks'] = risks.filter(residual_risk_score__gte=matrix.high_threshold if matrix else 15).count() if matrix else 0
        context['recent_activity_count'] = assessments.filter(assessment_date__gte=timezone.now()-timezone.timedelta(days=7)).count()
        # Top risks
        context['top_risks'] = risks.order_by('-residual_risk_score')[:5]
        # KRI status
        context['kris_status'] = kris.order_by('-timestamp')[:10]
        # Recent activity (simple example)
        context['recent_activity'] = [
            f"Assessment for {a.risk.risk_name} on {a.assessment_date}" for a in assessments.order_by('-assessment_date')[:10]
        ]
        context['report_links'] = [
            {
                'label': 'Download Risk Register PDF',
                'url': '/reports/risk/pdf/'
            },
        ]
        return context

# --- API Endpoints for Dashboard Widgets ---
@api_view(['GET'])
@permission_classes([IsAuthenticated, IsOrgManagerOrReadOnly])
def api_heatmap_data(request):
    org = request.tenant
    selected_register = request.GET.get('register')
    risks = Risk.objects.filter(organization=org)
    if selected_register:
        risks = risks.filter(risk_register_id=selected_register)
    matrix = get_active_matrix_config(org)
    # Prepare heatmap data (impact vs likelihood, colored by risk level)
    z = []
    x = list(range(1, (matrix.impact_levels if matrix else 5)+1))
    y = list(range(1, (matrix.likelihood_levels if matrix else 5)+1))
    for i in y:
        row = []
        for j in x:
            count = risks.filter(residual_impact_score=j, residual_likelihood_score=i).count()
            row.append(count)
        z.append(row)
    data = [{
        'z': z,
        'x': x,
        'y': y,
        'type': 'heatmap',
        'colorscale': 'YlOrRd',
        'colorbar': {'title': 'Risk Count'}
    }]
    layout = {
        'title': 'Risk Heat Map',
        'xaxis': {'title': 'Impact'},
        'yaxis': {'title': 'Likelihood'},
        'height': 400
    }
    return JsonResponse({'data': data, 'layout': layout})

@api_view(['GET'])
@permission_classes([IsAuthenticated, IsOrgManagerOrReadOnly])
def api_assessment_timeline(request):
    org = request.tenant
    selected_register = request.GET.get('register')
    risks = Risk.objects.filter(organization=org)
    if selected_register:
        risks = risks.filter(risk_register_id=selected_register)
    assessments = RiskAssessment.objects.filter(risk__in=risks)
    # Group by date, show average risk score over time
    timeline = assessments.values('assessment_date').annotate(avg_score=Count('risk_score')).order_by('assessment_date')
    x = [t['assessment_date'] for t in timeline]
    y = [t['avg_score'] for t in timeline]
    data = [{
        'x': x,
        'y': y,
        'type': 'scatter',
        'mode': 'lines+markers',
        'name': 'Avg Risk Score'
    }]
    layout = {
        'title': 'Assessment Timeline',
        'xaxis': {'title': 'Date'},
        'yaxis': {'title': 'Avg Risk Score'},
        'height': 250
    }
    return JsonResponse({'data': data, 'layout': layout})

@api_view(['GET'])
@permission_classes([IsAuthenticated, IsOrgManagerOrReadOnly])
def api_summary_cards(request):
    org = request.tenant
    selected_register = request.GET.get('register')
    risks = Risk.objects.filter(organization=org)
    if selected_register:
        risks = risks.filter(risk_register_id=selected_register)
    controls = Control.objects.filter(organization=org)
    kris = KRI.objects.filter(risk__organization=org)
    assessments = RiskAssessment.objects.filter(risk__organization=org)
    matrix = get_active_matrix_config(org)
    data = {
        'total_risks': risks.count(),
        'total_controls': controls.count(),
        'total_kris': kris.count(),
        'total_assessments': assessments.count(),
        'high_critical_risks': risks.filter(residual_risk_score__gte=matrix.high_threshold if matrix else 15).count() if matrix else 0,
        'recent_activity_count': assessments.filter(assessment_date__gte=timezone.now()-timezone.timedelta(days=7)).count(),
    }
    return JsonResponse(SummaryCardSerializer(data).data)

@api_view(['GET'])
@permission_classes([IsAuthenticated, IsOrgManagerOrReadOnly])
def api_top_risks(request):
    org = request.tenant
    selected_register = request.GET.get('register')
    risks = Risk.objects.filter(organization=org)
    if selected_register:
        risks = risks.filter(risk_register_id=selected_register)
    top_risks = risks.order_by('-residual_risk_score')[:5]
    data = TopRiskSerializer(top_risks, many=True).data
    return JsonResponse({'results': data})

@api_view(['GET'])
@permission_classes([IsAuthenticated, IsOrgManagerOrReadOnly])
def api_kri_status(request):
    org = request.tenant
    selected_register = request.GET.get('register')
    kris = KRI.objects.filter(risk__organization=org)
    if selected_register:
        kris = kris.filter(risk__risk_register_id=selected_register)
    kris = kris.order_by('-timestamp')[:10]
    data = KRIStatusSerializer(kris, many=True).data
    return JsonResponse({'results': data})

@api_view(['GET'])
@permission_classes([IsAuthenticated, IsOrgManagerOrReadOnly])
def api_recent_activity(request):
    org = request.tenant
    selected_register = request.GET.get('register')
    risks = Risk.objects.filter(organization=org)
    if selected_register:
        risks = risks.filter(risk_register_id=selected_register)
    assessments = RiskAssessment.objects.filter(risk__in=risks).order_by('-assessment_date')[:10]
    activity = [
        {'message': f"Assessment for {a.risk.risk_name} on {a.assessment_date}", 'timestamp': a.assessment_date}
        for a in assessments
    ]
    return JsonResponse({'results': RecentActivitySerializer(activity, many=True).data})

@api_view(['GET'])
@permission_classes([IsAuthenticated, IsOrgManagerOrReadOnly])
def api_assessment_timeline_details(request):
    org = request.tenant
    selected_register = request.GET.get('register')
    risks = Risk.objects.filter(organization=org)
    if selected_register:
        risks = risks.filter(risk_register_id=selected_register)
    assessments = RiskAssessment.objects.filter(risk__in=risks)
    timeline = assessments.values('assessment_date').annotate(avg_score=Count('risk_score')).order_by('assessment_date')
    data = [
        {'date': t['assessment_date'], 'avg_score': t['avg_score']} for t in timeline
    ]
    return JsonResponse({'results': AssessmentTimelinePointSerializer(data, many=True).data})

@api_view(['GET'])
@permission_classes([IsAuthenticated, IsOrgManagerOrReadOnly])
def api_risk_category_distribution(request):
    org = request.tenant
    selected_register = request.GET.get('register')
    risks = Risk.objects.filter(organization=org)
    if selected_register:
        risks = risks.filter(risk_register_id=selected_register)
    data = risks.values('category').annotate(count=Count('id')).order_by('category')
    return JsonResponse({'results': RiskCategoryDistributionSerializer(data, many=True).data})

@api_view(['GET'])
@permission_classes([IsAuthenticated, IsOrgManagerOrReadOnly])
def api_risk_status_distribution(request):
    org = request.tenant
    selected_register = request.GET.get('register')
    risks = Risk.objects.filter(organization=org)
    if selected_register:
        risks = risks.filter(risk_register_id=selected_register)
    data = risks.values('status').annotate(count=Count('id')).order_by('status')
    return JsonResponse({'results': RiskStatusDistributionSerializer(data, many=True).data})

@api_view(['GET'])
@permission_classes([IsAuthenticated, IsOrgManagerOrReadOnly])
def api_control_effectiveness(request):
    org = request.tenant
    controls = Control.objects.filter(organization=org)
    data = controls.values('effectiveness_rating').annotate(count=Count('id')).order_by('effectiveness_rating')
    # Map to serializer field
    data = [{'effectiveness': d['effectiveness_rating'], 'count': d['count']} for d in data]
    return JsonResponse({'results': ControlEffectivenessSerializer(data, many=True).data})

@api_view(['GET'])
@permission_classes([IsAuthenticated, IsOrgManagerOrReadOnly])
def api_kri_status_counts(request):
    org = request.tenant
    selected_register = request.GET.get('register')
    kris = KRI.objects.filter(risk__organization=org)
    if selected_register:
        kris = kris.filter(risk__risk_register_id=selected_register)
    # Count by status
    status_counts = {'normal': 0, 'warning': 0, 'critical': 0}
    for kri in kris:
        status = kri.get_status()
        if status in status_counts:
            status_counts[status] += 1
    data = [{'status': k, 'count': v} for k, v in status_counts.items()]
    return JsonResponse({'results': KRIStatusCountSerializer(data, many=True).data})

@api_view(['GET'])
@permission_classes([IsAuthenticated, IsOrgManagerOrReadOnly])
def api_assessment_type_counts(request):
    org = request.tenant
    selected_register = request.GET.get('register')
    risks = Risk.objects.filter(organization=org)
    if selected_register:
        risks = risks.filter(risk_register_id=selected_register)
    assessments = RiskAssessment.objects.filter(risk__in=risks)
    data = assessments.values('assessment_type').annotate(count=Count('id')).order_by('assessment_type')
    # Map to serializer field
    data = [{'assessment_type': d['assessment_type'], 'count': d['count']} for d in data]
    return JsonResponse({'results': AssessmentTypeCountSerializer(data, many=True).data})

@api_view(['GET'])
@permission_classes([IsAuthenticated, IsOrgManagerOrReadOnly])
def api_risk_advanced_filter(request):
    org = request.tenant
    qs = Risk.objects.filter(organization=org)
    owner = request.GET.get('owner')
    category = request.GET.get('category')
    status = request.GET.get('status')
    min_score = request.GET.get('min_score')
    max_score = request.GET.get('max_score')
    register = request.GET.get('register')
    if owner:
        qs = qs.filter(risk_owner__icontains=owner)
    if category:
        qs = qs.filter(category=category)
    if status:
        qs = qs.filter(status=status)
    if min_score:
        qs = qs.filter(residual_risk_score__gte=min_score)
    if max_score:
        qs = qs.filter(residual_risk_score__lte=max_score)
    if register:
        qs = qs.filter(risk_register_id=register)
    # Pagination
    page = int(request.GET.get('page', 1))
    page_size = int(request.GET.get('page_size', 20))
    paginator = Paginator(qs.order_by('-residual_risk_score'), page_size)
    page_obj = paginator.get_page(page)
    data = TopRiskSerializer(page_obj.object_list, many=True).data
    return JsonResponse({
        'results': data,
        'count': paginator.count,
        'num_pages': paginator.num_pages,
        'page': page
    })

# --- KRI Advanced Filter API ---
@api_view(['GET'])
@permission_classes([IsAuthenticated, IsOrgManagerOrReadOnly])
def api_kri_advanced_filter(request):
    org = request.tenant
    qs = KRI.objects.filter(risk__organization=org)
    risk = request.GET.get('risk')
    status = request.GET.get('status')
    min_value = request.GET.get('min_value')
    max_value = request.GET.get('max_value')
    direction = request.GET.get('direction')
    register = request.GET.get('register')
    if risk:
        qs = qs.filter(risk_id=risk)
    if status:
        qs = [k for k in qs if k.get_status() == status]
    if min_value:
        qs = [k for k in qs if k.value >= float(min_value)]
    if max_value:
        qs = [k for k in qs if k.value <= float(max_value)]
    if direction:
        qs = [k for k in qs if k.direction == direction]
    if register:
        qs = [k for k in qs if str(k.risk.risk_register_id) == str(register)]
    # Pagination
    page = int(request.GET.get('page', 1))
    page_size = int(request.GET.get('page_size', 20))
    total = len(qs)
    qs = qs[(page-1)*page_size:page*page_size]
    data = KRIStatusSerializer(qs, many=True).data
    return JsonResponse({
        'results': data,
        'count': total,
        'num_pages': (total + page_size - 1) // page_size,
        'page': page
    })

# --- RiskAssessment Advanced Filter API ---
@api_view(['GET'])
@permission_classes([IsAuthenticated, IsOrgManagerOrReadOnly])
def api_assessment_advanced_filter(request):
    org = request.tenant
    qs = RiskAssessment.objects.filter(risk__organization=org)
    risk = request.GET.get('risk')
    assessment_type = request.GET.get('assessment_type')
    assessor = request.GET.get('assessor')
    min_score = request.GET.get('min_score')
    max_score = request.GET.get('max_score')
    register = request.GET.get('register')
    if risk:
        qs = qs.filter(risk_id=risk)
    if assessment_type:
        qs = qs.filter(assessment_type=assessment_type)
    if assessor:
        qs = qs.filter(assessor__icontains=assessor)
    if min_score:
        qs = qs.filter(risk_score__gte=min_score)
    if max_score:
        qs = qs.filter(risk_score__lte=max_score)
    if register:
        qs = qs.filter(risk__risk_register_id=register)
    # Pagination
    page = int(request.GET.get('page', 1))
    page_size = int(request.GET.get('page_size', 20))
    paginator = Paginator(qs.order_by('-assessment_date'), page_size)
    page_obj = paginator.get_page(page)
    data = RiskAssessmentSerializer(page_obj.object_list, many=True).data
    return JsonResponse({
        'results': data,
        'count': paginator.count,
        'num_pages': paginator.num_pages,
        'page': page
    })

# --- CSV/Excel Export for Risk, KRI, RiskAssessment ---
def queryset_to_csv_response(qs, fields, filename):
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    writer = csv.writer(response)
    writer.writerow(fields)
    for obj in qs:
        writer.writerow([getattr(obj, f) if not callable(getattr(obj, f)) else getattr(obj, f)() for f in fields])
    return response

def queryset_to_excel_response(qs, fields, filename):
    if not pd:
        return HttpResponse('Pandas not installed', status=500)
    data = []
    for obj in qs:
        data.append({f: getattr(obj, f) if not callable(getattr(obj, f)) else getattr(obj, f)() for f in fields})
    df = pd.DataFrame(data)
    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    df.to_excel(response, index=False)
    return response

@api_view(['GET'])
@permission_classes([IsAuthenticated, IsOrgManagerOrReadOnly])
def export_risks(request):
    org = request.tenant
    qs = Risk.objects.filter(organization=org)
    # Apply same filters as api_risk_advanced_filter
    owner = request.GET.get('owner')
    category = request.GET.get('category')
    status = request.GET.get('status')
    min_score = request.GET.get('min_score')
    max_score = request.GET.get('max_score')
    register = request.GET.get('register')
    if owner:
        qs = qs.filter(risk_owner__icontains=owner)
    if category:
        qs = qs.filter(category=category)
    if status:
        qs = qs.filter(status=status)
    if min_score:
        qs = qs.filter(residual_risk_score__gte=min_score)
    if max_score:
        qs = qs.filter(residual_risk_score__lte=max_score)
    if register:
        qs = qs.filter(risk_register_id=register)
    fields = ['id', 'risk_name', 'risk_owner', 'category', 'status', 'residual_risk_score']
    fmt = request.GET.get('format', 'csv')
    if fmt == 'excel':
        return queryset_to_excel_response(qs, fields, 'risks.xlsx')
    return queryset_to_csv_response(qs, fields, 'risks.csv')

@api_view(['GET'])
@permission_classes([IsAuthenticated, IsOrgManagerOrReadOnly])
def export_kris(request):
    org = request.tenant
    qs = KRI.objects.filter(risk__organization=org)
    # Apply same filters as api_kri_advanced_filter
    risk = request.GET.get('risk')
    status = request.GET.get('status')
    min_value = request.GET.get('min_value')
    max_value = request.GET.get('max_value')
    direction = request.GET.get('direction')
    register = request.GET.get('register')
    if risk:
        qs = qs.filter(risk_id=risk)
    if status:
        qs = [k for k in qs if k.get_status() == status]
    if min_value:
        qs = [k for k in qs if k.value >= float(min_value)]
    if max_value:
        qs = [k for k in qs if k.value <= float(max_value)]
    if direction:
        qs = [k for k in qs if k.direction == direction]
    if register:
        qs = [k for k in qs if str(k.risk.risk_register_id) == str(register)]
    fields = ['id', 'name', 'risk', 'value', 'unit', 'timestamp', 'direction']
    fmt = request.GET.get('format', 'csv')
    if fmt == 'excel':
        return queryset_to_excel_response(qs, fields, 'kris.xlsx')
    return queryset_to_csv_response(qs, fields, 'kris.csv')

@api_view(['GET'])
@permission_classes([IsAuthenticated, IsOrgManagerOrReadOnly])
def export_assessments(request):
    org = request.tenant
    qs = RiskAssessment.objects.filter(risk__organization=org)
    # Apply same filters as api_assessment_advanced_filter
    risk = request.GET.get('risk')
    assessment_type = request.GET.get('assessment_type')
    assessor = request.GET.get('assessor')
    min_score = request.GET.get('min_score')
    max_score = request.GET.get('max_score')
    register = request.GET.get('register')
    if risk:
        qs = qs.filter(risk_id=risk)
    if assessment_type:
        qs = qs.filter(assessment_type=assessment_type)
    if assessor:
        qs = qs.filter(assessor__icontains=assessor)
    if min_score:
        qs = qs.filter(risk_score__gte=min_score)
    if max_score:
        qs = qs.filter(risk_score__lte=max_score)
    if register:
        qs = qs.filter(risk__risk_register_id=register)
    fields = ['id', 'risk', 'assessment_date', 'assessor', 'assessment_type', 'impact_score', 'likelihood_score', 'risk_score']
    fmt = request.GET.get('format', 'csv')
    if fmt == 'excel':
        return queryset_to_excel_response(qs, fields, 'assessments.xlsx')
    return queryset_to_csv_response(qs, fields, 'assessments.csv')
