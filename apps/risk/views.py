# apps/risk/views.py

from django.shortcuts import render
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView, TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.urls import reverse_lazy
from core.middleware import get_current_organization
from rest_framework import viewsets
from django_scopes import scope
from core.mixins.permissions import OrganizationPermissionMixin
from django.http import JsonResponse, HttpResponse
from django.db.models import Count, Q, Max, Avg
from django.db import models
from django.utils import timezone
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from django.core.paginator import Paginator
import csv
try:
    import pandas as pd
except ImportError:
    pd = None
from users.permissions import IsOrgAdmin, IsOrgManagerOrReadOnly, HasOrgAdminAccess, IsRiskChampionOrManagerOrReadOnly
from django.core.exceptions import PermissionDenied

from .models import (
    Risk, RiskRegister, RiskMatrixConfig, Control, KRI, RiskAssessment,
    # COBIT models
    COBITDomain, COBITProcess, COBITCapability, COBITControl, COBITGovernance,
    # NIST models
    NISTFunction, NISTCategory, NISTSubcategory, NISTImplementation, NISTThreat, NISTIncident,
    Objective
)
from .serializers import (
    RiskSerializer, SummaryCardSerializer, TopRiskSerializer, KRIStatusSerializer,
    RecentActivitySerializer, AssessmentTimelinePointSerializer,
    RiskCategoryDistributionSerializer, RiskStatusDistributionSerializer, ControlEffectivenessSerializer, KRIStatusCountSerializer, AssessmentTypeCountSerializer, RiskAssessmentSerializer,
    ObjectiveSerializer,
    # COBIT serializers
    COBITDomainSerializer, COBITProcessSerializer, COBITCapabilitySerializer, COBITControlSerializer, COBITGovernanceSerializer,
    # NIST serializers
    NISTFunctionSerializer, NISTCategorySerializer, NISTSubcategorySerializer, NISTImplementationSerializer, NISTThreatSerializer, NISTIncidentSerializer
)
from .forms import (
    RiskRegisterForm, RiskMatrixConfigForm, RiskForm, ControlForm, KRIForm, RiskAssessmentForm, RiskRegisterFilterForm, RiskMatrixConfigFilterForm,
    ObjectiveForm,
    # COBIT forms
    COBITDomainForm, COBITProcessForm, COBITCapabilityForm, COBITControlForm, COBITGovernanceForm,
    # NIST forms
    NISTFunctionForm, NISTCategoryForm, NISTSubcategoryForm, NISTImplementationForm, NISTThreatForm, NISTIncidentForm
)


@scope(provider=get_current_organization, name="organization")
class RiskScopedViewSet(viewsets.ModelViewSet):
    """
    Option A: Row‑level isolation via django‑scopes.
    All queries automatically limited by the active organization scope.
    """
    queryset = Risk.objects.all()
    serializer_class = RiskSerializer
    permission_classes = [IsRiskChampionOrManagerOrReadOnly]


class OrganizationPermissionMixin:
    """Mixin to ensure the user has access to the current organization."""
    def dispatch(self, request, *args, **kwargs):
        # First check if user is authenticated - if not, LoginRequiredMixin will handle redirect
        if not request.user.is_authenticated:
            return super().dispatch(request, *args, **kwargs)
        
        # Only check organization context if user is authenticated
        if not hasattr(request, 'organization') or request.organization is None:
            raise PermissionDenied("No organization context found.")

        # Enforce Risk Champion scope within Risk app
        if request.user.role == 'risk_champion':
            # Require explicit opt-in for ANY access on class-based views
            if not getattr(self, 'allow_risk_champion_access', False):
                raise PermissionDenied("Risk Champion is restricted to specific Risk features only.")
            # Additionally require explicit opt-in for write operations
            if request.method not in ('GET', 'HEAD', 'OPTIONS') and not getattr(self, 'allow_risk_champion_write', False):
                raise PermissionDenied("Risk Champion is restricted to core Risk CRUD only.")
        return super().dispatch(request, *args, **kwargs)


class RiskListView(OrganizationPermissionMixin, LoginRequiredMixin, ListView):
    """
    Web listing of Risks, automatically filtered to request.organization.
    """
    model = Risk
    template_name = 'risk/risk_list.html'
    context_object_name = 'risks'
    paginate_by = 20
    allow_risk_champion_access = True
    def get_queryset(self):
        qs = super().get_queryset()
        qs = qs.filter(organization=self.request.organization)
        q = self.request.GET.get('q')
        if q:
            qs = qs.filter(risk_name__icontains=q)
        owner = self.request.GET.get('owner')
        if owner:
            qs = qs.filter(risk_owner__icontains=owner)
        category = self.request.GET.get('category')
        if category:
            qs = qs.filter(category=category)
        status = self.request.GET.get('status')
        if status:
            qs = qs.filter(status=status)
        min_score = self.request.GET.get('min_score')
        if min_score:
            qs = qs.filter(residual_risk_score__gte=min_score)
        max_score = self.request.GET.get('max_score')
        if max_score:
            qs = qs.filter(residual_risk_score__lte=max_score)
        register = self.request.GET.get('register')
        if register:
            qs = qs.filter(risk_register_id=register)
        return qs
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['risks'] = self.get_queryset()
        return context


class RiskDetailView(OrganizationPermissionMixin, LoginRequiredMixin, DetailView):
    """
    Web detail view of a single Risk, 404s if not in request.organization.
    """
    model = Risk
    template_name = 'risk/risk_detail.html'
    context_object_name = 'risk'
    allow_risk_champion_access = True
    def get_queryset(self):
        qs = super().get_queryset()
        return qs.filter(organization=self.request.organization)


# --- RiskRegister Views ---
class RiskRegisterListView(OrganizationPermissionMixin, LoginRequiredMixin, ListView):
    model = RiskRegister
    template_name = 'risk/riskregister_list.html'
    context_object_name = 'riskregisters'
    paginate_by = 20
    allow_risk_champion_access = True
    def get_queryset(self):
        qs = super().get_queryset()
        qs = qs.filter(organization=self.request.organization)
        form = RiskRegisterFilterForm(self.request.GET)
        if form.is_valid():
            q = form.cleaned_data.get('q')
            if q:
                qs = qs.filter(Q(register_name__icontains=q) | Q(code__icontains=q))
            period = form.cleaned_data.get('period')
            if period:
                qs = qs.filter(register_period__icontains=period)
        return qs
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['filter_form'] = RiskRegisterFilterForm(self.request.GET)
        return context


class RiskRegisterCreateView(OrganizationPermissionMixin, LoginRequiredMixin, CreateView):
    model = RiskRegister
    form_class = RiskRegisterForm
    template_name = 'risk/riskregister_form.html'
    success_url = reverse_lazy('risk:riskregister_list')
    allow_risk_champion_access = True
    allow_risk_champion_write = True
    def form_valid(self, form):
        form.instance.organization = self.request.organization
        form.instance.created_by = self.request.user
        form.instance.updated_by = self.request.user
        return super().form_valid(form)
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['organization'] = self.request.organization
        return kwargs


class RiskRegisterUpdateView(OrganizationPermissionMixin, LoginRequiredMixin, UpdateView):
    model = RiskRegister
    form_class = RiskRegisterForm
    template_name = 'risk/riskregister_form.html'
    success_url = reverse_lazy('risk:riskregister_list')
    allow_risk_champion_access = True
    allow_risk_champion_write = True
    def form_valid(self, form):
        form.instance.organization = self.request.organization
        form.instance.updated_by = self.request.user
        return super().form_valid(form)
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['organization'] = self.request.organization
        return kwargs


class RiskRegisterDetailView(OrganizationPermissionMixin, LoginRequiredMixin, DetailView):
    model = RiskRegister
    template_name = 'risk/riskregister_detail.html'
    context_object_name = 'riskregister'
    allow_risk_champion_access = True
    def get_queryset(self):
        qs = super().get_queryset()
        return qs.filter(organization=self.request.organization)


class RiskRegisterDeleteView(OrganizationPermissionMixin, LoginRequiredMixin, DeleteView):
    model = RiskRegister
    template_name = 'risk/riskregister_confirm_delete.html'
    success_url = reverse_lazy('risk:riskregister_list')
    allow_risk_champion_access = True
    allow_risk_champion_write = True
    def get_queryset(self):
        return super().get_queryset().filter(organization=self.request.organization)


# --- RiskMatrixConfig Views ---
class RiskMatrixConfigListView(OrganizationPermissionMixin, LoginRequiredMixin, ListView):
    model = RiskMatrixConfig
    template_name = 'risk/riskmatrixconfig_list.html'
    context_object_name = 'matrixconfigs'
    paginate_by = 20
    def get_queryset(self):
        qs = super().get_queryset()
        qs = qs.filter(organization=self.request.organization)
        form = RiskMatrixConfigFilterForm(self.request.GET)
        if form.is_valid():
            name = form.cleaned_data.get('name')
            if name:
                qs = qs.filter(name__icontains=name)
            is_active = form.cleaned_data.get('is_active')
            if is_active == '1':
                qs = qs.filter(is_active=True)
            elif is_active == '0':
                qs = qs.filter(is_active=False)
        return qs
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['filter_form'] = RiskMatrixConfigFilterForm(self.request.GET)
        return context


class RiskMatrixConfigCreateView(OrganizationPermissionMixin, LoginRequiredMixin, CreateView):
    model = RiskMatrixConfig
    form_class = RiskMatrixConfigForm
    template_name = 'risk/riskmatrixconfig_form.html'
    success_url = reverse_lazy('risk:riskmatrixconfig_list')
    def form_valid(self, form):
        form.instance.organization = self.request.organization
        form.instance.created_by = self.request.user
        form.instance.updated_by = self.request.user
        return super().form_valid(form)
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['organization'] = self.request.organization
        return kwargs


class RiskMatrixConfigUpdateView(OrganizationPermissionMixin, LoginRequiredMixin, UpdateView):
    model = RiskMatrixConfig
    form_class = RiskMatrixConfigForm
    template_name = 'risk/riskmatrixconfig_form.html'
    success_url = reverse_lazy('risk:riskmatrixconfig_list')
    def form_valid(self, form):
        form.instance.organization = self.request.organization
        form.instance.updated_by = self.request.user
        return super().form_valid(form)
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['organization'] = self.request.organization
        return kwargs


class RiskMatrixConfigDetailView(OrganizationPermissionMixin, LoginRequiredMixin, DetailView):
    model = RiskMatrixConfig
    template_name = 'risk/riskmatrixconfig_detail.html'
    context_object_name = 'matrix'
    def get_queryset(self):
        return super().get_queryset().filter(organization=self.request.organization)


class RiskMatrixConfigDeleteView(OrganizationPermissionMixin, LoginRequiredMixin, DeleteView):
    model = RiskMatrixConfig
    template_name = 'risk/riskmatrixconfig_confirm_delete.html'
    success_url = reverse_lazy('risk:riskmatrixconfig_list')
    def get_queryset(self):
        return super().get_queryset().filter(organization=self.request.organization)


# --- Risk Views ---
class RiskCreateView(OrganizationPermissionMixin, LoginRequiredMixin, CreateView):
    model = Risk
    form_class = RiskForm
    template_name = 'risk/risk_form.html'
    success_url = reverse_lazy('risk:risk_list')
    allow_risk_champion_access = True
    allow_risk_champion_write = True
    def form_valid(self, form):
        form.instance.organization = self.request.organization
        form.instance.created_by = self.request.user
        form.instance.updated_by = self.request.user
        return super().form_valid(form)
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['organization'] = self.request.organization
        return kwargs


class RiskUpdateView(OrganizationPermissionMixin, LoginRequiredMixin, UpdateView):
    model = Risk
    form_class = RiskForm
    template_name = 'risk/risk_form.html'
    success_url = reverse_lazy('risk:risk_list')
    allow_risk_champion_access = True
    allow_risk_champion_write = True
    def form_valid(self, form):
        form.instance.organization = self.request.organization
        form.instance.updated_by = self.request.user
        return super().form_valid(form)
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['organization'] = self.request.organization
        return kwargs


class RiskDeleteView(OrganizationPermissionMixin, LoginRequiredMixin, DeleteView):
    model = Risk
    template_name = 'risk/risk_confirm_delete.html'
    success_url = reverse_lazy('risk:risk_list')
    allow_risk_champion_access = True
    allow_risk_champion_write = True
    def get_queryset(self):
        return super().get_queryset().filter(organization=self.request.organization)


# --- Control Views ---
class ControlListView(OrganizationPermissionMixin, LoginRequiredMixin, ListView):
    model = Control
    template_name = 'risk/control_list.html'
    context_object_name = 'controls'
    paginate_by = 20
    allow_risk_champion_access = True
    def get_queryset(self):
        qs = super().get_queryset()
        qs = qs.filter(organization=self.request.organization)
        owner = self.request.GET.get('owner')
        if owner:
            qs = qs.filter(control_owner__icontains=owner)
        effectiveness = self.request.GET.get('effectiveness')
        if effectiveness:
            qs = qs.filter(effectiveness_rating__iexact=effectiveness)
        status = self.request.GET.get('status')
        if status:
            qs = qs.filter(status__iexact=status)
        return qs


class ControlCreateView(OrganizationPermissionMixin, LoginRequiredMixin, CreateView):
    model = Control
    form_class = ControlForm
    template_name = 'risk/control_form.html'
    success_url = reverse_lazy('risk:control_list')
    allow_risk_champion_access = True
    allow_risk_champion_write = True
    def form_valid(self, form):
        form.instance.organization = self.request.organization
        return super().form_valid(form)
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['organization'] = self.request.organization
        return kwargs


class ControlUpdateView(OrganizationPermissionMixin, LoginRequiredMixin, UpdateView):
    model = Control
    form_class = ControlForm
    template_name = 'risk/control_form.html'
    success_url = reverse_lazy('risk:control_list')
    allow_risk_champion_access = True
    allow_risk_champion_write = True
    def form_valid(self, form):
        form.instance.organization = self.request.organization
        form.instance.updated_by = self.request.user
        if not form.instance.pk:
            form.instance.created_by = self.request.user
        return super().form_valid(form)
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['organization'] = self.request.organization
        return kwargs


class ControlDetailView(OrganizationPermissionMixin, LoginRequiredMixin, DetailView):
    model = Control
    template_name = 'risk/control_detail.html'
    context_object_name = 'control'
    allow_risk_champion_access = True
    def get_queryset(self):
        qs = super().get_queryset()
        return qs.filter(organization=self.request.organization)


class ControlDeleteView(OrganizationPermissionMixin, LoginRequiredMixin, DeleteView):
    model = Control
    template_name = 'risk/control_confirm_delete.html'
    success_url = reverse_lazy('risk:control_list')
    allow_risk_champion_access = True
    allow_risk_champion_write = True
    def get_queryset(self):
        return super().get_queryset().filter(organization=self.request.organization)


# --- KRI Views ---
class KRIListView(OrganizationPermissionMixin, LoginRequiredMixin, ListView):
    model = KRI
    template_name = 'risk/kri_list.html'
    context_object_name = 'kris'
    paginate_by = 20
    allow_risk_champion_access = True
    def get_queryset(self):
        qs = super().get_queryset()
        return qs.filter(risk__organization=self.request.organization)
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['kris'] = self.get_queryset()
        return context


class KRICreateView(OrganizationPermissionMixin, LoginRequiredMixin, CreateView):
    model = KRI
    form_class = KRIForm
    template_name = 'risk/kri_form.html'
    success_url = reverse_lazy('risk:kri_list')
    allow_risk_champion_access = True
    allow_risk_champion_write = True
    def form_valid(self, form):
        if form.instance.risk.organization != self.request.organization:
            raise PermissionDenied("Risk does not belong to this organization.")
        return super().form_valid(form)
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['organization'] = self.request.organization
        return kwargs


class KRIUpdateView(OrganizationPermissionMixin, LoginRequiredMixin, UpdateView):
    model = KRI
    form_class = KRIForm
    template_name = 'risk/kri_form.html'
    success_url = reverse_lazy('risk:kri_list')
    allow_risk_champion_access = True
    allow_risk_champion_write = True
    def form_valid(self, form):
        if form.instance.risk.organization != self.request.organization:
            raise PermissionDenied("Risk does not belong to this organization.")
        return super().form_valid(form)
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['organization'] = self.request.organization
        return kwargs


class KRIDetailView(OrganizationPermissionMixin, LoginRequiredMixin, DetailView):
    model = KRI
    template_name = 'risk/kri_detail.html'
    context_object_name = 'kri'
    allow_risk_champion_access = True
    def get_queryset(self):
        qs = super().get_queryset()
        return qs.filter(risk__organization=self.request.organization)


class KRIDeleteView(OrganizationPermissionMixin, LoginRequiredMixin, DeleteView):
    model = KRI
    template_name = 'risk/kri_confirm_delete.html'
    success_url = reverse_lazy('risk:kri_list')
    allow_risk_champion_access = True
    allow_risk_champion_write = True
    def get_queryset(self):
        return super().get_queryset().filter(risk__organization=self.request.organization)


# --- RiskAssessment Views ---
class RiskAssessmentListView(OrganizationPermissionMixin, LoginRequiredMixin, ListView):
    model = RiskAssessment
    template_name = 'risk/riskassessment_list.html'
    context_object_name = 'riskassessments'
    paginate_by = 20
    allow_risk_champion_access = True
    def get_queryset(self):
        qs = super().get_queryset()
        return qs.filter(organization=self.request.organization)
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['riskassessments'] = self.get_queryset()
        return context


class RiskAssessmentCreateView(OrganizationPermissionMixin, LoginRequiredMixin, CreateView):
    model = RiskAssessment
    form_class = RiskAssessmentForm
    template_name = 'risk/riskassessment_form.html'
    success_url = reverse_lazy('risk:riskassessment_list')
    allow_risk_champion_access = True
    allow_risk_champion_write = True
    def form_valid(self, form):
        form.instance.organization = self.request.organization
        form.instance.created_by = self.request.user
        form.instance.updated_by = self.request.user
        return super().form_valid(form)
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['organization'] = self.request.organization
        return kwargs


class RiskAssessmentUpdateView(OrganizationPermissionMixin, LoginRequiredMixin, UpdateView):
    model = RiskAssessment
    form_class = RiskAssessmentForm
    template_name = 'risk/riskassessment_form.html'
    success_url = reverse_lazy('risk:riskassessment_list')
    allow_risk_champion_access = True
    allow_risk_champion_write = True
    def form_valid(self, form):
        form.instance.organization = self.request.organization
        form.instance.updated_by = self.request.user
        return super().form_valid(form)
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['organization'] = self.request.organization
        return kwargs


class RiskAssessmentDetailView(OrganizationPermissionMixin, LoginRequiredMixin, DetailView):
    model = RiskAssessment
    template_name = 'risk/riskassessment_detail.html'
    context_object_name = 'assessment'
    allow_risk_champion_access = True
    def get_queryset(self):
        qs = super().get_queryset()
        return qs.filter(organization=self.request.organization)


class RiskAssessmentDeleteView(OrganizationPermissionMixin, LoginRequiredMixin, DeleteView):
    model = RiskAssessment
    template_name = 'risk/riskassessment_confirm_delete.html'
    success_url = reverse_lazy('risk:riskassessment_list')
    allow_risk_champion_access = True
    allow_risk_champion_write = True
    def get_queryset(self):
        return super().get_queryset().filter(organization=self.request.organization)


def get_active_matrix_config(org):
    return RiskMatrixConfig.objects.filter(organization=org, is_active=True).first()

# Helper: collapse detailed risk levels into Low/Medium/High buckets
def _bucket_risk_levels(risks, matrix):
    """Return tuple (low_count, medium_count, high_count).

    High bucket includes 'high', 'very_high', and 'critical' levels so that
    totals always add up to the overall number of risks when only three bands
    are displayed in reports.
    """
    if risks is None:
        return (0, 0, 0)
    low = medium = high = 0
    # Safeguard when matrix is missing
    active_matrix = matrix
    for r in risks:
        level = r.get_risk_level() if active_matrix else None
        if level == 'low':
            low += 1
        elif level == 'medium':
            medium += 1
        elif level in ('high', 'very_high', 'critical'):
            high += 1
        else:
            # If level could not be determined, infer using default thresholds (5/10/15/20)
            score = r.residual_risk_score
            if score <= 5:
                low += 1
            elif score <= 10:
                medium += 1
            else:
                high += 1
    return (low, medium, high)

class RiskDashboardView(OrganizationPermissionMixin, LoginRequiredMixin, ListView):
    template_name = 'risk/list.html'
    context_object_name = 'dashboard'
    allow_risk_champion_access = True
    def get_queryset(self):
        return []  # Not used
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        org = self.request.organization
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
        selected_register = self.request.GET.get('register')
        riskregisters = RiskRegister.objects.filter(organization=org)
        risks = Risk.objects.filter(organization=org)
        if not filter_all:
            q = Q(date_identified__year__in=year_ints)
            if month_ints:
                q &= Q(date_identified__month__in=month_ints)
            risks = risks.filter(q)
        if selected_register:
            risks = risks.filter(risk_register_id=selected_register)
        controls = Control.objects.filter(organization=org)
        if not filter_all:
            cq = Q()
            # Prefer review dates for period where available
            cq |= Q(last_review_date__year__in=year_ints)
            if month_ints:
                cq &= Q(last_review_date__month__in=month_ints)
            controls = controls.filter(cq)
        kris = KRI.objects.filter(risk__organization=org)
        if not filter_all:
            kq = Q(timestamp__year__in=year_ints)
            if month_ints:
                kq &= Q(timestamp__month__in=month_ints)
            kris = kris.filter(kq)
        assessments = RiskAssessment.objects.filter(risk__organization=org)
        if not filter_all:
            aq = Q(assessment_date__year__in=year_ints)
            if month_ints:
                aq &= Q(assessment_date__month__in=month_ints)
            assessments = assessments.filter(aq)
        matrix = get_active_matrix_config(org)
        
        # COBIT Data
        cobit_domains = COBITDomain.objects.filter(organization=org)
        cobit_processes = COBITProcess.objects.filter(organization=org)
        cobit_capabilities = COBITCapability.objects.filter(organization=org)
        cobit_controls = COBITControl.objects.filter(organization=org)
        cobit_governance = COBITGovernance.objects.filter(organization=org)
        
        # NIST Data
        nist_functions = NISTFunction.objects.filter(organization=org)
        nist_categories = NISTCategory.objects.filter(organization=org)
        nist_subcategories = NISTSubcategory.objects.filter(organization=org)
        nist_implementations = NISTImplementation.objects.filter(organization=org)
        nist_threats = NISTThreat.objects.filter(organization=org)
        nist_incidents = NISTIncident.objects.filter(organization=org)
        
        # Advanced analytics
        from collections import Counter
        # Risks by category
        category_dist = risks.values_list('category', flat=True)
        # Risks by status
        status_dist = risks.values_list('status', flat=True)
        # Risks by owner
        owner_dist = risks.values_list('risk_owner', flat=True)
        # Risks by register
        register_dist = risks.values_list('risk_register__register_name', flat=True)
        # KRI status breakdown
        kri_status_dist = [kri.get_status() for kri in kris]
        # Control effectiveness
        control_effectiveness_dist = controls.values_list('effectiveness_rating', flat=True)
        
        # COBIT Analytics
        cobit_domain_dist = cobit_domains.values_list('domain_code', flat=True)
        cobit_capability_maturity_dist = cobit_capabilities.values_list('current_maturity', flat=True)
        cobit_control_status_dist = cobit_controls.values_list('implementation_status', flat=True)
        
        # NIST Analytics
        nist_function_dist = nist_functions.values_list('function_code', flat=True)
        nist_category_dist = nist_categories.values_list('category_code', flat=True)
        nist_threat_severity_dist = nist_threats.values_list('severity', flat=True)
        nist_incident_status_dist = nist_incidents.values_list('status', flat=True)
        
        # Always provide valid structures for charting, even if empty
        context['risk_category_dist'] = dict(Counter(category_dist)) or {}
        context['risk_status_dist'] = dict(Counter(status_dist)) or {}
        context['risk_owner_dist'] = dict(Counter(owner_dist)) or {}
        context['risk_register_dist'] = dict(Counter(register_dist)) or {}
        context['kri_status_dist'] = dict(Counter(kri_status_dist)) or {}
        context['control_effectiveness_dist'] = dict(Counter(control_effectiveness_dist)) or {}
        
        # COBIT distributions
        context['cobit_domain_dist'] = dict(Counter(cobit_domain_dist)) or {}
        context['cobit_capability_maturity_dist'] = dict(Counter(cobit_capability_maturity_dist)) or {}
        context['cobit_control_status_dist'] = dict(Counter(cobit_control_status_dist)) or {}
        
        # NIST distributions
        context['nist_function_dist'] = dict(Counter(nist_function_dist)) or {}
        context['nist_category_dist'] = dict(Counter(nist_category_dist)) or {}
        context['nist_threat_severity_dist'] = dict(Counter(nist_threat_severity_dist)) or {}
        context['nist_incident_status_dist'] = dict(Counter(nist_incident_status_dist)) or {}
        
        # Risk trend: always a list
        from django.db.models.functions import TruncMonth
        risk_trend = risks.annotate(month=TruncMonth('date_identified')).values('month').annotate(count=Count('id')).order_by('month')
        context['risk_trend'] = [{'month': r['month'].strftime('%Y-%m') if r['month'] else '', 'count': r['count']} for r in risk_trend] if risk_trend else []
        
        # COBIT trend
        cobit_trend = cobit_controls.annotate(month=TruncMonth('created_at')).values('month').annotate(count=Count('id')).order_by('month')
        context['cobit_trend'] = [{'month': r['month'].strftime('%Y-%m') if r['month'] else '', 'count': r['count']} for r in cobit_trend] if cobit_trend else []
        
        # NIST trend
        nist_trend = nist_incidents.annotate(month=TruncMonth('detected_date')).values('month').annotate(count=Count('id')).order_by('month')
        context['nist_trend'] = [{'month': r['month'].strftime('%Y-%m') if r['month'] else '', 'count': r['count']} for r in nist_trend] if nist_trend else []
        
        # Debug output for troubleshooting
        import json
        context['risk_trend_debug'] = json.dumps(context['risk_trend'], indent=2)

        # Period filter context for template
        context['available_years'] = years
        context['available_months'] = months
        context['selected_years'] = selected_years
        context['selected_months'] = selected_months
        context['filter_all'] = filter_all
        
        # Summary cards
        context['riskregisters'] = riskregisters
        context['selected_register'] = int(selected_register) if selected_register else None
        context['total_risks'] = risks.count()
        context['total_controls'] = controls.count()
        context['total_kris'] = kris.count()
        context['total_assessments'] = assessments.count()
        # Three-band breakdown (High bucket aggregates very_high/critical)
        low_c, med_c, high_c = _bucket_risk_levels(list(risks), matrix)
        context['low_risks'] = low_c
        context['medium_risks'] = med_c
        context['high_risks'] = high_c
        context['high_critical_risks'] = high_c  # maintain existing key semantics
        context['recent_activity_count'] = assessments.filter(assessment_date__gte=timezone.now()-timezone.timedelta(days=7)).count()
        
        # COBIT Summary Cards
        context['total_cobit_domains'] = cobit_domains.count()
        context['total_cobit_processes'] = cobit_processes.count()
        context['total_cobit_capabilities'] = cobit_capabilities.count()
        context['total_cobit_controls'] = cobit_controls.count()
        context['total_cobit_governance'] = cobit_governance.count()
        context['active_cobit_controls'] = cobit_controls.filter(implementation_status='fully_implemented').count()
        context['high_maturity_capabilities'] = cobit_capabilities.filter(current_maturity__in=[4, 5]).count()
        
        # NIST Summary Cards
        context['total_nist_functions'] = nist_functions.count()
        context['total_nist_categories'] = nist_categories.count()
        context['total_nist_subcategories'] = nist_subcategories.count()
        context['total_nist_implementations'] = nist_implementations.count()
        context['total_nist_threats'] = nist_threats.count()
        context['total_nist_incidents'] = nist_incidents.count()
        context['high_severity_threats'] = nist_threats.filter(severity__in=['high', 'critical']).count()
        context['open_incidents'] = nist_incidents.filter(status='detected').count()
        
        # Top risks
        context['top_risks'] = risks.order_by('-residual_risk_score')[:5]
        
        # Top COBIT controls by effectiveness
        context['top_cobit_controls'] = cobit_controls.order_by('-effectiveness_rating')[:5]
        
        # Top NIST threats by severity
        context['top_nist_threats'] = nist_threats.order_by('-severity')[:5]
        
        # KRI status
        context['kris_status'] = kris.order_by('-timestamp')[:10]
        
        # Recent COBIT activity
        context['recent_cobit_activity'] = [
            f"Control {c.control_code} updated on {c.updated_at.strftime('%Y-%m-%d')}" 
            for c in cobit_controls.order_by('-updated_at')[:5]
        ]
        
        # Recent NIST activity
        context['recent_nist_activity'] = [
            f"Incident {i.incident_id} reported on {i.detected_date.strftime('%Y-%m-%d')}" 
            for i in nist_incidents.order_by('-detected_date')[:5]
        ]
        
        # Recent activity (simple example)
        context['recent_activity'] = [
            f"Assessment for {a.risk.risk_name} on {a.assessment_date}" for a in assessments.order_by('-assessment_date')[:10]
        ]
        
        context['report_links'] = [
            {
                'label': 'Download Risk Register PDF',
                'url': '/reports/risk/pdf/'
            },
            {
                'label': 'Download COBIT Framework Report',
                'url': '/reports/cobit/pdf/'
            },
            {
                'label': 'Download NIST Framework Report',
                'url': '/reports/nist/pdf/'
            },
        ]
        return context

# --- Objective Views ---
class ObjectiveListView(OrganizationPermissionMixin, LoginRequiredMixin, ListView):
    model = Objective
    template_name = 'risk/objective_list.html'
    context_object_name = 'objectives'
    paginate_by = 20
    def get_queryset(self):
        qs = super().get_queryset()
        qs = qs.filter(organization=self.request.organization)
        q = self.request.GET.get('q')
        status = self.request.GET.get('status')
        if q:
            qs = qs.filter(models.Q(name__icontains=q) | models.Q(code__icontains=q) | models.Q(origin_source__icontains=q))
        if status:
            qs = qs.filter(status=status)
        return qs

class ObjectiveCreateView(OrganizationPermissionMixin, LoginRequiredMixin, CreateView):
    model = Objective
    form_class = ObjectiveForm
    template_name = 'risk/objective_form.html'
    success_url = reverse_lazy('risk:objective_list')
    def form_valid(self, form):
        form.instance.organization = self.request.organization
        form.instance.created_by = self.request.user
        form.instance.updated_by = self.request.user
        return super().form_valid(form)
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['organization'] = self.request.organization
        return kwargs

class ObjectiveUpdateView(OrganizationPermissionMixin, LoginRequiredMixin, UpdateView):
    model = Objective
    form_class = ObjectiveForm
    template_name = 'risk/objective_form.html'
    success_url = reverse_lazy('risk:objective_list')
    def form_valid(self, form):
        form.instance.organization = self.request.organization
        form.instance.updated_by = self.request.user
        return super().form_valid(form)
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['organization'] = self.request.organization
        return kwargs

class ObjectiveDetailView(OrganizationPermissionMixin, LoginRequiredMixin, DetailView):
    model = Objective
    template_name = 'risk/objective_detail.html'
    context_object_name = 'objective'
    def get_queryset(self):
        qs = super().get_queryset()
        return qs.filter(organization=self.request.organization)

class ObjectiveDeleteView(OrganizationPermissionMixin, LoginRequiredMixin, DeleteView):
    model = Objective
    template_name = 'risk/objective_confirm_delete.html'
    success_url = reverse_lazy('risk:objective_list')
    def get_queryset(self):
        return super().get_queryset().filter(organization=self.request.organization)

# ─── REPORTS VIEW ────────────────────────────────────────────────────────────
class RiskReportsView(OrganizationPermissionMixin, LoginRequiredMixin, TemplateView):
    template_name = 'risk/reports.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        organization = self.request.organization
        
        # Get risk registers for dropdowns
        risk_registers = RiskRegister.objects.filter(organization=organization)
        context['risk_registers'] = list(risk_registers.values_list('register_name', flat=True).distinct())
        
        # Get risk categories for filters
        risk_categories = Risk.objects.filter(organization=organization).values_list('category', flat=True).distinct()
        context['risk_categories'] = sorted(list(risk_categories))
        
        # Get risk statuses for filters
        risk_statuses = Risk.objects.filter(organization=organization).values_list('status', flat=True).distinct()
        context['risk_statuses'] = sorted(list(risk_statuses))
        
        # Get risk owners for filters
        risk_owners = Risk.objects.filter(organization=organization).values_list('risk_owner', flat=True).distinct()
        context['risk_owners'] = sorted(list(risk_owners))
        
        # Get KRI statuses for filters (using the get_status method)
        kris = KRI.objects.filter(risk__organization=organization)
        kri_statuses = list(set([kri.get_status() for kri in kris]))
        context['kri_statuses'] = sorted(kri_statuses)
        
        # Get control effectiveness ratings for filters
        control_ratings = Control.objects.filter(organization=organization).values_list('effectiveness_rating', flat=True).distinct()
        context['control_ratings'] = sorted(list(control_ratings))
        
        # COBIT Filters
        cobit_domain_types = COBITDomain.objects.filter(organization=organization).values_list('domain_code', flat=True).distinct()
        context['cobit_domain_types'] = sorted(list(cobit_domain_types))
        
        cobit_capability_maturity_levels = COBITCapability.objects.filter(organization=organization).values_list('current_maturity', flat=True).distinct()
        context['cobit_capability_maturity_levels'] = sorted(list(cobit_capability_maturity_levels))
        
        cobit_control_statuses = COBITControl.objects.filter(organization=organization).values_list('implementation_status', flat=True).distinct()
        context['cobit_control_statuses'] = sorted(list(cobit_control_statuses))
        
        cobit_governance_types = COBITGovernance.objects.filter(organization=organization).values_list('objective_type', flat=True).distinct()
        context['cobit_governance_types'] = sorted(list(cobit_governance_types))
        
        # NIST Filters
        nist_function_types = NISTFunction.objects.filter(organization=organization).values_list('function_code', flat=True).distinct()
        context['nist_function_types'] = sorted(list(nist_function_types))
        
        nist_category_types = NISTCategory.objects.filter(organization=organization).values_list('category_code', flat=True).distinct()
        context['nist_category_types'] = sorted(list(nist_category_types))
        
        nist_subcategory_types = NISTSubcategory.objects.filter(organization=organization).values_list('subcategory_code', flat=True).distinct()
        context['nist_subcategory_types'] = sorted(list(nist_subcategory_types))
        
        nist_implementation_statuses = NISTImplementation.objects.filter(organization=organization).values_list('implementation_status', flat=True).distinct()
        context['nist_implementation_statuses'] = sorted(list(nist_implementation_statuses))
        
        nist_threat_severity_levels = NISTThreat.objects.filter(organization=organization).values_list('severity', flat=True).distinct()
        context['nist_threat_severity_levels'] = sorted(list(nist_threat_severity_levels))
        
        nist_incident_statuses = NISTIncident.objects.filter(organization=organization).values_list('status', flat=True).distinct()
        context['nist_incident_statuses'] = sorted(list(nist_incident_statuses))

        # Objective filters
        objective_statuses = Objective.objects.filter(organization=organization).values_list('status', flat=True).distinct()
        context['objective_statuses'] = sorted(list(objective_statuses))
        
        # Add the specific data needed for the template dropdowns
        context['cobit_domains'] = COBITDomain.objects.filter(organization=organization)
        context['cobit_processes'] = COBITProcess.objects.filter(organization=organization)
        context['nist_functions'] = NISTFunction.objects.filter(organization=organization)
        context['nist_subcategories'] = NISTSubcategory.objects.filter(organization=organization)
        context['objectives'] = Objective.objects.filter(organization=organization)
        
        return context

# --- API Endpoints for Dashboard Widgets ---
@api_view(['GET'])
@permission_classes([IsAuthenticated, IsOrgManagerOrReadOnly])
def api_heatmap_data(request):
    org = request.organization
    selected_register = request.GET.get('register')
    risks = Risk.objects.filter(organization=org)
    if selected_register:
        risks = risks.filter(risk_register_id=selected_register)
    matrix = get_active_matrix_config(org)
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
    }] if any(any(row) for row in z) else []
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
    org = request.organization
    selected_register = request.GET.get('register')
    risks = Risk.objects.filter(organization=org)
    if selected_register:
        risks = risks.filter(risk_register_id=selected_register)
    assessments = RiskAssessment.objects.filter(risk__in=risks)
    timeline = assessments.values('assessment_date').annotate(avg_score=Count('risk_score')).order_by('assessment_date')
    x = [t['assessment_date'] for t in timeline]
    y = [t['avg_score'] for t in timeline]
    data = [{
        'x': x,
        'y': y,
        'type': 'scatter',
        'mode': 'lines+markers',
        'name': 'Avg Risk Score'
    }] if x and y and any(y) else []
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
    org = request.organization
    selected_register = request.GET.get('register')
    risks = Risk.objects.filter(organization=org)
    if selected_register:
        risks = risks.filter(risk_register_id=selected_register)
    controls = Control.objects.filter(organization=org)
    kris = KRI.objects.filter(risk__organization=org)
    assessments = RiskAssessment.objects.filter(risk__organization=org)
    matrix = get_active_matrix_config(org)
    low_c, med_c, high_c = _bucket_risk_levels(list(risks), matrix)
    data = {
        'total_risks': risks.count(),
        'total_controls': controls.count(),
        'total_kris': kris.count(),
        'total_assessments': assessments.count(),
        'high_critical_risks': high_c,
        'low_risks': low_c,
        'medium_risks': med_c,
        'high_risks': high_c,
        'recent_activity_count': assessments.filter(assessment_date__gte=timezone.now()-timezone.timedelta(days=7)).count(),
    }
    return JsonResponse(SummaryCardSerializer(data).data)

@api_view(['GET'])
@permission_classes([IsAuthenticated, IsOrgManagerOrReadOnly])
def api_top_risks(request):
    org = request.organization
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
    org = request.organization
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
    org = request.organization
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
    org = request.organization
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
    org = request.organization
    selected_register = request.GET.get('register')
    risks = Risk.objects.filter(organization=org)
    if selected_register:
        risks = risks.filter(risk_register_id=selected_register)
    data = risks.values('category').annotate(count=Count('id')).order_by('category')
    return JsonResponse({'results': RiskCategoryDistributionSerializer(data, many=True).data})

@api_view(['GET'])
@permission_classes([IsAuthenticated, IsOrgManagerOrReadOnly])
def api_risk_status_distribution(request):
    org = request.organization
    selected_register = request.GET.get('register')
    risks = Risk.objects.filter(organization=org)
    if selected_register:
        risks = risks.filter(risk_register_id=selected_register)
    data = risks.values('status').annotate(count=Count('id')).order_by('status')
    return JsonResponse({'results': RiskStatusDistributionSerializer(data, many=True).data})

@api_view(['GET'])
@permission_classes([IsAuthenticated, IsOrgManagerOrReadOnly])
def api_control_effectiveness(request):
    org = request.organization
    controls = Control.objects.filter(organization=org)
    data = controls.values('effectiveness_rating').annotate(count=Count('id')).order_by('effectiveness_rating')
    # Map to serializer field
    data = [{'effectiveness': d['effectiveness_rating'], 'count': d['count']} for d in data]
    return JsonResponse({'results': ControlEffectivenessSerializer(data, many=True).data})

@api_view(['GET'])
@permission_classes([IsAuthenticated, IsOrgManagerOrReadOnly])
def api_kri_status_counts(request):
    org = request.organization
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
    org = request.organization
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
    org = request.organization
    qs = Risk.objects.filter(organization=org)
    owner = request.GET.get('owner')
    category = request.GET.get('category')
    status = request.GET.get('status')
    register = request.GET.get('register')
    if owner:
        qs = qs.filter(risk_owner__icontains=owner)
    if category:
        qs = qs.filter(category=category)
    if status:
        qs = qs.filter(status=status)
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
    org = request.organization
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
    org = request.organization
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
    org = request.organization
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
    org = request.organization
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
    org = request.organization
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


# --- COBIT Views ---

class COBITDomainListView(OrganizationPermissionMixin, LoginRequiredMixin, ListView):
    model = COBITDomain
    template_name = 'risk/cobitdomain_list.html'
    context_object_name = 'cobitdomains'
    paginate_by = 20
    
    def get_queryset(self):
        qs = super().get_queryset()
        qs = qs.filter(organization=self.request.organization)
        q = self.request.GET.get('q')
        if q:
            qs = qs.filter(Q(domain_name__icontains=q) | Q(domain_code__icontains=q))
        return qs


class COBITDomainCreateView(OrganizationPermissionMixin, LoginRequiredMixin, CreateView):
    model = COBITDomain
    form_class = COBITDomainForm
    template_name = 'risk/cobitdomain_form.html'
    success_url = reverse_lazy('risk:cobitdomain_list')
    
    def form_valid(self, form):
        form.instance.organization = self.request.organization
        form.instance.created_by = self.request.user
        form.instance.updated_by = self.request.user
        return super().form_valid(form)
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['organization'] = self.request.organization
        return kwargs


class COBITDomainUpdateView(OrganizationPermissionMixin, LoginRequiredMixin, UpdateView):
    model = COBITDomain
    form_class = COBITDomainForm
    template_name = 'risk/cobitdomain_form.html'
    success_url = reverse_lazy('risk:cobitdomain_list')
    
    def form_valid(self, form):
        form.instance.organization = self.request.organization
        form.instance.updated_by = self.request.user
        return super().form_valid(form)
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['organization'] = self.request.organization
        return kwargs


class COBITDomainDetailView(OrganizationPermissionMixin, LoginRequiredMixin, DetailView):
    model = COBITDomain
    template_name = 'risk/cobitdomain_detail.html'
    context_object_name = 'cobitdomain'
    
    def get_queryset(self):
        qs = super().get_queryset()
        return qs.filter(organization=self.request.organization)


class COBITDomainDeleteView(OrganizationPermissionMixin, LoginRequiredMixin, DeleteView):
    model = COBITDomain
    template_name = 'risk/cobitdomain_confirm_delete.html'
    success_url = reverse_lazy('risk:cobitdomain_list')
    
    def get_queryset(self):
        return super().get_queryset().filter(organization=self.request.organization)


class COBITProcessListView(OrganizationPermissionMixin, LoginRequiredMixin, ListView):
    model = COBITProcess
    template_name = 'risk/cobitprocess_list.html'
    context_object_name = 'cobitprocesses'
    paginate_by = 20
    
    def get_queryset(self):
        qs = super().get_queryset()
        qs = qs.filter(organization=self.request.organization)
        q = self.request.GET.get('q')
        if q:
            qs = qs.filter(Q(process_name__icontains=q) | Q(process_code__icontains=q))
        domain = self.request.GET.get('domain')
        if domain:
            qs = qs.filter(domain_id=domain)
        return qs


class COBITProcessCreateView(OrganizationPermissionMixin, LoginRequiredMixin, CreateView):
    model = COBITProcess
    form_class = COBITProcessForm
    template_name = 'risk/cobitprocess_form.html'
    success_url = reverse_lazy('risk:cobitprocess_list')
    
    def form_valid(self, form):
        form.instance.organization = self.request.organization
        form.instance.created_by = self.request.user
        form.instance.updated_by = self.request.user
        return super().form_valid(form)
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['organization'] = self.request.organization
        return kwargs


class COBITProcessUpdateView(OrganizationPermissionMixin, LoginRequiredMixin, UpdateView):
    model = COBITProcess
    form_class = COBITProcessForm
    template_name = 'risk/cobitprocess_form.html'
    success_url = reverse_lazy('risk:cobitprocess_list')
    
    def form_valid(self, form):
        form.instance.organization = self.request.organization
        form.instance.updated_by = self.request.user
        return super().form_valid(form)
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['organization'] = self.request.organization
        return kwargs


class COBITProcessDetailView(OrganizationPermissionMixin, LoginRequiredMixin, DetailView):
    model = COBITProcess
    template_name = 'risk/cobitprocess_detail.html'
    context_object_name = 'cobitprocess'
    
    def get_queryset(self):
        qs = super().get_queryset()
        return qs.filter(organization=self.request.organization)


class COBITProcessDeleteView(OrganizationPermissionMixin, LoginRequiredMixin, DeleteView):
    model = COBITProcess
    template_name = 'risk/cobitprocess_confirm_delete.html'
    success_url = reverse_lazy('risk:cobitprocess_list')
    
    def get_queryset(self):
        return super().get_queryset().filter(organization=self.request.organization)


class COBITCapabilityListView(OrganizationPermissionMixin, LoginRequiredMixin, ListView):
    model = COBITCapability
    template_name = 'risk/cobitcapability_list.html'
    context_object_name = 'cobitcapabilities'
    paginate_by = 20
    
    def get_queryset(self):
        qs = super().get_queryset()
        qs = qs.filter(organization=self.request.organization)
        process = self.request.GET.get('process')
        if process:
            qs = qs.filter(process_id=process)
        return qs


class COBITCapabilityCreateView(OrganizationPermissionMixin, LoginRequiredMixin, CreateView):
    model = COBITCapability
    form_class = COBITCapabilityForm
    template_name = 'risk/cobitcapability_form.html'
    success_url = reverse_lazy('risk:cobitcapability_list')
    
    def form_valid(self, form):
        form.instance.organization = self.request.organization
        form.instance.created_by = self.request.user
        form.instance.updated_by = self.request.user
        return super().form_valid(form)
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['organization'] = self.request.organization
        return kwargs


class COBITCapabilityUpdateView(OrganizationPermissionMixin, LoginRequiredMixin, UpdateView):
    model = COBITCapability
    form_class = COBITCapabilityForm
    template_name = 'risk/cobitcapability_form.html'
    success_url = reverse_lazy('risk:cobitcapability_list')
    
    def form_valid(self, form):
        form.instance.organization = self.request.organization
        form.instance.updated_by = self.request.user
        return super().form_valid(form)
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['organization'] = self.request.organization
        return kwargs


class COBITCapabilityDetailView(OrganizationPermissionMixin, LoginRequiredMixin, DetailView):
    model = COBITCapability
    template_name = 'risk/cobitcapability_detail.html'
    context_object_name = 'cobitcapability'
    
    def get_queryset(self):
        qs = super().get_queryset()
        return qs.filter(organization=self.request.organization)


class COBITCapabilityDeleteView(OrganizationPermissionMixin, LoginRequiredMixin, DeleteView):
    model = COBITCapability
    template_name = 'risk/cobitcapability_confirm_delete.html'
    success_url = reverse_lazy('risk:cobitcapability_list')
    
    def get_queryset(self):
        return super().get_queryset().filter(organization=self.request.organization)


class COBITControlListView(OrganizationPermissionMixin, LoginRequiredMixin, ListView):
    model = COBITControl
    template_name = 'risk/cobitcontrol_list.html'
    context_object_name = 'cobitcontrols'
    paginate_by = 20
    
    def get_queryset(self):
        qs = super().get_queryset()
        qs = qs.filter(organization=self.request.organization)
        q = self.request.GET.get('q')
        if q:
            qs = qs.filter(Q(control_name__icontains=q) | Q(control_code__icontains=q))
        process = self.request.GET.get('process')
        if process:
            qs = qs.filter(process_id=process)
        control_type = self.request.GET.get('control_type')
        if control_type:
            qs = qs.filter(control_type=control_type)
        return qs


class COBITControlCreateView(OrganizationPermissionMixin, LoginRequiredMixin, CreateView):
    model = COBITControl
    form_class = COBITControlForm
    template_name = 'risk/cobitcontrol_form.html'
    success_url = reverse_lazy('risk:cobitcontrol_list')
    
    def form_valid(self, form):
        form.instance.organization = self.request.organization
        form.instance.created_by = self.request.user
        form.instance.updated_by = self.request.user
        return super().form_valid(form)
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['organization'] = self.request.organization
        return kwargs


class COBITControlUpdateView(OrganizationPermissionMixin, LoginRequiredMixin, UpdateView):
    model = COBITControl
    form_class = COBITControlForm
    template_name = 'risk/cobitcontrol_form.html'
    success_url = reverse_lazy('risk:cobitcontrol_list')
    
    def form_valid(self, form):
        form.instance.organization = self.request.organization
        form.instance.updated_by = self.request.user
        return super().form_valid(form)
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['organization'] = self.request.organization
        return kwargs


class COBITControlDetailView(OrganizationPermissionMixin, LoginRequiredMixin, DetailView):
    model = COBITControl
    template_name = 'risk/cobitcontrol_detail.html'
    context_object_name = 'cobitcontrol'
    
    def get_queryset(self):
        qs = super().get_queryset()
        return qs.filter(organization=self.request.organization)


class COBITControlDeleteView(OrganizationPermissionMixin, LoginRequiredMixin, DeleteView):
    model = COBITControl
    template_name = 'risk/cobitcontrol_confirm_delete.html'
    success_url = reverse_lazy('risk:cobitcontrol_list')
    
    def get_queryset(self):
        return super().get_queryset().filter(organization=self.request.organization)


class COBITGovernanceListView(OrganizationPermissionMixin, LoginRequiredMixin, ListView):
    model = COBITGovernance
    template_name = 'risk/cobitgovernance_list.html'
    context_object_name = 'cobitgovernances'
    paginate_by = 20
    
    def get_queryset(self):
        qs = super().get_queryset()
        qs = qs.filter(organization=self.request.organization)
        q = self.request.GET.get('q')
        if q:
            qs = qs.filter(Q(objective_name__icontains=q) | Q(objective_code__icontains=q))
        objective_type = self.request.GET.get('objective_type')
        if objective_type:
            qs = qs.filter(objective_type=objective_type)
        return qs


class COBITGovernanceCreateView(OrganizationPermissionMixin, LoginRequiredMixin, CreateView):
    model = COBITGovernance
    form_class = COBITGovernanceForm
    template_name = 'risk/cobitgovernance_form.html'
    success_url = reverse_lazy('risk:cobitgovernance_list')
    
    def form_valid(self, form):
        form.instance.organization = self.request.organization
        form.instance.created_by = self.request.user
        form.instance.updated_by = self.request.user
        return super().form_valid(form)
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['organization'] = self.request.organization
        return kwargs


class COBITGovernanceUpdateView(OrganizationPermissionMixin, LoginRequiredMixin, UpdateView):
    model = COBITGovernance
    form_class = COBITGovernanceForm
    template_name = 'risk/cobitgovernance_form.html'
    success_url = reverse_lazy('risk:cobitgovernance_list')
    
    def form_valid(self, form):
        form.instance.organization = self.request.organization
        form.instance.updated_by = self.request.user
        return super().form_valid(form)
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['organization'] = self.request.organization
        return kwargs


class COBITGovernanceDetailView(OrganizationPermissionMixin, LoginRequiredMixin, DetailView):
    model = COBITGovernance
    template_name = 'risk/cobitgovernance_detail.html'
    context_object_name = 'cobitgovernance'
    
    def get_queryset(self):
        qs = super().get_queryset()
        return qs.filter(organization=self.request.organization)


class COBITGovernanceDeleteView(OrganizationPermissionMixin, LoginRequiredMixin, DeleteView):
    model = COBITGovernance
    template_name = 'risk/cobitgovernance_confirm_delete.html'
    success_url = reverse_lazy('risk:cobitgovernance_list')
    
    def get_queryset(self):
        return super().get_queryset().filter(organization=self.request.organization)


# --- NIST Views ---

class NISTFunctionListView(OrganizationPermissionMixin, LoginRequiredMixin, ListView):
    model = NISTFunction
    template_name = 'risk/nistfunction_list.html'
    context_object_name = 'nistfunctions'
    paginate_by = 20
    
    def get_queryset(self):
        qs = super().get_queryset()
        qs = qs.filter(organization=self.request.organization)
        q = self.request.GET.get('q')
        if q:
            qs = qs.filter(Q(function_name__icontains=q) | Q(function_code__icontains=q))
        return qs


class NISTFunctionCreateView(OrganizationPermissionMixin, LoginRequiredMixin, CreateView):
    model = NISTFunction
    form_class = NISTFunctionForm
    template_name = 'risk/nistfunction_form.html'
    success_url = reverse_lazy('risk:nistfunction_list')
    
    def form_valid(self, form):
        form.instance.organization = self.request.organization
        form.instance.created_by = self.request.user
        form.instance.updated_by = self.request.user
        return super().form_valid(form)
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['organization'] = self.request.organization
        return kwargs


class NISTFunctionUpdateView(OrganizationPermissionMixin, LoginRequiredMixin, UpdateView):
    model = NISTFunction
    form_class = NISTFunctionForm
    template_name = 'risk/nistfunction_form.html'
    success_url = reverse_lazy('risk:nistfunction_list')
    
    def form_valid(self, form):
        form.instance.organization = self.request.organization
        form.instance.updated_by = self.request.user
        return super().form_valid(form)
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['organization'] = self.request.organization
        return kwargs


class NISTFunctionDetailView(OrganizationPermissionMixin, LoginRequiredMixin, DetailView):
    model = NISTFunction
    template_name = 'risk/nistfunction_detail.html'
    context_object_name = 'nistfunction'
    
    def get_queryset(self):
        qs = super().get_queryset()
        return qs.filter(organization=self.request.organization)


class NISTFunctionDeleteView(OrganizationPermissionMixin, LoginRequiredMixin, DeleteView):
    model = NISTFunction
    template_name = 'risk/nistfunction_confirm_delete.html'
    success_url = reverse_lazy('risk:nistfunction_list')
    
    def get_queryset(self):
        return super().get_queryset().filter(organization=self.request.organization)


class NISTCategoryListView(OrganizationPermissionMixin, LoginRequiredMixin, ListView):
    model = NISTCategory
    template_name = 'risk/nistcategory_list.html'
    context_object_name = 'nistcategories'
    paginate_by = 20
    
    def get_queryset(self):
        qs = super().get_queryset()
        qs = qs.filter(organization=self.request.organization)
        q = self.request.GET.get('q')
        if q:
            qs = qs.filter(Q(category_name__icontains=q) | Q(category_code__icontains=q))
        function = self.request.GET.get('function')
        if function:
            qs = qs.filter(function_id=function)
        return qs


class NISTCategoryCreateView(OrganizationPermissionMixin, LoginRequiredMixin, CreateView):
    model = NISTCategory
    form_class = NISTCategoryForm
    template_name = 'risk/nistcategory_form.html'
    success_url = reverse_lazy('risk:nistcategory_list')
    
    def form_valid(self, form):
        form.instance.organization = self.request.organization
        form.instance.created_by = self.request.user
        form.instance.updated_by = self.request.user
        return super().form_valid(form)
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['organization'] = self.request.organization
        return kwargs


class NISTCategoryUpdateView(OrganizationPermissionMixin, LoginRequiredMixin, UpdateView):
    model = NISTCategory
    form_class = NISTCategoryForm
    template_name = 'risk/nistcategory_form.html'
    success_url = reverse_lazy('risk:nistcategory_list')
    
    def form_valid(self, form):
        form.instance.organization = self.request.organization
        form.instance.updated_by = self.request.user
        return super().form_valid(form)
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['organization'] = self.request.organization
        return kwargs


class NISTCategoryDetailView(OrganizationPermissionMixin, LoginRequiredMixin, DetailView):
    model = NISTCategory
    template_name = 'risk/nistcategory_detail.html'
    context_object_name = 'nistcategory'
    
    def get_queryset(self):
        qs = super().get_queryset()
        return qs.filter(organization=self.request.organization)


class NISTCategoryDeleteView(OrganizationPermissionMixin, LoginRequiredMixin, DeleteView):
    model = NISTCategory
    template_name = 'risk/nistcategory_confirm_delete.html'
    success_url = reverse_lazy('risk:nistcategory_list')
    
    def get_queryset(self):
        return super().get_queryset().filter(organization=self.request.organization)


class NISTSubcategoryListView(OrganizationPermissionMixin, LoginRequiredMixin, ListView):
    model = NISTSubcategory
    template_name = 'risk/nistsubcategory_list.html'
    context_object_name = 'nistsubcategories'
    paginate_by = 20
    
    def get_queryset(self):
        qs = super().get_queryset()
        qs = qs.filter(organization=self.request.organization)
        q = self.request.GET.get('q')
        if q:
            qs = qs.filter(Q(subcategory_name__icontains=q) | Q(subcategory_code__icontains=q))
        category = self.request.GET.get('category')
        if category:
            qs = qs.filter(category_id=category)
        return qs


class NISTSubcategoryCreateView(OrganizationPermissionMixin, LoginRequiredMixin, CreateView):
    model = NISTSubcategory
    form_class = NISTSubcategoryForm
    template_name = 'risk/nistsubcategory_form.html'
    success_url = reverse_lazy('risk:nistsubcategory_list')
    
    def form_valid(self, form):
        form.instance.organization = self.request.organization
        form.instance.created_by = self.request.user
        form.instance.updated_by = self.request.user
        return super().form_valid(form)
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['organization'] = self.request.organization
        return kwargs


class NISTSubcategoryUpdateView(OrganizationPermissionMixin, LoginRequiredMixin, UpdateView):
    model = NISTSubcategory
    form_class = NISTSubcategoryForm
    template_name = 'risk/nistsubcategory_form.html'
    success_url = reverse_lazy('risk:nistsubcategory_list')
    
    def form_valid(self, form):
        form.instance.organization = self.request.organization
        form.instance.updated_by = self.request.user
        return super().form_valid(form)
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['organization'] = self.request.organization
        return kwargs


class NISTSubcategoryDetailView(OrganizationPermissionMixin, LoginRequiredMixin, DetailView):
    model = NISTSubcategory
    template_name = 'risk/nistsubcategory_detail.html'
    context_object_name = 'nistsubcategory'
    
    def get_queryset(self):
        qs = super().get_queryset()
        return qs.filter(organization=self.request.organization)


class NISTSubcategoryDeleteView(OrganizationPermissionMixin, LoginRequiredMixin, DeleteView):
    model = NISTSubcategory
    template_name = 'risk/nistsubcategory_confirm_delete.html'
    success_url = reverse_lazy('risk:nistsubcategory_list')
    
    def get_queryset(self):
        return super().get_queryset().filter(organization=self.request.organization)


class NISTImplementationListView(OrganizationPermissionMixin, LoginRequiredMixin, ListView):
    model = NISTImplementation
    template_name = 'risk/nistimplementation_list.html'
    context_object_name = 'nistimplementations'
    paginate_by = 20
    
    def get_queryset(self):
        qs = super().get_queryset()
        qs = qs.filter(organization=self.request.organization)
        subcategory = self.request.GET.get('subcategory')
        if subcategory:
            qs = qs.filter(subcategory_id=subcategory)
        implementation_status = self.request.GET.get('implementation_status')
        if implementation_status:
            qs = qs.filter(implementation_status=implementation_status)
        return qs


class NISTImplementationCreateView(OrganizationPermissionMixin, LoginRequiredMixin, CreateView):
    model = NISTImplementation
    form_class = NISTImplementationForm
    template_name = 'risk/nistimplementation_form.html'
    success_url = reverse_lazy('risk:nistimplementation_list')
    
    def form_valid(self, form):
        form.instance.organization = self.request.organization
        form.instance.created_by = self.request.user
        form.instance.updated_by = self.request.user
        return super().form_valid(form)
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['organization'] = self.request.organization
        return kwargs


class NISTImplementationUpdateView(OrganizationPermissionMixin, LoginRequiredMixin, UpdateView):
    model = NISTImplementation
    form_class = NISTImplementationForm
    template_name = 'risk/nistimplementation_form.html'
    success_url = reverse_lazy('risk:nistimplementation_list')
    
    def form_valid(self, form):
        form.instance.organization = self.request.organization
        form.instance.updated_by = self.request.user
        return super().form_valid(form)
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['organization'] = self.request.organization
        return kwargs


class NISTImplementationDetailView(OrganizationPermissionMixin, LoginRequiredMixin, DetailView):
    model = NISTImplementation
    template_name = 'risk/nistimplementation_detail.html'
    context_object_name = 'nistimplementation'
    
    def get_queryset(self):
        qs = super().get_queryset()
        return qs.filter(organization=self.request.organization)


class NISTImplementationDeleteView(OrganizationPermissionMixin, LoginRequiredMixin, DeleteView):
    model = NISTImplementation
    template_name = 'risk/nistimplementation_confirm_delete.html'
    success_url = reverse_lazy('risk:nistimplementation_list')
    
    def get_queryset(self):
        return super().get_queryset().filter(organization=self.request.organization)


class NISTThreatListView(OrganizationPermissionMixin, LoginRequiredMixin, ListView):
    model = NISTThreat
    template_name = 'risk/nistthreat_list.html'
    context_object_name = 'nistthreats'
    paginate_by = 20
    
    def get_queryset(self):
        qs = super().get_queryset()
        qs = qs.filter(organization=self.request.organization)
        q = self.request.GET.get('q')
        if q:
            qs = qs.filter(threat_name__icontains=q)
        threat_type = self.request.GET.get('threat_type')
        if threat_type:
            qs = qs.filter(threat_type=threat_type)
        severity = self.request.GET.get('severity')
        if severity:
            qs = qs.filter(severity=severity)
        return qs


class NISTThreatCreateView(OrganizationPermissionMixin, LoginRequiredMixin, CreateView):
    model = NISTThreat
    form_class = NISTThreatForm
    template_name = 'risk/nistthreat_form.html'
    success_url = reverse_lazy('risk:nistthreat_list')
    
    def form_valid(self, form):
        form.instance.organization = self.request.organization
        form.instance.created_by = self.request.user
        form.instance.updated_by = self.request.user
        return super().form_valid(form)
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['organization'] = self.request.organization
        return kwargs


class NISTThreatUpdateView(OrganizationPermissionMixin, LoginRequiredMixin, UpdateView):
    model = NISTThreat
    form_class = NISTThreatForm
    template_name = 'risk/nistthreat_form.html'
    success_url = reverse_lazy('risk:nistthreat_list')
    
    def form_valid(self, form):
        form.instance.organization = self.request.organization
        form.instance.updated_by = self.request.user
        return super().form_valid(form)
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['organization'] = self.request.organization
        return kwargs


class NISTThreatDetailView(OrganizationPermissionMixin, LoginRequiredMixin, DetailView):
    model = NISTThreat
    template_name = 'risk/nistthreat_detail.html'
    context_object_name = 'nistthreat'
    
    def get_queryset(self):
        qs = super().get_queryset()
        return qs.filter(organization=self.request.organization)


class NISTThreatDeleteView(OrganizationPermissionMixin, LoginRequiredMixin, DeleteView):
    model = NISTThreat
    template_name = 'risk/nistthreat_confirm_delete.html'
    success_url = reverse_lazy('risk:nistthreat_list')
    
    def get_queryset(self):
        return super().get_queryset().filter(organization=self.request.organization)


class NISTIncidentListView(OrganizationPermissionMixin, LoginRequiredMixin, ListView):
    model = NISTIncident
    template_name = 'risk/nistincident_list.html'
    context_object_name = 'nistincidents'
    paginate_by = 20
    
    def get_queryset(self):
        qs = super().get_queryset()
        qs = qs.filter(organization=self.request.organization)
        q = self.request.GET.get('q')
        if q:
            qs = qs.filter(Q(title__icontains=q) | Q(incident_id__icontains=q))
        incident_type = self.request.GET.get('incident_type')
        if incident_type:
            qs = qs.filter(incident_type=incident_type)
        severity = self.request.GET.get('severity')
        if severity:
            qs = qs.filter(severity=severity)
        status = self.request.GET.get('status')
        if status:
            qs = qs.filter(status=status)
        return qs


class NISTIncidentCreateView(OrganizationPermissionMixin, LoginRequiredMixin, CreateView):
    model = NISTIncident
    form_class = NISTIncidentForm
    template_name = 'risk/nistincident_form.html'
    success_url = reverse_lazy('risk:nistincident_list')
    
    def form_valid(self, form):
        form.instance.organization = self.request.organization
        form.instance.created_by = self.request.user
        form.instance.updated_by = self.request.user
        return super().form_valid(form)
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['organization'] = self.request.organization
        return kwargs


class NISTIncidentUpdateView(OrganizationPermissionMixin, LoginRequiredMixin, UpdateView):
    model = NISTIncident
    form_class = NISTIncidentForm
    template_name = 'risk/nistincident_form.html'
    success_url = reverse_lazy('risk:nistincident_list')
    
    def form_valid(self, form):
        form.instance.organization = self.request.organization
        form.instance.updated_by = self.request.user
        return super().form_valid(form)
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['organization'] = self.request.organization
        return kwargs


class NISTIncidentDetailView(OrganizationPermissionMixin, LoginRequiredMixin, DetailView):
    model = NISTIncident
    template_name = 'risk/nistincident_detail.html'
    context_object_name = 'nistincident'
    
    def get_queryset(self):
        qs = super().get_queryset()
        return qs.filter(organization=self.request.organization)


class NISTIncidentDeleteView(OrganizationPermissionMixin, LoginRequiredMixin, DeleteView):
    model = NISTIncident
    template_name = 'risk/nistincident_confirm_delete.html'
    success_url = reverse_lazy('risk:nistincident_list')
    
    def get_queryset(self):
        return super().get_queryset().filter(organization=self.request.organization)


# --- COBIT API Endpoints for Dashboard Widgets ---
@api_view(['GET'])
@permission_classes([IsAuthenticated, IsOrgManagerOrReadOnly])
def api_cobit_domain_distribution(request):
    org = request.organization
    domains = COBITDomain.objects.filter(organization=org)
    domain_dist = domains.values('domain_code').annotate(count=Count('id')).order_by('domain_code')
    
    data = [{
        'x': [d['domain_code'] for d in domain_dist],
        'y': [d['count'] for d in domain_dist],
        'type': 'bar',
        'name': 'COBIT Domains',
        'marker': {'color': 'rgb(55, 83, 109)'}
    }] if domain_dist else []
    
    layout = {
        'title': 'COBIT Domain Distribution',
        'xaxis': {'title': 'Domain Code'},
        'yaxis': {'title': 'Count'},
        'height': 300
    }
    return JsonResponse({'data': data, 'layout': layout})


@api_view(['GET'])
@permission_classes([IsAuthenticated, IsOrgManagerOrReadOnly])
def api_cobit_control_status(request):
    org = request.organization
    controls = COBITControl.objects.filter(organization=org)
    status_dist = controls.values('implementation_status').annotate(count=Count('id')).order_by('implementation_status')
    
    data = [{
        'labels': [s['implementation_status'] for s in status_dist],
        'values': [s['count'] for s in status_dist],
        'type': 'pie',
        'name': 'Control Status',
        'marker': {'colors': ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728']}
    }] if status_dist else []
    
    layout = {
        'title': 'COBIT Control Status Distribution',
        'height': 300
    }
    return JsonResponse({'data': data, 'layout': layout})


@api_view(['GET'])
@permission_classes([IsAuthenticated, IsOrgManagerOrReadOnly])
def api_cobit_maturity_trend(request):
    org = request.organization
    from django.db.models.functions import TruncMonth
    
    capabilities = COBITCapability.objects.filter(organization=org)
    maturity_trend = capabilities.annotate(
        month=TruncMonth('created_at')
    ).values('month').annotate(
        avg_maturity=Avg('current_maturity')
    ).order_by('month')
    
    data = [{
        'x': [m['month'].strftime('%Y-%m') for m in maturity_trend],
        'y': [float(m['avg_maturity']) for m in maturity_trend],
        'type': 'scatter',
        'mode': 'lines+markers',
        'name': 'Avg Maturity Level',
        'line': {'color': 'rgb(75, 192, 192)'}
    }] if maturity_trend else []
    
    layout = {
        'title': 'COBIT Capability Maturity Trend',
        'xaxis': {'title': 'Month'},
        'yaxis': {'title': 'Average Maturity Level', 'range': [0, 5]},
        'height': 300
    }
    return JsonResponse({'data': data, 'layout': layout})


# --- NIST API Endpoints for Dashboard Widgets ---
@api_view(['GET'])
@permission_classes([IsAuthenticated, IsOrgManagerOrReadOnly])
def api_nist_function_distribution(request):
    org = request.organization
    functions = NISTFunction.objects.filter(organization=org)
    function_dist = functions.values('function_code').annotate(count=Count('id')).order_by('function_code')
    
    data = [{
        'x': [f['function_code'] for f in function_dist],
        'y': [f['count'] for f in function_dist],
        'type': 'bar',
        'name': 'NIST Functions',
        'marker': {'color': 'rgb(158, 202, 225)'}
    }] if function_dist else []
    
    layout = {
        'title': 'NIST Function Distribution',
        'xaxis': {'title': 'Function Code'},
        'yaxis': {'title': 'Count'},
        'height': 300
    }
    return JsonResponse({'data': data, 'layout': layout})


@api_view(['GET'])
@permission_classes([IsAuthenticated, IsOrgManagerOrReadOnly])
def api_nist_threat_severity(request):
    org = request.organization
    threats = NISTThreat.objects.filter(organization=org)
    severity_dist = threats.values('severity').annotate(count=Count('id')).order_by('severity')
    
    data = [{
        'labels': [s['severity'] for s in severity_dist],
        'values': [s['count'] for s in severity_dist],
        'type': 'pie',
        'name': 'Threat Severity',
        'marker': {'colors': ['#ff9999', '#66b3ff', '#99ff99', '#ffcc99', '#ff99cc']}
    }] if severity_dist else []
    
    layout = {
        'title': 'NIST Threat Severity Distribution',
        'height': 300
    }
    return JsonResponse({'data': data, 'layout': layout})


@api_view(['GET'])
@permission_classes([IsAuthenticated, IsOrgManagerOrReadOnly])
def api_nist_incident_timeline(request):
    org = request.organization
    from django.db.models.functions import TruncMonth
    
    incidents = NISTIncident.objects.filter(organization=org)
    incident_trend = incidents.annotate(
        month=TruncMonth('incident_date')
    ).values('month').annotate(
        count=Count('id')
    ).order_by('month')
    
    data = [{
        'x': [i['month'].strftime('%Y-%m') for i in incident_trend],
        'y': [i['count'] for i in incident_trend],
        'type': 'scatter',
        'mode': 'lines+markers',
        'name': 'Incident Count',
        'line': {'color': 'rgb(255, 99, 132)'}
    }] if incident_trend else []
    
    layout = {
        'title': 'NIST Incident Timeline',
        'xaxis': {'title': 'Month'},
        'yaxis': {'title': 'Incident Count'},
        'height': 300
    }
    return JsonResponse({'data': data, 'layout': layout})


@api_view(['GET'])
@permission_classes([IsAuthenticated, IsOrgManagerOrReadOnly])
def api_cobit_nist_summary(request):
    org = request.organization
    
    # COBIT Summary
    cobit_domains = COBITDomain.objects.filter(organization=org).count()
    cobit_processes = COBITProcess.objects.filter(organization=org).count()
    cobit_controls = COBITControl.objects.filter(organization=org).count()
    active_cobit_controls = COBITControl.objects.filter(organization=org, implementation_status='fully_implemented').count()
    
    # NIST Summary
    nist_functions = NISTFunction.objects.filter(organization=org).count()
    nist_categories = NISTCategory.objects.filter(organization=org).count()
    nist_threats = NISTThreat.objects.filter(organization=org).count()
    nist_incidents = NISTIncident.objects.filter(organization=org).count()
    
    data = {
        'cobit': {
            'domains': cobit_domains,
            'processes': cobit_processes,
            'controls': cobit_controls,
            'active_controls': active_cobit_controls,
            'control_effectiveness': round((active_cobit_controls / cobit_controls * 100) if cobit_controls > 0 else 0, 1)
        },
        'nist': {
            'functions': nist_functions,
            'categories': nist_categories,
            'threats': nist_threats,
            'incidents': nist_incidents,
            'threat_coverage': round((nist_categories / nist_functions * 100) if nist_functions > 0 else 0, 1)
        }
    }
    
    return JsonResponse(data)
