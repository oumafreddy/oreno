# apps/audit/views.py

# Utility functions to avoid AttributeError with htmx
def is_htmx_request(request):
    """Safely check if a request is an HTMX request without AttributeError"""
    return request.headers and request.headers.get('HX-Request') == 'true'

# Utility function to safely retrieve issue_pk from various sources
def safe_get_issue_pk(view_instance, raise_error=False):
    """Safely retrieve issue_pk from various sources including URL params, GET/POST data, or view object.
    
    Args:
        view_instance: The view instance (needs to have request and kwargs)
        raise_error: Whether to raise ValueError if issue_pk not found (default: False)
        
    Returns:
        The issue_pk value or None if not found and raise_error is False
    """
    # Try from URL parameters or request data
    issue_pk = view_instance.kwargs.get("issue_pk") or \
               view_instance.request.GET.get("issue_pk") or \
               view_instance.request.POST.get("issue_pk")
    
    # If not found, try to get from the view object
    if not issue_pk and hasattr(view_instance, 'object') and view_instance.object:
        if hasattr(view_instance.object, 'issue_id') and view_instance.object.issue_id:
            return view_instance.object.issue_id
    
    # If still not found, try to get the object from the database
    if not issue_pk and hasattr(view_instance, 'get_object') and hasattr(view_instance, 'kwargs'):
        try:
            if hasattr(view_instance.kwargs, 'pk') or 'pk' in view_instance.kwargs:
                obj = view_instance.get_object()
                if hasattr(obj, 'issue_id') and obj.issue_id:
                    return obj.issue_id
        except Exception:
            # Silently handle any errors during object retrieval
            pass
    
    # If we need to raise an error and we don't have an issue_pk
    if not issue_pk and raise_error:
        raise ValueError("issue_pk is required")
        
    return issue_pk

# Add htmx attribute to request objects to ensure backward compatibility
class RequestWrapper:
    def __init__(self, get_response):
        self.get_response = get_response
        
    def __call__(self, request):
        # Add htmx attribute if it doesn't exist
        if not hasattr(request, 'htmx'):
            request.htmx = is_htmx_request(request)
        return self.get_response(request)

# Monkey patch the request object to ensure htmx attribute
import types
from django.http.request import HttpRequest
def _htmx_property(self):
    return is_htmx_request(self)
HttpRequest.htmx = property(_htmx_property)


from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.shortcuts import get_object_or_404, render, redirect
from django.urls import reverse_lazy
from django.conf import settings
from django.views.generic import (
    ListView, DetailView, CreateView, UpdateView, DeleteView, TemplateView, View
)
from django.contrib.messages.views import SuccessMessageMixin
from django.http import JsonResponse
from django.template.loader import render_to_string
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.core.exceptions import PermissionDenied
from django.db import transaction, DatabaseError, NotSupportedError
from django.db.models import Q, F, Case, When
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.views.decorators.http import require_http_methods as require_HTTP_methods
import logging

logger = logging.getLogger(__name__)
from django.utils.translation import gettext_lazy as _
from django.views.generic import (
    ListView, DetailView, CreateView, UpdateView, DeleteView,
    TemplateView
)
from django_fsm import can_proceed

from core.mixins import OrganizationMixin, OrganizationPermissionMixin
from core.decorators import skip_org_check
from organizations.models import Organization

from .models import AuditWorkplan, Engagement, Issue, Approval, Notification, IssueWorkingPaper, Note, FollowUpAction, IssueRetest, Objective, Procedure, ProcedureResult
from .forms import (
    AuditWorkplanForm, EngagementForm, IssueForm,
    ApprovalForm, WorkplanFilterForm, EngagementFilterForm, IssueFilterForm,
    ProcedureForm, ProcedureResultForm, FollowUpActionForm, IssueRetestForm, NoteForm,
    IssueWorkingPaperForm
)

from rest_framework import generics, permissions, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from .serializers import (
    AuditWorkplanSerializer, EngagementSerializer, IssueSerializer,
    ApprovalSerializer, NoteSerializer, NotificationSerializer
)

from core.permissions import IsTenantMember
from django.contrib.contenttypes.models import ContentType
from users.permissions import IsOrgAdmin, IsOrgManagerOrReadOnly, HasOrgAdminAccess
from core.mixins.organization import OrganizationScopedQuerysetMixin

import csv
from django.http import HttpResponse
import openpyxl
from openpyxl.utils import get_column_letter
from django.utils.encoding import smart_str

from .models.objective import Objective
from .forms import ObjectiveForm

from .models.procedure import Procedure
from .models.procedureresult import ProcedureResult
from .models.followupaction import FollowUpAction
from .models.issueretest import IssueRetest
from .models.note import Note
from .models.recommendation import Recommendation
from .forms import RecommendationForm

from django.http import JsonResponse
from django.template.loader import render_to_string
from django.db.models import Count
from django.utils import timezone
from django.views.decorators.http import require_GET

from .models.issue_working_paper import IssueWorkingPaper
from .forms import IssueWorkingPaperForm
from .serializers import IssueWorkingPaperSerializer

# ─── MIXINS ──────────────────────────────────────────────────────────────────
class AuditPermissionMixin(OrganizationPermissionMixin):
    """Verify that current user has audit permissions for the organization"""
    
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
            
        # Get organization from the view's object or kwargs
        organization = None
        if hasattr(self, 'object'):
            organization = self.object.organization
        elif 'organization_pk' in kwargs:
            organization = get_object_or_404(Organization, pk=kwargs['organization_pk'])
        
        if organization and not request.user.has_audit_access(organization):
            raise PermissionDenied(_("You don't have permission to access audit data for this organization"))
        
        return super().dispatch(request, *args, **kwargs)

# ─── WORKPLAN VIEWS ──────────────────────────────────────────────────────────
class WorkplanListView(AuditPermissionMixin, ListView):
    model = AuditWorkplan
    template_name = 'audit/workplan_list.html'
    context_object_name = 'workplans'
    paginate_by = 20
    
    def get_queryset(self):
        queryset = super().get_queryset()
        organization = self.request.organization
        queryset = queryset.filter(organization=organization).select_related(
            'created_by', 'updated_by'
        ).prefetch_related('engagements')
        form = WorkplanFilterForm(self.request.GET)
        if form.is_valid():
            q = form.cleaned_data.get('q')
            if q:
                queryset = queryset.filter(Q(name__icontains=q) | Q(code__icontains=q))
            status = form.cleaned_data.get('status')
            if status:
                queryset = queryset.filter(state=status)
            fiscal_year = form.cleaned_data.get('fiscal_year')
            if fiscal_year:
                queryset = queryset.filter(fiscal_year=fiscal_year)
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['filter_form'] = WorkplanFilterForm(self.request.GET)
        return context

class WorkplanDetailView(AuditPermissionMixin, DetailView):
    model = AuditWorkplan
    template_name = 'audit/workplan_detail.html'
    context_object_name = 'workplan'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        workplan = self.object
        
        # Add related data efficiently
        context.update({
            'engagements': workplan.engagements.all().select_related(
                'assigned_to', 'assigned_by'
            ),
            'approvals': workplan.approvals.all().select_related(
                'requester', 'approver'
            ),
            'can_submit': can_proceed(workplan.submit_for_approval),
            'can_approve': can_proceed(workplan.approve),
            'can_reject': can_proceed(workplan.reject),
        })
        return context

class WorkplanCreateView(AuditPermissionMixin, SuccessMessageMixin, CreateView):
    model = AuditWorkplan
    form_class = AuditWorkplanForm
    template_name = 'audit/workplan_form.html'
    success_message = _("Workplan %(name)s was created successfully")
    
    def form_valid(self, form):
        form.instance.organization = self.request.organization
        form.instance.created_by = self.request.user
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse_lazy('audit:workplan-detail', kwargs={'pk': self.object.pk})

class WorkplanUpdateView(AuditPermissionMixin, SuccessMessageMixin, UpdateView):
    model = AuditWorkplan
    form_class = AuditWorkplanForm
    template_name = 'audit/workplan_form.html'
    success_message = _("Workplan %(name)s was updated successfully")
    
    def get_success_url(self):
        return reverse_lazy('audit:workplan-detail', kwargs={'pk': self.object.pk})

# ─── ENGAGEMENT VIEWS ────────────────────────────────────────────────────────
class EngagementListView(AuditPermissionMixin, ListView):
    model = Engagement
    template_name = 'audit/engagement_list.html'
    context_object_name = 'engagements'
    paginate_by = 20
    
    def get_queryset(self):
        queryset = super().get_queryset()
        organization = self.request.organization
        queryset = queryset.filter(organization=organization).select_related(
            'audit_workplan', 'assigned_to', 'assigned_by'
        )
        form = EngagementFilterForm(self.request.GET)
        if form.is_valid():
            q = form.cleaned_data.get('q')
            if q:
                queryset = queryset.filter(Q(title__icontains=q) | Q(code__icontains=q))
            status = form.cleaned_data.get('status')
            if status:
                queryset = queryset.filter(project_status=status)
            owner = form.cleaned_data.get('owner')
            if owner:
                queryset = queryset.filter(assigned_to__email__icontains=owner)
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['filter_form'] = EngagementFilterForm(self.request.GET)
        return context

class EngagementDetailView(AuditPermissionMixin, DetailView):
    model = Engagement
    template_name = 'audit/engagement_detail.html'
    context_object_name = 'engagement'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        engagement = self.object
        context.update({
            'issues': engagement.all_issues.select_related(
                'issue_owner', 'procedure_result'
            ),
            'approvals': engagement.approvals.all().select_related(
                'requester', 'approver'
            ),
            'can_submit': can_proceed(engagement.submit_for_approval),
            'can_approve': can_proceed(engagement.approve),
            'can_reject': can_proceed(engagement.reject),
            'content_type_id': ContentType.objects.get_for_model(type(engagement)).pk,
        })
        return context

class EngagementCreateView(AuditPermissionMixin, SuccessMessageMixin, CreateView):
    model = Engagement
    form_class = EngagementForm
    template_name = 'audit/engagement_form.html'
    success_message = _("Engagement %(title)s was created successfully")
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['organization'] = self.request.organization
        return kwargs
    
    def get_initial(self):
        initial = super().get_initial()
        if self.request.GET.get('workplan'):
            try:
                workplan_id = int(self.request.GET.get('workplan'))
                workplan = get_object_or_404(AuditWorkplan, pk=workplan_id, organization=self.request.organization)
                initial['audit_workplan'] = workplan
            except (ValueError, TypeError):
                pass
        return initial
    
    def get_template_names(self):
        """Return different templates based on request type."""
        if self.request.headers.get('HX-Request'):
            return ['audit/engagement_modal_form.html']
        return [self.template_name]
        
    def get(self, request, *args, **kwargs):
        # Check if this is an HTMX request - if so, we use the modal template via get_template_names()
        return super().get(request, *args, **kwargs)
    
    def form_valid(self, form):
        form.instance.organization = self.request.organization
        form.instance.created_by = self.request.user
        response = super().form_valid(form)
        
        # Handle HTMX or AJAX requests
        is_htmx = self.request.headers.get('HX-Request') == 'true'
        is_ajax = self.request.headers.get('X-Requested-With') == 'XMLHttpRequest'
        
        if is_htmx or is_ajax:
            from django.http import JsonResponse
            
            # Provide JSON response for modal handler
            return JsonResponse({
                'success': True,
                'pk': self.object.pk,
                'redirect': self.get_success_url(),
                'message': self.success_message % form.cleaned_data,
            })
        
        return response
    
    def form_invalid(self, form):
        """Handle form validation errors."""
        is_htmx = self.request.headers.get('HX-Request') == 'true'
        is_ajax = self.request.headers.get('X-Requested-With') == 'XMLHttpRequest'
        
        if is_htmx or is_ajax:
            from django.http import JsonResponse
            from django.template.loader import render_to_string
            
            # Render the form with errors
            html = render_to_string(
                self.get_template_names()[0],
                self.get_context_data(form=form),
                request=self.request
            )
            
            return JsonResponse({
                'success': False,
                'html': html,
            }, status=400)
        
        return super().form_invalid(form)
    
    def get_success_url(self):
        return reverse_lazy('audit:engagement-detail', kwargs={'pk': self.object.pk})

class EngagementUpdateView(AuditPermissionMixin, SuccessMessageMixin, UpdateView):
    model = Engagement
    form_class = EngagementForm
    template_name = 'audit/engagement_form.html'
    success_message = _("Engagement %(title)s was updated successfully")
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['organization'] = self.request.organization
        return kwargs
    
    def get_template_names(self):
        """Return different templates based on request type."""
        if self.request.headers.get('HX-Request'):
            return ['audit/engagement_modal_form.html']
        return [self.template_name]
    
    def form_valid(self, form):
        """Handle successful form submission."""
        form.instance.organization = self.request.organization
        form.instance.last_modified_by = self.request.user
        response = super().form_valid(form)
        
        # Handle HTMX or AJAX requests
        is_htmx = self.request.headers.get('HX-Request') == 'true'
        is_ajax = self.request.headers.get('X-Requested-With') == 'XMLHttpRequest'
        
        if is_htmx or is_ajax:
            from django.http import JsonResponse
            from django.template.loader import render_to_string
            
            # Provide JSON response for modal handler
            return JsonResponse({
                'success': True,
                'pk': self.object.pk,
                'redirect': self.get_success_url(),
                'message': self.success_message % form.cleaned_data,
            })
        
        return response
    
    def form_invalid(self, form):
        """Handle form validation errors."""
        is_htmx = self.request.headers.get('HX-Request') == 'true'
        is_ajax = self.request.headers.get('X-Requested-With') == 'XMLHttpRequest'
        
        if is_htmx or is_ajax:
            from django.http import JsonResponse
            from django.template.loader import render_to_string
            
            # Render the form with errors
            html = render_to_string(
                self.get_template_names()[0],
                self.get_context_data(form=form),
                request=self.request
            )
            
            return JsonResponse({
                'success': False,
                'html': html,
            }, status=400)
        
        return super().form_invalid(form)
    
    def get_success_url(self):
        return reverse_lazy('audit:engagement-detail', kwargs={'pk': self.object.pk})

# ─── ISSUE VIEWS ─────────────────────────────────────────────────────────────
class IssueListView(AuditPermissionMixin, ListView):
    model = Issue
    template_name = 'audit/issue_list.html'
    context_object_name = 'issues'
    paginate_by = 20
    
    def get_queryset(self):
        queryset = super().get_queryset()
        organization = self.request.organization
        queryset = queryset.filter(organization=organization).select_related(
            'issue_owner', 'procedure_result'
        )
        form = IssueFilterForm(self.request.GET)
        if form.is_valid():
            q = form.cleaned_data.get('q')
            if q:
                queryset = queryset.filter(Q(issue_title__icontains=q) | Q(code__icontains=q))
            status = form.cleaned_data.get('status')
            if status:
                queryset = queryset.filter(issue_status=status)
            severity = form.cleaned_data.get('severity')
            if severity:
                queryset = queryset.filter(severity_status=severity)
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['filter_form'] = IssueFilterForm(self.request.GET)
        return context

class IssueDetailView(AuditPermissionMixin, DetailView):
    model = Issue
    template_name = 'audit/issue_detail.html'
    context_object_name = 'issue'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        from django.contrib.contenttypes.models import ContentType
        issue = self.object
        # Robustly get engagement (via procedure_result > procedure > objective > engagement)
        engagement = None
        if issue.procedure_result and hasattr(issue.procedure_result, 'procedure') and issue.procedure_result.procedure and hasattr(issue.procedure_result.procedure, 'objective') and issue.procedure_result.procedure.objective:
            engagement = issue.procedure_result.procedure.objective.engagement
        context['engagement'] = engagement
        # For notes
        content_type = ContentType.objects.get_for_model(issue)
        context['content_type_id'] = content_type.id
        context['object_id'] = issue.pk
        context['issue'] = issue  # For partials
        # Add any other context needed for modals/partials here
        context['working_papers'] = IssueWorkingPaper.objects.filter(issue=issue)
        return context

class IssueCreateView(AuditPermissionMixin, SuccessMessageMixin, CreateView):
    model = Issue
    form_class = IssueForm
    template_name = 'audit/issue_form.html'
    success_message = _("Issue %(issue_title)s was created successfully")
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['organization'] = self.request.organization
        return kwargs
    
    def form_valid(self, form):
        form.instance.organization = self.request.organization
        form.instance.created_by = self.request.user
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse_lazy('audit:issue-detail', kwargs={'pk': self.object.pk})

class IssueUpdateView(AuditPermissionMixin, SuccessMessageMixin, UpdateView):
    model = Issue
    form_class = IssueForm
    template_name = 'audit/issue_form.html'
    success_message = _("Issue %(issue_title)s was updated successfully")
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['organization'] = self.request.organization
        return kwargs
    
    def get_success_url(self):
        return reverse_lazy('audit:issue-detail', kwargs={'pk': self.object.pk})

# ─── APPROVAL VIEWS ──────────────────────────────────────────────────────────
class ApprovalCreateView(AuditPermissionMixin, SuccessMessageMixin, CreateView):
    model = Approval
    form_class = ApprovalForm
    template_name = 'audit/approval_form.html'
    success_message = _("Approval request was created successfully")
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['organization'] = self.request.organization
        kwargs['requester'] = self.request.user
        return kwargs
    
    def form_valid(self, form):
        form.instance.organization = self.request.organization
        form.instance.requester = self.request.user
        return super().form_valid(form)
    
    def get_success_url(self):
        return reverse_lazy('audit:approval_detail', kwargs={'pk': self.object.pk})

class ApprovalDetailView(AuditPermissionMixin, DetailView):
    model = Approval
    template_name = 'audit/approval_detail.html'
    context_object_name = 'approval'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        approval = self.object
        
        # Add related data efficiently
        context.update({
            'content_object': approval.content_object,
            'can_approve': self.request.user.has_perm('audit.can_approve_workplan'),
        })
        return context

# ─── DASHBOARD VIEW ──────────────────────────────────────────────────────────
class AuditDashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'audit/dashboard.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        organization = self.request.organization
        from collections import Counter, defaultdict
        from django.utils import timezone
        from .models.objective import Objective
        from .models.procedure import Procedure
        from .models.procedureresult import ProcedureResult
        from .models.recommendation import Recommendation
        from .models.followupaction import FollowUpAction
        from .models.issueretest import IssueRetest
        from .models.note import Note
        from .models.issue import Issue
        from django.contrib.auth import get_user_model
        User = get_user_model()
        
        # Summary counts
        context['workplan_count'] = AuditWorkplan.objects.filter(organization=organization).count()
        context['engagement_count'] = Engagement.objects.filter(organization=organization).count()
        context['issue_count'] = Issue.objects.filter(organization=organization).count()
        context['approval_count'] = Approval.objects.filter(organization=organization).count()
        # Recent objects (limit 8)
        context['recent_workplans'] = AuditWorkplan.objects.filter(organization=organization).order_by('-creation_date')[:8]
        context['recent_engagements'] = Engagement.objects.filter(organization=organization).order_by('-project_start_date')[:8]
        context['recent_issues'] = Issue.objects.filter(organization=organization).order_by('-date_identified')[:8]
        context['pending_approvals'] = Approval.objects.filter(organization=organization, status='pending').order_by('-created_at')[:8]
        # Org info (if available)
        org = organization
        context['org_name'] = getattr(org, 'name', None)
        context['org_code'] = getattr(org, 'code', None)
        context['org_logo'] = org.logo.url if getattr(org, 'logo', None) else None
        context['org_status'] = 'Active' if getattr(org, 'is_active', True) else 'Inactive'
        # Engagement status distribution
        engagement_status_dist = Engagement.objects.filter(organization=organization).values_list('project_status', flat=True)
        context['engagement_status_dist'] = dict(Counter(engagement_status_dist)) or {}
        # Average engagement duration
        engagements = Engagement.objects.filter(organization=organization)
        durations = [(e.target_end_date - e.project_start_date).days for e in engagements if e.target_end_date and e.project_start_date]
        context['avg_engagement_duration'] = sum(durations) / len(durations) if durations else 0
        # Overdue issues
        today = timezone.now().date()
        overdue_issues = Issue.objects.filter(organization=organization, issue_status__in=['open', 'in_progress'], remediation_deadline_date__lt=today).count()
        context['overdue_issues'] = overdue_issues
        # Issue severity distribution
        issue_severity_dist = Issue.objects.filter(organization=organization).values_list('severity_status', flat=True)
        context['issue_severity_dist'] = dict(Counter(issue_severity_dist)) or {}
        # Workplan completion rates
        workplans = AuditWorkplan.objects.filter(organization=organization)
        completed_workplans = workplans.filter(state='completed').count()
        context['workplan_completion_rate'] = {'Completed': completed_workplans, 'Total': workplans.count()}
        # Approval status breakdown
        approvals = Approval.objects.filter(organization=organization)
        approval_status_dist = approvals.values_list('status', flat=True)
        context['approval_status_dist'] = dict(Counter(approval_status_dist)) or {}
        # Owner workload (engagements assigned)
        owner_workload = engagements.values_list('assigned_to__email', flat=True)
        context['engagement_owner_workload'] = dict(Counter(owner_workload)) or {}
        # Add engagement_names for dashboard dropdowns
        context['engagement_names'] = list(Engagement.objects.filter(organization=organization).values_list('title', flat=True).distinct().order_by('title')) or []
        # Add recent lists and counts for all major audit models
        context['objective_count'] = Objective.objects.filter(organization=organization).count()
        context['recent_objectives'] = Objective.objects.filter(organization=organization).order_by('-id')[:8]
        context['procedure_count'] = Procedure.objects.filter(organization=organization).count()
        context['recent_procedures'] = Procedure.objects.filter(organization=organization).order_by('-id')[:8]
        context['recommendation_count'] = Recommendation.objects.filter(organization=organization).count()
        context['recent_recommendations'] = Recommendation.objects.filter(organization=organization).order_by('-id')[:8]
        context['procedureresult_count'] = ProcedureResult.objects.filter(organization=organization).count()
        context['recent_procedureresults'] = ProcedureResult.objects.filter(organization=organization).order_by('-id')[:8]
        context['followupaction_count'] = FollowUpAction.objects.filter(organization=organization).count()
        context['recent_followupactions'] = FollowUpAction.objects.filter(organization=organization).order_by('-created_at')[:8]
        context['issueretest_count'] = IssueRetest.objects.filter(organization=organization).count()
        context['recent_issueretests'] = IssueRetest.objects.filter(organization=organization).order_by('-retest_date', '-created_at')[:8]
        context['note_count'] = Note.objects.filter(organization=organization).count()
        context['recent_notes'] = Note.objects.filter(organization=organization).order_by('-created_at')[:8]
        # Analytics context for dashboard
        # 1. Issue Trend (last 12 months)
        today = timezone.now().date()
        months = [(today.replace(day=1) - timezone.timedelta(days=30*i)).replace(day=1) for i in range(11, -1, -1)]
        months = sorted(set(months))
        issue_trend = defaultdict(int)
        for m in months:
            next_month = (m.replace(day=28) + timezone.timedelta(days=4)).replace(day=1)
            count = Issue.objects.filter(organization=organization, date_identified__gte=m, date_identified__lt=next_month).count()
            issue_trend[m.strftime('%b %Y')] = count
        context['issue_trend_data'] = issue_trend
        # 2. Completion Rates
        def pct_complete(qs, field='status', complete_value='completed'):
            total = qs.count()
            completed = qs.filter(**{field: complete_value}).count()
            return round(100 * completed / total, 1) if total else 0
        context['completion_rate_data'] = {
            'Objectives': pct_complete(Objective.objects.filter(engagement__organization=organization), 'status', 'completed') if hasattr(Objective, 'status') else None,
            'Procedures': pct_complete(Procedure.objects.filter(objective__engagement__organization=organization), 'status', 'completed') if hasattr(Procedure, 'status') else None,
            'Recommendations': pct_complete(Recommendation.objects.filter(organization=organization), 'status', 'completed') if hasattr(Recommendation, 'status') else None,
            'FollowUps': pct_complete(FollowUpAction.objects.filter(organization=organization), 'status', 'completed'),
        }
        # 3. User Activity (top creators)
        user_activity = User.objects.filter(
            id__in=Issue.objects.filter(organization=organization).values_list('created_by', flat=True)
        ).annotate(
            issues=Count('issue_created', filter=Q(issue_created__organization=organization)),
            objectives=Count('objective_created', filter=Q(objective_created__engagement__organization=organization)),
            procedures=Count('procedure_created', filter=Q(procedure_created__objective__engagement__organization=organization)),
        ).order_by('-issues', '-objectives', '-procedures')[:10]
        context['user_activity_data'] = [
            {'user': u.get_full_name() or u.email, 'issues': u.issues, 'objectives': u.objectives, 'procedures': u.procedures}
            for u in user_activity
        ]
        # 4. Audit Activity Heatmap (activity by week/month)
        heatmap = defaultdict(int)
        for i in range(0, 12):
            month = (today.replace(day=1) - timezone.timedelta(days=30*i)).replace(day=1)
            count = Issue.objects.filter(organization=organization, date_identified__month=month.month, date_identified__year=month.year).count()
            heatmap[month.strftime('%b %Y')] = count
        context['audit_heatmap_data'] = heatmap
        return context

class AuditWorkplanViewSet(viewsets.ModelViewSet):
    """API endpoint for audit workplans."""
    serializer_class = AuditWorkplanSerializer
    permission_classes = [permissions.IsAuthenticated, IsOrgManagerOrReadOnly]

    def get_queryset(self):
        return AuditWorkplan.objects.filter(organization=self.request.organization)

    def perform_create(self, serializer):
        serializer.save(organization=self.request.organization)

class EngagementViewSet(OrganizationScopedQuerysetMixin, viewsets.ModelViewSet):
    """API endpoint for audit engagements."""
    serializer_class = EngagementSerializer
    permission_classes = [permissions.IsAuthenticated, IsOrgManagerOrReadOnly]

    def perform_create(self, serializer):
        serializer.save(organization=self.request.organization)

class IssueViewSet(OrganizationScopedQuerysetMixin, viewsets.ModelViewSet):
    """API endpoint for audit issues."""
    serializer_class = IssueSerializer
    permission_classes = [permissions.IsAuthenticated, IsOrgManagerOrReadOnly]

    def perform_create(self, serializer):
        serializer.save(organization=self.request.organization)

class ApprovalViewSet(OrganizationScopedQuerysetMixin, viewsets.ModelViewSet):
    """API endpoint for audit approvals."""
    serializer_class = ApprovalSerializer
    permission_classes = [permissions.IsAuthenticated, IsOrgAdmin]

    def perform_create(self, serializer):
        serializer.save(
            organization=self.request.organization,
            requester=self.request.user
        )

class WorkplanEngagementViewSet(viewsets.ModelViewSet):
    """API endpoint for workplan engagements."""
    serializer_class = EngagementSerializer
    permission_classes = [permissions.IsAuthenticated, IsOrgManagerOrReadOnly]

    def get_queryset(self):
        workplan_pk = self.kwargs.get('workplan_pk')
        return Engagement.objects.filter(
            organization=self.request.organization,
            audit_workplan_id=workplan_pk
        )

    def perform_create(self, serializer):
        workplan_pk = self.kwargs.get('workplan_pk')
        workplan = AuditWorkplan.objects.get(pk=workplan_pk)
        serializer.save(
            organization=self.request.organization,
            audit_workplan=workplan
        )

class WorkplanApprovalViewSet(viewsets.ModelViewSet):
    """API endpoint for workplan approvals."""
    serializer_class = ApprovalSerializer
    permission_classes = [permissions.IsAuthenticated, IsOrgAdmin]

    def get_queryset(self):
        """Return approvals for the specified workplan."""
        workplan_id = self.kwargs.get('workplan_pk')
        return Approval.objects.filter(
            content_type__model='auditworkplan',
            object_id=workplan_id
        )

    def perform_create(self, serializer):
        """Create a new approval for the workplan."""
        workplan_id = self.kwargs.get('workplan_pk')
        workplan = get_object_or_404(AuditWorkplan, pk=workplan_id)
        serializer.save(
            content_type=ContentType.objects.get_for_model(AuditWorkplan),
            object_id=workplan_id,
            organization=workplan.organization
        )

class EngagementIssueViewSet(viewsets.ModelViewSet):
    """API endpoint for engagement issues."""
    serializer_class = IssueSerializer
    permission_classes = [permissions.IsAuthenticated, IsOrgManagerOrReadOnly]
    
    def get_queryset(self):
        engagement_pk = self.kwargs.get('engagement_pk')
        return Issue.objects.filter(
            engagement_id=engagement_pk
        ).select_related('issue_owner', 'engagement')
    
    def perform_create(self, serializer):
        engagement_pk = self.kwargs.get('engagement_pk')
        engagement = get_object_or_404(Engagement, pk=engagement_pk)
        serializer.save(
            engagement=engagement,
            organization=self.request.organization,
            created_by=self.request.user
        )

class EngagementApprovalViewSet(viewsets.ModelViewSet):
    """API endpoint for engagement approvals."""
    serializer_class = ApprovalSerializer
    permission_classes = [permissions.IsAuthenticated, IsOrgAdmin]
    
    def get_queryset(self):
        engagement_pk = self.kwargs.get('engagement_pk')
        return Approval.objects.filter(
            content_type__model='engagement',
            object_id=engagement_pk
        ).select_related('requester', 'approver')
    
    def perform_create(self, serializer):
        engagement_pk = self.kwargs.get('engagement_pk')
        engagement = get_object_or_404(Engagement, pk=engagement_pk)
        serializer.save(
            content_object=engagement,
            organization=self.request.organization,
            requester=self.request.user
        )

class IssueApprovalViewSet(viewsets.ModelViewSet):
    """API endpoint for issue approvals."""
    serializer_class = ApprovalSerializer
    permission_classes = [permissions.IsAuthenticated, IsOrgAdmin]
    
    def get_queryset(self):
        issue_pk = self.kwargs.get('issue_pk')
        return Approval.objects.filter(
            content_type__model='issue',
            object_id=issue_pk
        ).select_related('requester', 'approver')
    
    def perform_create(self, serializer):
        issue_pk = self.kwargs.get('issue_pk')
        issue = get_object_or_404(Issue, pk=issue_pk)
        serializer.save(
            content_object=issue,
            organization=self.request.organization,
            requester=self.request.user
        )

@login_required
def submit_workplan(request, pk):
    workplan = get_object_or_404(AuditWorkplan, pk=pk)
    if can_proceed(workplan.submit_for_approval):
        workplan.submit_for_approval()
        workplan.save()
        messages.success(request, _("Workplan submitted for approval successfully."))
    else:
        messages.error(request, _("Cannot submit workplan for approval in its current state."))
    return redirect('audit:workplan-detail', pk=pk)

@login_required
def approve_workplan(request, pk):
    workplan = get_object_or_404(AuditWorkplan, pk=pk)
    if can_proceed(workplan.approve):
        workplan.approve()
        workplan.save()
        messages.success(request, _("Workplan approved successfully."))
    else:
        messages.error(request, _("Cannot approve workplan in its current state."))
    return redirect('audit:workplan-detail', pk=pk)

@login_required
def reject_workplan(request, pk):
    workplan = get_object_or_404(AuditWorkplan, pk=pk)
    if can_proceed(workplan.reject):
        workplan.reject()
        workplan.save()
        messages.success(request, _("Workplan rejected."))
    else:
        messages.error(request, _("Cannot reject workplan in its current state."))
    return redirect('audit:workplan-detail', pk=pk)

@login_required
def submit_engagement(request, pk):
    engagement = get_object_or_404(Engagement, pk=pk)
    if can_proceed(engagement.submit_for_approval):
        engagement.submit_for_approval()
        engagement.save()
        messages.success(request, _("Engagement submitted for approval successfully."))
    else:
        messages.error(request, _("Cannot submit engagement for approval in its current state."))
    return redirect('audit:engagement-detail', pk=pk)

@login_required
def approve_engagement(request, pk):
    engagement = get_object_or_404(Engagement, pk=pk)
    if can_proceed(engagement.approve):
        engagement.approve()
        engagement.save()
        messages.success(request, _("Engagement approved successfully."))
    else:
        messages.error(request, _("Cannot approve engagement in its current state."))
    return redirect('audit:engagement-detail', pk=pk)

@login_required
def reject_engagement(request, pk):
    engagement = get_object_or_404(Engagement, pk=pk)
    if can_proceed(engagement.reject):
        engagement.reject()
        engagement.save()
        messages.success(request, _("Engagement rejected."))
    else:
        messages.error(request, _("Cannot reject engagement in its current state."))
    return redirect('audit:engagement-detail', pk=pk)

@login_required
def close_issue(request, pk):
    issue = get_object_or_404(Issue, pk=pk)
    issue.issue_status = 'closed'
    issue.save()
    messages.success(request, _("Issue closed successfully."))
    return redirect('audit:issue-detail', pk=pk)

@login_required
def reopen_issue(request, pk):
    issue = get_object_or_404(Issue, pk=pk)
    issue.issue_status = 'open'
    issue.save()
    messages.success(request, _("Issue reopened successfully."))
    return redirect('audit:issue-detail', pk=pk)

@login_required
def approve_approval(request, pk):
    approval = get_object_or_404(Approval, pk=pk)
    approval.status = 'approved'
    approval.save()
    messages.success(request, _("Approval request approved successfully."))
    return redirect('audit:approval-detail', pk=pk)

@login_required
def reject_approval(request, pk):
    approval = get_object_or_404(Approval, pk=pk)
    approval.status = 'rejected'
    approval.save()
    messages.success(request, _("Approval request rejected."))
    return redirect('audit:approval-detail', pk=pk)

@login_required
def bulk_approve(request):
    if request.method == 'POST':
        ids = request.POST.getlist('selected_items')
        Approval.objects.filter(id__in=ids).update(status='approved')
        messages.success(request, _("Selected items approved successfully."))
    return redirect('audit:approval-list')

@login_required
def bulk_reject(request):
    if request.method == 'POST':
        ids = request.POST.getlist('selected_items')
        Approval.objects.filter(id__in=ids).update(status='rejected')
        messages.success(request, _("Selected items rejected successfully."))
    return redirect('audit:approval-list')

@login_required
def export_data(request):
    # Implement export logic here
    pass

@login_required
def workplan_report(request):
    # Implement workplan report generation here
    pass

@login_required
def engagement_report(request):
    # Implement engagement report generation here
    pass

@login_required
def issue_report(request):
    # Implement issue report generation here
    pass

@login_required
def approval_report(request):
    # Implement approval report generation here
    pass

@login_required
def search(request):
    # Implement search functionality here
    pass

@login_required
def autocomplete(request):
    # Implement autocomplete functionality here
    pass

@login_required
def validate(request):
    # Implement validation functionality here
    pass

def export_to_xlsx(headers, rows, filename):
    wb = openpyxl.Workbook()
    ws = wb.active
    ws.append(headers)
    for row in rows:
        ws.append([smart_str(cell) for cell in row])
    for col_num, _ in enumerate(headers, 1):
        ws.column_dimensions[get_column_letter(col_num)].width = 20
    from io import BytesIO
    output = BytesIO()
    wb.save(output)
    output.seek(0)
    response = HttpResponse(output.read(), content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    return response

@login_required
def export_workplans(request):
    fiscal_year = request.GET.get('fiscal_year')
    name = request.GET.get('name')
    export_format = request.GET.get('format', 'csv')
    qs = AuditWorkplan.objects.filter(organization=request.organization)
    if fiscal_year:
        qs = qs.filter(fiscal_year=fiscal_year)
    if name:
        qs = qs.filter(name__icontains=name)
    headers = ['ID', 'Code', 'Name', 'Fiscal Year', 'State', 'Creation Date']
    rows = [[wp.id, wp.code, wp.name, wp.fiscal_year, wp.state, wp.creation_date] for wp in qs]
    if export_format == 'xlsx':
        return export_to_xlsx(headers, rows, 'workplans.xlsx')
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="workplans.csv"'
    writer = csv.writer(response)
    writer.writerow(headers)
    for row in rows:
        writer.writerow(row)
    return response

@login_required
def export_engagements(request):
    qs = Engagement.objects.filter(organization=request.organization)
    # Apply the same filters as the list view
    q = request.GET.get('q')
    if q:
        qs = qs.filter(Q(title__icontains=q) | Q(code__icontains=q))
    status = request.GET.get('status')
    if status:
        qs = qs.filter(project_status=status)
    owner = request.GET.get('owner')
    if owner:
        qs = qs.filter(assigned_to__email__icontains=owner)
    # Add more filters as needed

    export_format = request.GET.get('format', 'csv')
    headers = ['ID', 'Code', 'Title', 'Status', 'Assigned To', 'Start Date', 'End Date']
    rows = [[e.id, e.code, e.title, e.project_status, getattr(e.assigned_to, 'email', ''), e.project_start_date, e.target_end_date] for e in qs]
    if export_format == 'xlsx':
        return export_to_xlsx(headers, rows, 'engagements.xlsx')
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="engagements.csv"'
    writer = csv.writer(response)
    writer.writerow(headers)
    for row in rows:
        writer.writerow(row)
    return response

@login_required
def export_issues(request):
    name = request.GET.get('name')
    severity = request.GET.get('severity')
    export_format = request.GET.get('format', 'csv')
    qs = Issue.objects.filter(organization=request.organization)
    if name:
        qs = qs.filter(issue_title__icontains=name)
    if severity:
        qs = qs.filter(severity_status=severity)
    headers = ['ID', 'Code', 'Title', 'Severity', 'Status', 'Owner', 'Date Identified']
    rows = [[i.id, i.code, i.issue_title, i.severity_status, i.issue_status, getattr(i.issue_owner, 'email', ''), i.date_identified] for i in qs]
    if export_format == 'xlsx':
        return export_to_xlsx(headers, rows, 'issues.xlsx')
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="issues.csv"'
    writer = csv.writer(response)
    writer.writerow(headers)
    for row in rows:
        writer.writerow(row)
    return response

class ObjectiveListView(AuditPermissionMixin, ListView):
    model = Objective
    template_name = 'audit/objective_list.html'
    context_object_name = 'objectives'
    paginate_by = 20

    def get_queryset(self):
        queryset = super().get_queryset()
        organization = self.request.organization
        return queryset.filter(engagement__organization=organization)

class ObjectiveDetailView(AuditPermissionMixin, DetailView):
    model = Objective
    template_name = 'audit/objective_detail.html'
    context_object_name = 'objective'

class ObjectiveCreateView(AuditPermissionMixin, SuccessMessageMixin, CreateView):
    model = Objective
    form_class = ObjectiveForm
    template_name = 'audit/objective_form.html'
    success_message = _('Objective %(title)s was created successfully')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['organization'] = self.request.organization
        return kwargs

    def form_valid(self, form):
        engagement_pk = self.kwargs.get('engagement_pk')
        form.instance.engagement_id = engagement_pk
        form.instance.organization = self.request.organization
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy('audit:engagement-detail', kwargs={'pk': self.object.engagement.pk})

class ObjectiveUpdateView(AuditPermissionMixin, SuccessMessageMixin, UpdateView):
    model = Objective
    form_class = ObjectiveForm
    template_name = 'audit/objective_form.html'
    success_message = _('Objective %(title)s was updated successfully')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['organization'] = self.request.organization
        return kwargs

    def get_success_url(self):
        return reverse_lazy('audit:engagement-detail', kwargs={'pk': self.object.engagement.pk})

class ObjectiveModalCreateView(AuditPermissionMixin, SuccessMessageMixin, CreateView):
    model = Objective
    form_class = ObjectiveForm
    template_name = 'audit/objective_modal_form.html'
    success_message = _('Objective %(title)s was created successfully')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['organization'] = self.request.organization
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['engagement_pk'] = self.kwargs.get('engagement_pk')
        return context

    def form_valid(self, form):
        engagement_pk = self.kwargs.get('engagement_pk')
        form.instance.engagement_id = engagement_pk
        form.instance.organization = self.request.organization
        response = super().form_valid(form)
        if self.request.headers.get("x-requested-with") == "XMLHttpRequest" or self.request.headers.get("HX-Request") == "true":
            return JsonResponse({'success': True, 'pk': self.object.pk, 'title': self.object.title})
        return response

    def get_success_url(self):
        return reverse_lazy('audit:engagement-detail', kwargs={'pk': self.object.engagement.pk})

# PROCEDURE VIEWS
class ProcedureListView(AuditPermissionMixin, ListView):
    model = Procedure
    template_name = 'audit/procedure_list.html'
    context_object_name = 'procedures'
    paginate_by = 20
    def get_queryset(self):
        queryset = super().get_queryset()
        organization = self.request.organization
        return queryset.filter(objective__engagement__organization=organization)

class ProcedureDetailView(AuditPermissionMixin, DetailView):
    model = Procedure
    template_name = 'audit/procedure_detail.html'
    context_object_name = 'procedure'

class ProcedureCreateView(AuditPermissionMixin, SuccessMessageMixin, CreateView):
    model = Procedure
    form_class = ProcedureForm
    template_name = 'audit/procedure_form.html'
    success_message = _('Procedure %(title)s was created successfully')
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['organization'] = self.request.organization
        return kwargs
    def form_valid(self, form):
        objective_pk = self.kwargs.get('objective_pk')
        form.instance.objective_id = objective_pk
        form.instance.organization = self.request.organization
        return super().form_valid(form)
    def get_success_url(self):
        return reverse_lazy('audit:objective-detail', kwargs={'pk': self.object.objective.pk})

class ProcedureUpdateView(AuditPermissionMixin, SuccessMessageMixin, UpdateView):
    model = Procedure
    form_class = ProcedureForm
    template_name = 'audit/procedure_form.html'
    success_message = _('Procedure %(title)s was updated successfully')
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['organization'] = self.request.organization
        return kwargs
    def get_success_url(self):
        return reverse_lazy('audit:objective-detail', kwargs={'pk': self.object.objective.pk})

class ProcedureModalCreateView(AuditPermissionMixin, SuccessMessageMixin, CreateView):
    model = Procedure
    form_class = ProcedureForm
    template_name = 'audit/procedure_modal_form.html'
    success_message = _('Procedure %(title)s was created successfully')
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['organization'] = self.request.organization
        # Pass the specific objective_pk to the form for context-aware filtering
        kwargs['objective_pk'] = self.kwargs.get('objective_pk')
        return kwargs
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['objective_pk'] = self.kwargs.get('objective_pk')
        return context
    def form_valid(self, form):
        objective_pk = self.kwargs.get('objective_pk')
        form.instance.objective_id = objective_pk
        form.instance.organization = self.request.organization
        response = super().form_valid(form)
        if self.request.headers.get("x-requested-with") == "XMLHttpRequest" or self.request.headers.get("HX-Request") == "true":
            return JsonResponse({'success': True, 'pk': self.object.pk, 'title': self.object.title})
        return response

    def get_success_url(self):
        return reverse_lazy('audit:objective-detail', kwargs={'pk': self.object.objective.pk})

# PROCEDURE RESULT VIEWS
class ProcedureResultListView(AuditPermissionMixin, ListView):
    model = ProcedureResult
    template_name = 'audit/procedureresult_list.html'
    context_object_name = 'procedure_results'
    paginate_by = 20
    def get_queryset(self):
        queryset = super().get_queryset()
        organization = self.request.organization
        return queryset.filter(procedure__objective__engagement__organization=organization)

class ProcedureResultDetailView(AuditPermissionMixin, DetailView):
    model = ProcedureResult
    template_name = 'audit/procedureresult_detail.html'
    context_object_name = 'procedure_result'

class ProcedureResultCreateView(AuditPermissionMixin, SuccessMessageMixin, CreateView):
    model = ProcedureResult
    form_class = ProcedureResultForm
    template_name = 'audit/procedureresult_form.html'
    success_message = _('Procedure Result was created successfully')
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['organization'] = self.request.organization
        return kwargs
    def form_valid(self, form):
        procedure_pk = self.kwargs.get('procedure_pk')
        form.instance.procedure_id = procedure_pk
        form.instance.organization = self.request.organization
        return super().form_valid(form)
    def get_success_url(self):
        return reverse_lazy('audit:procedure-detail', kwargs={'pk': self.object.procedure.pk})

class ProcedureResultUpdateView(AuditPermissionMixin, SuccessMessageMixin, UpdateView):
    model = ProcedureResult
    form_class = ProcedureResultForm
    template_name = 'audit/procedureresult_form.html'
    success_message = _('Procedure Result was updated successfully')
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['organization'] = self.request.organization
        return kwargs
    def get_success_url(self):
        return reverse_lazy('audit:procedure-detail', kwargs={'pk': self.object.procedure.pk})

class ProcedureResultModalCreateView(AuditPermissionMixin, SuccessMessageMixin, CreateView):
    model = ProcedureResult
    form_class = ProcedureResultForm
    template_name = 'audit/procedureresult_modal_form.html'
    success_message = _('Procedure Result was created successfully')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['organization'] = self.request.organization
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['procedure_pk'] = self.kwargs.get('procedure_pk')
        return context

    def form_valid(self, form):
        procedure_pk = self.kwargs.get('procedure_pk')
        form.instance.procedure_id = procedure_pk
        form.instance.organization = self.request.organization
        response = super().form_valid(form)
        if self.request.headers.get("x-requested-with") == "XMLHttpRequest" or self.request.headers.get("HX-Request") == "true":
            results = ProcedureResult.objects.filter(procedure_id=procedure_pk, organization=self.request.organization)
            from .models.procedure import Procedure
            html_list = render_to_string("audit/_procedure_result_list_partial.html", {
                "results": results,
                "procedure": Procedure.objects.get(pk=procedure_pk),
            }, request=self.request)
            return JsonResponse({"form_is_valid": True, "html_list": html_list})
        return response

    def form_invalid(self, form):
        if self.request.headers.get("x-requested-with") == "XMLHttpRequest":
            html_form = render_to_string(self.template_name, {"form": form}, request=self.request)
            return JsonResponse({"form_is_valid": False, "html_form": html_form})
        return super().form_invalid(form)

    def get_success_url(self):
        return reverse_lazy('audit:procedure-detail', kwargs={'pk': self.object.procedure.pk})

class ProcedureResultModalUpdateView(AuditPermissionMixin, SuccessMessageMixin, UpdateView):
    model = ProcedureResult
    form_class = ProcedureResultForm
    template_name = 'audit/procedureresult_modal_form.html'
    success_message = _('Procedure Result was updated successfully')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['organization'] = self.request.organization
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['procedure_pk'] = self.object.procedure.pk if self.object.procedure_id else None
        return context

    def form_valid(self, form):
        response = super().form_valid(form)
        if self.request.headers.get("x-requested-with") == "XMLHttpRequest" or self.request.headers.get("HX-Request") == "true":
            results = ProcedureResult.objects.filter(procedure_id=self.object.procedure_id, organization=self.request.organization)
            from .models.procedure import Procedure
            html_list = render_to_string("audit/_procedure_result_list_partial.html", {
                "results": results,
                "procedure": Procedure.objects.get(pk=self.object.procedure_id),
            }, request=self.request)
            return JsonResponse({"form_is_valid": True, "html_list": html_list})
        return response

    def form_invalid(self, form):
        if self.request.headers.get("x-requested-with") == "XMLHttpRequest":
            html_form = render_to_string(self.template_name, {"form": form}, request=self.request)
            return JsonResponse({"form_is_valid": False, "html_form": html_form})
        return super().form_invalid(form)

    def get_success_url(self):
        return reverse_lazy('audit:procedure-detail', kwargs={'pk': self.object.procedure.pk})

# FOLLOWUP ACTION VIEWS
class FollowUpActionListView(AuditPermissionMixin, ListView):
    model = FollowUpAction
    template_name = 'audit/followupaction_list.html'
    context_object_name = 'followup_actions'
    paginate_by = 20
    
    def get_queryset(self):
        queryset = super().get_queryset()
        organization = self.request.organization
        
        # Filter by organization
        queryset = queryset.filter(organization=organization)
        
        # Filter by issue if specified
        issue_pk = self.request.GET.get('issue_pk')
        if issue_pk:
            queryset = queryset.filter(issue_id=issue_pk)
            
        # Filter by status if specified
        status = self.request.GET.get('status')
        if status:
            queryset = queryset.filter(status=status)
            
        # Filter by assigned_to if specified
        assigned_to = self.request.GET.get('assigned_to')
        if assigned_to:
            queryset = queryset.filter(assigned_to_id=assigned_to)
            
        # Order by due date (ascending, with nulls last)
        queryset = queryset.order_by(
            models.F('due_date').asc(nulls_last=True),
            '-created_at'
        )
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        organization = self.request.organization
        
        # Add filter form data
        context['status_choices'] = dict(FollowUpAction.STATUS_CHOICES)
        
        # Add issue info if filtered by issue
        issue_pk = self.request.GET.get('issue_pk')
        if issue_pk:
            from .models.issue import Issue
            try:
                context['issue'] = Issue.objects.get(pk=issue_pk, organization=organization)
            except Issue.DoesNotExist:
                pass
                
        # Add assigned users for filter
        context['assigned_users'] = CustomUser.objects.filter(
            organization=organization,
            followup_actions_assigned__isnull=False
        ).distinct()
        
        return context

class FollowUpActionDetailView(AuditPermissionMixin, DetailView):
    model = FollowUpAction
    template_name = 'audit/followupaction_detail.html'
    context_object_name = 'followup_action'
    
    def get_queryset(self):
        queryset = super().get_queryset()
        return queryset.filter(organization=self.request.organization)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['can_edit'] = self.request.user.has_perm('audit.change_followupaction')
        context['can_delete'] = self.request.user.has_perm('audit.delete_followupaction')
        return context

class FollowUpActionCreateView(AuditPermissionMixin, SuccessMessageMixin, CreateView):
    model = FollowUpAction
    form_class = FollowUpActionForm
    template_name = "audit/followupaction_form.html"
    success_message = _("Follow Up Action was created successfully")

    def get_issue_pk(self):
        issue_pk = self.kwargs.get("issue_pk") or self.request.GET.get("issue_pk") or self.request.POST.get("issue_pk")
        if not issue_pk:
            raise ValueError("issue_pk is required for this modal")
        return issue_pk

    def get_initial(self):
        return {"issue": self.get_issue_pk()}

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["organization"] = self.request.organization
        kwargs["issue_pk"] = self.get_issue_pk()
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        from .models.issue import Issue
        try:
            issue_pk = self.get_issue_pk()
            context["issue"] = Issue.objects.get(pk=issue_pk)
            context["issue_pk"] = issue_pk
        except Exception:
            context["issue"] = None
            context["issue_pk"] = None
        return context

    def form_valid(self, form):
        form.instance.issue_id = self.get_issue_pk()
        form.instance.organization = self.request.organization
        form.instance.created_by = self.request.user  # Automatically set the creator
        response = super().form_valid(form)
        if self.request.headers.get("x-requested-with") == "XMLHttpRequest" or self.request.headers.get("HX-Request") == "true":
            followups = FollowUpAction.objects.filter(issue_id=self.get_issue_pk(), organization=self.request.organization)
            from .models.issue import Issue
            html_list = render_to_string("audit/followupaction_list.html", {
                "followup_actions": followups,
                "issue": Issue.objects.get(pk=self.get_issue_pk()),
            }, request=self.request)
            return JsonResponse({"form_is_valid": True, "html_list": html_list})
        return response

    def form_invalid(self, form):
        if self.request.headers.get("x-requested-with") == "XMLHttpRequest":
            html_form = render_to_string(self.template_name, {"form": form}, request=self.request)
            return JsonResponse({"form_is_valid": False, "html_form": html_form})
        return super().form_invalid(form)

    def get_success_url(self):
        return reverse_lazy("audit:followupaction-list", kwargs={"issue_pk": self.get_issue_pk()})

class FollowUpActionUpdateView(AuditPermissionMixin, SuccessMessageMixin, UpdateView):
    model = FollowUpAction
    form_class = FollowUpActionForm
    template_name = "audit/followupaction_form.html"
    success_message = _("Follow Up Action was updated successfully")
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["organization"] = self.request.organization
        if hasattr(self, 'object') and self.object.issue_id:
            kwargs["issue_pk"] = self.object.issue_id
        return kwargs
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if hasattr(self, 'object') and self.object.issue:
            context["issue"] = self.object.issue
            context["issue_pk"] = self.object.issue_id
        return context
    
    def form_valid(self, form):
        form.instance.organization = self.request.organization
        response = super().form_valid(form)
        if self.request.headers.get("x-requested-with") == "XMLHttpRequest" or self.request.headers.get("HX-Request") == "true":
            from .models.issue import Issue
            followups = FollowUpAction.objects.filter(issue_id=self.object.issue_id, organization=self.request.organization)
            html_list = render_to_string("audit/followupaction_list.html", {
                "followup_actions": followups,
                "issue": Issue.objects.get(pk=self.object.issue_id),
            }, request=self.request)
            return JsonResponse({"form_is_valid": True, "html_list": html_list})
        return response
    
    def form_invalid(self, form):
        if self.request.headers.get("x-requested-with") == "XMLHttpRequest" or self.request.headers.get("HX-Request") == "true":
            html_form = render_to_string(self.template_name, {"form": form}, request=self.request)
            return JsonResponse({"form_is_valid": False, "html_form": html_form})
        return super().form_invalid(form)
    
    def get_success_url(self):
        if hasattr(self, 'object') and self.object.issue_id:
            return reverse_lazy('audit:issue-detail', kwargs={'pk': self.object.issue_id})
        return reverse_lazy('audit:followupaction-list')

class FollowUpActionModalCreateView(AuditPermissionMixin, SuccessMessageMixin, CreateView):
    model = FollowUpAction
    form_class = FollowUpActionForm
    template_name = 'audit/followupaction_modal_form.html'
    success_message = _('Follow Up Action was created successfully')

    def get_issue_pk(self):
        """Get the issue_pk from URL kwargs or request parameters."""
        return self.kwargs.get("issue_pk") or self.request.GET.get("issue_pk")

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["organization"] = self.request.organization
        issue_pk = self.get_issue_pk()
        if issue_pk:
            kwargs["issue_pk"] = issue_pk
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        issue_pk = self.get_issue_pk()
        if issue_pk:
            from .models.issue import Issue
            try:
                context["issue"] = Issue.objects.get(pk=issue_pk, organization=self.request.organization)
            except Issue.DoesNotExist:
                pass
        return context

    def get(self, request, *args, **kwargs):
        """Handle GET request to display the form."""
        self.object = None
        form_class = self.get_form_class()
        form = self.get_form(form_class)
        
        # Add HTMX headers to the response
        context = self.get_context_data(form=form)
        if request.headers.get('HX-Request'):
            return self.render_to_response(context)
        return super().get(request, *args, **kwargs)
        
    def form_valid(self, form):
        """Handle form validation and submission."""
        issue_pk = self.get_issue_pk()
        if not issue_pk:
            form.add_error(None, _("Issue is required for creating a follow-up action."))
            return self.form_invalid(form)
            
        form.instance.issue_id = issue_pk
        form.instance.organization = self.request.organization
        form.instance.created_by = self.request.user
        
        try:
            self.object = form.save()
            
            # Handle HTMX request
            if self.request.headers.get('HX-Request'):
                from django.template.loader import render_to_string
                from .models.issue import Issue
                
                try:
                    issue = Issue.objects.get(pk=issue_pk, organization=self.request.organization)
                    followups = FollowUpAction.objects.filter(issue=issue, organization=self.request.organization)
                    
                    # Render the follow-up list partial
                    html = render_to_string(
                        'audit/_followupaction_list_partial.html',
                        {
                            'followups': followups,
                            'issue': issue,
                            'request': self.request
                        }
                    )
                    
                    # Return success response with HTML
                    return HttpResponse(html)
                    
                except Issue.DoesNotExist:
                    return JsonResponse({
                        'success': False,
                        'message': _("Error: Related issue not found.")
                    }, status=400)
            
            # For non-HTMX requests, redirect to success URL
            messages.success(self.request, self.get_success_message(form.cleaned_data))
            return redirect(self.get_success_url())
            
        except Exception as e:
            if self.request.headers.get('HX-Request'):
                return JsonResponse({
                    'success': False,
                    'message': str(e)
                }, status=400)
            raise

    def form_invalid(self, form):
        if self.request.headers.get("x-requested-with") == "XMLHttpRequest" or self.request.headers.get("HX-Request") == "true":
            html_form = render_to_string(
                self.template_name,
                self.get_context_data(form=form),
                request=self.request
            )
            return JsonResponse({
                "form_is_valid": False,
                "html_form": html_form
            })
        return super().form_invalid(form)

    def get_success_url(self):
        issue_pk = self.get_issue_pk()
        if issue_pk:
            return reverse_lazy("audit:issue-detail", kwargs={"pk": issue_pk})
        return reverse_lazy("audit:followupaction-list")

class FollowUpActionModalUpdateView(AuditPermissionMixin, SuccessMessageMixin, UpdateView):
    model = FollowUpAction
    form_class = FollowUpActionForm
    template_name = 'audit/followupaction_modal_form.html'
    success_message = _('Follow Up Action was updated successfully')

    def get_queryset(self):
        """Limit queryset to objects in the current organization."""
        return super().get_queryset().filter(organization=self.request.organization)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['organization'] = self.request.organization
        if hasattr(self, 'object') and self.object.issue_id:
            kwargs['issue_pk'] = self.object.issue_id
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if hasattr(self, 'object') and self.object.issue:
            context['issue'] = self.object.issue
        return context

    def form_valid(self, form):
        form.instance.organization = self.request.organization
        response = super().form_valid(form)
        
        # Handle HTMX/JSON response
        if self.request.headers.get("x-requested-with") == "XMLHttpRequest" or self.request.headers.get("HX-Request") == "true":
            try:
                # Return a success response that will close the modal
                return JsonResponse({
                    'success': True,
                    'message': str(self.success_message),
                    'redirect_url': self.get_success_url()
                })
            except Exception as e:
                return JsonResponse({
                    'success': False,
                    'message': _("Error updating follow-up action: {}".format(str(e)))
                }, status=400)
        
        return response

    def form_invalid(self, form):
        if self.request.headers.get("x-requested-with") == "XMLHttpRequest" or self.request.headers.get("HX-Request") == "true":
            html_form = render_to_string(
                self.template_name,
                self.get_context_data(form=form),
                request=self.request
            )
            return JsonResponse({
                'success': False,
                'form_errors': form.errors,
                'html_form': html_form
            }, status=400)
        return super().form_invalid(form)

    def get_success_url(self):
        if hasattr(self, 'object') and self.object.issue_id:
            return reverse_lazy('audit:issue-detail', kwargs={'pk': self.object.issue_id})
        return reverse_lazy('audit:followupaction-list')

# ISSUE RETEST VIEWS
class IssueRetestListView(AuditPermissionMixin, ListView):
    model = IssueRetest
    template_name = 'audit/issueretest_list.html'
    context_object_name = 'issue_retests'
    paginate_by = 20
    def get_queryset(self):
        queryset = super().get_queryset()
        organization = self.request.organization
        return queryset.filter(issue__procedure_result__procedure__objective__engagement__organization=organization)

class IssueRetestDetailView(AuditPermissionMixin, DetailView):
    model = IssueRetest
    template_name = 'audit/issueretest_detail.html'
    context_object_name = 'issue_retest'

class IssueRetestCreateView(AuditPermissionMixin, SuccessMessageMixin, CreateView):
    model = IssueRetest
    form_class = IssueRetestForm
    template_name = "audit/issueretest_form.html"
    success_message = _("Issue Retest was created successfully")

    def get_initial(self):
        return {"issue": self.kwargs["issue_pk"]}

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["organization"] = self.request.organization
        return kwargs

    def form_valid(self, form):
        form.instance.issue_id = self.kwargs["issue_pk"]
        form.instance.organization = self.request.organization
        response = super().form_valid(form)
        if self.request.headers.get("x-requested-with") == "XMLHttpRequest" or self.request.headers.get("HX-Request") == "true":
            retests = IssueRetest.objects.filter(issue_id=self.kwargs["issue_pk"], organization=self.request.organization)
            from .models.issue import Issue
            html_list = render_to_string("audit/issueretest_list.html", {
                "issue_retests": retests,
                "issue": Issue.objects.get(pk=self.kwargs["issue_pk"]),
            }, request=self.request)
            return JsonResponse({"form_is_valid": True, "html_list": html_list})
        return response

    def form_invalid(self, form):
        if self.request.headers.get("x-requested-with") == "XMLHttpRequest":
            html_form = render_to_string(self.template_name, {"form": form}, request=self.request)
            return JsonResponse({"form_is_valid": False, "html_form": html_form})
        return super().form_invalid(form)

    def get_success_url(self):
        return reverse_lazy("audit:issueretest-list", kwargs={"issue_pk": self.kwargs["issue_pk"]})

class IssueRetestUpdateView(IssueRetestCreateView, UpdateView):
    success_message = _("Issue Retest was updated successfully")

class IssueRetestModalCreateView(AuditPermissionMixin, SuccessMessageMixin, CreateView):
    model = IssueRetest
    form_class = IssueRetestForm
    template_name = 'audit/issueretest_modal_form.html'
    success_message = _('Retest was created successfully')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['organization'] = self.request.organization
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['issue_pk'] = self.kwargs.get('issue_pk')
        return context

    def form_valid(self, form):
        issue_pk = self.kwargs.get('issue_pk')
        form.instance.issue_id = issue_pk
        form.instance.organization = self.request.organization
        response = super().form_valid(form)
        if self.request.htmx or self.request.headers.get('HX-Request') == 'true':
            from django.template.loader import render_to_string
            from django.http import JsonResponse
            html = render_to_string('audit/_issueretest_list_partial.html', {
                'issue_retests': IssueRetest.objects.filter(issue_id=issue_pk)
            }, request=self.request)
            return JsonResponse({'success': True, 'html': html})
        return response

    def form_invalid(self, form):
        if self.request.htmx or self.request.headers.get('HX-Request') == 'true':
            from django.template.loader import render_to_string
            from django.http import JsonResponse
            html = render_to_string(self.template_name, self.get_context_data(form=form), request=self.request)
            return JsonResponse({'success': False, 'html': html}, status=400)
        return super().form_invalid(form)

    def get_success_url(self):
        return reverse_lazy('audit:issue-detail', kwargs={'pk': self.object.issue.pk})

class IssueRetestModalUpdateView(AuditPermissionMixin, SuccessMessageMixin, UpdateView):
    model = IssueRetest
    form_class = IssueRetestForm
    template_name = 'audit/issueretest_modal_form.html'
    success_message = _('Retest was updated successfully')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['organization'] = self.request.organization
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['issue_pk'] = self.object.issue.pk if self.object.issue_id else None
        return context

    def form_valid(self, form):
        response = super().form_valid(form)
        if self.request.htmx or self.request.headers.get('HX-Request') == 'true':
            from django.template.loader import render_to_string
            from django.http import JsonResponse
            html = render_to_string('audit/_issueretest_list_partial.html', {
                'issue_retests': IssueRetest.objects.filter(issue_id=self.object.issue_id)
            }, request=self.request)
            return JsonResponse({'success': True, 'html': html})
        return response

    def form_invalid(self, form):
        if self.request.htmx or self.request.headers.get('HX-Request') == 'true':
            from django.template.loader import render_to_string
            from django.http import JsonResponse
            html = render_to_string(self.template_name, self.get_context_data(form=form), request=self.request)
            return JsonResponse({'success': False, 'html': html}, status=400)
        return super().form_invalid(form)

    def get_success_url(self):
        return reverse_lazy('audit:issue-detail', kwargs={'pk': self.object.issue.pk})

# NOTE VIEWS (GENERIC, MODAL)
class NoteCreateView(AuditPermissionMixin, SuccessMessageMixin, CreateView):
    model = Note
    form_class = NoteForm
    template_name = 'audit/note_modal_form.html'
    success_message = _('Note was created successfully')

    def get_issue_pk(self):
        issue_pk = self.kwargs.get('issue_pk') or self.request.GET.get('issue_pk') or self.request.POST.get('issue_pk')
        return issue_pk

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['organization'] = self.request.organization
        # Only pass issue_pk if it exists
        issue_pk = self.get_issue_pk()
        if issue_pk:
            kwargs['issue_pk'] = issue_pk
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Add content type and object id to the context for proper rendering
        context['content_type_id'] = self.kwargs.get('content_type_id')
        context['object_id'] = self.kwargs.get('object_id')
        
        # Add issue_pk only if it exists
        issue_pk = self.get_issue_pk()
        if issue_pk:
            context['issue_pk'] = issue_pk
        return context

    def form_valid(self, form):
        form.instance.organization = self.request.organization
        form.instance.content_type_id = self.kwargs.get('content_type_id')
        form.instance.object_id = self.kwargs.get('object_id')
        response = super().form_valid(form)
        if self.request.headers.get("x-requested-with") == "XMLHttpRequest" or self.request.headers.get("HX-Request") == "true":
            notes = Note.objects.filter(content_type_id=self.kwargs.get('content_type_id'), object_id=self.kwargs.get('object_id'), organization=self.request.organization)
            html_list = render_to_string("audit/_note_list_partial.html", {
                "notes": notes,
            }, request=self.request)
            return JsonResponse({"form_is_valid": True, "html_list": html_list})
        return response

    def form_invalid(self, form):
        if self.request.headers.get("x-requested-with") == "XMLHttpRequest":
            html_form = render_to_string(self.template_name, {"form": form}, request=self.request)
            return JsonResponse({"form_is_valid": False, "html_form": html_form})
        return super().form_invalid(form)

    def get_success_url(self):
        return reverse_lazy('audit:note-list')

class NoteModalUpdateView(AuditPermissionMixin, SuccessMessageMixin, UpdateView):
    model = Note
    form_class = NoteForm
    template_name = "audit/note_modal_form.html"
    success_message = _("Note was updated successfully")

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['organization'] = self.request.organization
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['content_type_id'] = self.object.content_type_id
        context['object_id'] = self.object.object_id
        return context

    def form_valid(self, form):
        response = super().form_valid(form)
        if self.request.headers.get("x-requested-with") == "XMLHttpRequest" or self.request.headers.get("HX-Request") == "true":
            notes = Note.objects.filter(content_type_id=self.object.content_type_id, object_id=self.object.object_id, organization=self.request.organization)
            html_list = render_to_string("audit/_note_list_partial.html", {
                "notes": notes,
            }, request=self.request)
            return JsonResponse({"form_is_valid": True, "html_list": html_list})
        return response

    def form_invalid(self, form):
        if self.request.headers.get("x-requested-with") == "XMLHttpRequest":
            html_form = render_to_string(self.template_name, {"form": form}, request=self.request)
            return JsonResponse({"form_is_valid": False, "html_form": html_form})
        return super().form_invalid(form)

    def get_success_url(self):
        return reverse_lazy('audit:note-list')

class NotificationListView(AuditPermissionMixin, generics.ListAPIView):
    serializer_class = NotificationSerializer
    permission_classes = [permissions.IsAuthenticated]
    def get_queryset(self):
        return Notification.objects.filter(user=self.request.user, user__organization=self.request.organization)

class NotificationTemplateView(AuditPermissionMixin, ListView):
    """A template-based view for displaying notifications in a user-friendly UI"""
    model = Notification
    template_name = 'audit/notification_list.html'
    context_object_name = 'notifications'
    paginate_by = 20
    
    def get_queryset(self):
        # Get notifications for the current user and mark them as read
        queryset = Notification.objects.filter(
            user=self.request.user, 
            user__organization=self.request.organization
        ).order_by('-created_at')
        
        # Mark all as read (optional, remove if you want to keep unread status)
        # queryset.update(is_read=True)
        
        return queryset
        
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['unread_count'] = Notification.objects.filter(
            user=self.request.user,
            user__organization=self.request.organization,
            is_read=False
        ).count()
        return context

class NoteListView(AuditPermissionMixin, ListView):
    model = Note
    template_name = 'audit/note_list.html'
    context_object_name = 'notes'
    paginate_by = 20

    def get_queryset(self):
        queryset = super().get_queryset()
        organization = self.request.organization
        queryset = queryset.filter(organization=organization)
        # Optionally filter by content_type/object_id if provided
        content_type_id = self.request.GET.get('content_type_id')
        object_id = self.request.GET.get('object_id')
        if content_type_id and object_id:
            queryset = queryset.filter(content_type_id=content_type_id, object_id=object_id)
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['content_type_id'] = self.request.GET.get('content_type_id')
        context['object_id'] = self.request.GET.get('object_id')
        return context

class RecommendationListView(AuditPermissionMixin, ListView):
    model = Recommendation
    template_name = "audit/recommendation_list.html"
    context_object_name = "recommendations"

    def get_queryset(self):
        issue_pk = self.kwargs["issue_pk"]
        return Recommendation.objects.filter(issue_id=issue_pk, organization=self.request.organization)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        from .models.issue import Issue
        context["issue"] = Issue.objects.get(pk=self.kwargs["issue_pk"])
        return context

class RecommendationCreateView(AuditPermissionMixin, SuccessMessageMixin, CreateView):
    model = Recommendation
    form_class = RecommendationForm
    template_name = "audit/recommendation_form.html"
    success_message = _("Recommendation was created successfully")

    def get_issue_pk(self):
        issue_pk = self.kwargs.get("issue_pk") or self.request.GET.get("issue_pk") or self.request.POST.get("issue_pk")
        if not issue_pk:
            raise ValueError("issue_pk is required for this modal")
        return issue_pk

    def get_initial(self):
        return {"issue": self.get_issue_pk()}

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["organization"] = self.request.organization
        kwargs["issue_pk"] = self.get_issue_pk()
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        from .models.issue import Issue
        try:
            issue_pk = self.get_issue_pk()
            context["issue"] = Issue.objects.get(pk=issue_pk)
            context["issue_pk"] = issue_pk
        except Exception:
            context["issue"] = None
            context["issue_pk"] = None
        return context

    def form_valid(self, form):
        form.instance.issue_id = self.get_issue_pk()
        form.instance.organization = self.request.organization
        response = super().form_valid(form)
        if self.request.headers.get("x-requested-with") == "XMLHttpRequest" or self.request.headers.get("HX-Request") == "true":
            recommendations = Recommendation.objects.filter(issue_id=self.get_issue_pk(), organization=self.request.organization)
            from .models.issue import Issue
            html_list = render_to_string("audit/recommendation_list.html", {
                "recommendations": recommendations,
                "issue": Issue.objects.get(pk=self.get_issue_pk()),
            }, request=self.request)
            return JsonResponse({"form_is_valid": True, "html_list": html_list})
        return response

    def form_invalid(self, form):
        if self.request.headers.get("x-requested-with") == "XMLHttpRequest":
            html_form = render_to_string(self.template_name, {"form": form}, request=self.request)
            return JsonResponse({"form_is_valid": False, "html_form": html_form})
        return super().form_invalid(form)

    def get_success_url(self):
        return reverse_lazy("audit:recommendation-list", kwargs={"issue_pk": self.get_issue_pk()})

class RecommendationUpdateView(RecommendationCreateView, UpdateView):
    success_message = _("Recommendation was updated successfully")
    
    def get_issue_pk(self):
        # Use the safe utility function to get issue_pk from any available source
        # without raising ValueError if not found
        return safe_get_issue_pk(self, raise_error=False)
        
    def get_form_kwargs(self):
        kwargs = super(RecommendationCreateView, self).get_form_kwargs()
        kwargs["organization"] = self.request.organization
        
        # Try to get issue_pk, add it to kwargs only if found
        issue_pk = self.get_issue_pk()
        if issue_pk:
            kwargs["issue_pk"] = issue_pk
        
        return kwargs
        
    def get_initial(self):
        initial = super(RecommendationCreateView, self).get_initial()
        issue_pk = self.get_issue_pk()
        if issue_pk:
            initial["issue"] = issue_pk
        return initial
        
    def form_valid(self, form):
        # Ensure the organization is set
        form.instance.organization = self.request.organization
        
        # Only set issue_id if we have a valid issue_pk
        issue_pk = self.get_issue_pk()
        if issue_pk:
            form.instance.issue_id = issue_pk
            
        return super().form_valid(form)

class RecommendationDetailView(AuditPermissionMixin, DetailView):
    model = Recommendation
    template_name = "audit/recommendation_detail.html"
    context_object_name = "recommendation"

class RecommendationModalUpdateView(AuditPermissionMixin, SuccessMessageMixin, UpdateView):
    model = Recommendation
    form_class = RecommendationForm
    template_name = 'audit/recommendation_modal_form.html'
    success_message = _('Recommendation was updated successfully')

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['organization'] = self.request.organization
        return kwargs

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['issue_pk'] = self.object.issue.pk if self.object.issue_id else None
        return context

    def form_valid(self, form):
        response = super().form_valid(form)
        if self.request.headers.get("x-requested-with") == "XMLHttpRequest" or self.request.headers.get("HX-Request") == "true":
            recommendations = Recommendation.objects.filter(issue_id=self.object.issue_id, organization=self.request.organization)
            from .models.issue import Issue
            html_list = render_to_string("audit/_recommendation_list_partial.html", {
                "recommendations": recommendations,
                "issue": Issue.objects.get(pk=self.object.issue_id),
            }, request=self.request)
            return JsonResponse({"form_is_valid": True, "html_list": html_list})
        return response

    def form_invalid(self, form):
        if self.request.headers.get("x-requested-with") == "XMLHttpRequest":
            html_form = render_to_string(self.template_name, {"form": form}, request=self.request)
            return JsonResponse({"form_is_valid": False, "html_form": html_form})
        return super().form_invalid(form)

    def get_success_url(self):
        return reverse_lazy('audit:issue-detail', kwargs={'pk': self.object.issue.pk})

@login_required
def api_engagements(request):
    org = request.organization
    qs = Engagement.objects.filter(organization=org).order_by('title')
    data = [{'id': e.pk, 'text': e.title} for e in qs]
    return JsonResponse(data, safe=False)

@login_required
def api_objectives(request):
    org = request.organization
    engagement_id = request.GET.get('engagement')
    qs = Objective.objects.filter(engagement__organization=org)
    if engagement_id:
        qs = qs.filter(engagement_id=engagement_id)
    data = [{'id': o.pk, 'text': o.title} for o in qs]
    return JsonResponse(data, safe=False)

@login_required
def api_issues(request):
    org = request.organization
    engagement_id = request.GET.get('engagement')
    qs = Issue.objects.filter(organization=org)
    if engagement_id:
        qs = qs.filter(engagement_id=engagement_id)
    data = [{'id': i.pk, 'text': i.issue_title} for i in qs]
    return JsonResponse(data, safe=False)

@login_required
def api_recommendations(request):
    org = request.organization
    issue_id = request.GET.get('issue')
    qs = Recommendation.objects.filter(organization=org)
    if issue_id:
        qs = qs.filter(issue_id=issue_id)
    data = [{'id': r.pk, 'text': r.title} for r in qs]
    return JsonResponse(data, safe=False)

@login_required
@require_GET
def htmx_objective_list(request):
    org = request.organization
    engagement_id = request.GET.get('engagement')
    qs = Objective.objects.filter(engagement__organization=org)
    if engagement_id:
        qs = qs.filter(engagement_id=engagement_id)
    html = render_to_string('audit/_objective_list_partial.html', {'objectives': qs})
    return JsonResponse({'html': html})

@login_required
@require_GET
def htmx_procedure_list(request):
    org = request.organization
    objective_id = request.GET.get('objective')
    qs = Procedure.objects.filter(objective__engagement__organization=org)
    if objective_id:
        qs = qs.filter(objective_id=objective_id)
    html = render_to_string('audit/_procedure_list_partial.html', {'procedures': qs})
    return JsonResponse({'html': html})

@login_required
@require_GET
def htmx_recommendation_list(request):
    org = request.organization
    issue_id = request.GET.get('issue')
    qs = Recommendation.objects.filter(organization=org)
    if issue_id:
        qs = qs.filter(issue_id=issue_id)
    html = render_to_string('audit/_recommendation_list_partial.html', {'recommendations': qs})
    return JsonResponse({'html': html})

@login_required
@require_HTTP_methods(["GET"])
def htmx_followupaction_list(request):
    """
    HTMX endpoint to load follow-up actions for an issue or recommendation.
    Supports both HTMX and regular AJAX requests.
    """
    try:
        # Get organization from the request or user's primary organization
        org = getattr(request, 'organization', None)
        if not org and hasattr(request.user, 'organization'):
            org = request.user.organization
            
        if not org:
            logger.error("Organization not found in request or user profile")
            raise PermissionDenied("Organization not found. Please ensure you're accessing this from within an organization context.")

        # Get filter parameters
        issue_id = request.GET.get('issue_id')
        recommendation_id = request.GET.get('recommendation')
        
        # Base queryset with select_related for performance
        qs = FollowUpAction.objects.filter(organization=org)
        qs = qs.select_related('issue', 'assigned_to', 'created_by')
        
        # Apply filters
        if issue_id and issue_id.isdigit():
            qs = qs.filter(issue_id=int(issue_id))
        if recommendation_id and recommendation_id.isdigit():
            qs = qs.filter(recommendation_id=int(recommendation_id))
        
        # Handle ordering with nulls last for due_date
        try:
            # Try with nulls_last if the database supports it
            qs = qs.order_by(F('due_date').asc(nulls_last=True), '-created_at')
        except (NotSupportedError, DatabaseError):
            # Fallback for databases that don't support nulls_last
            qs = qs.order_by(
                Case(When(due_date__isnull=True, then=1), default=0),
                     'due_date',
                     '-created_at'
            )
        
        context = {
            'followups': qs,
            'issue_id': issue_id,
            'request': request
        }
        
        # If this is an HTMX request, return just the list content
        if request.headers.get('HX-Request'):
            html = render_to_string('audit/_followupaction_list_partial.html', context)
            return HttpResponse(html)
        
        # For regular AJAX requests, return JSON
        return JsonResponse({
            'success': True,
            'count': qs.count(),
            'html': render_to_string('audit/_followupaction_list_partial.html', context)
        })
        
    except Exception as e:
        error_msg = f"Error in htmx_followupaction_list: {str(e)}"
        logger.error(error_msg, exc_info=True)
        
        # Prepare error context
        error_context = {
            'error': str(e),
            'error_type': e.__class__.__name__,
            'issue_id': request.GET.get('issue_id'),
            'recommendation_id': request.GET.get('recommendation'),
            'user': request.user.username if request.user.is_authenticated else 'anonymous'
        }
        
        # Log detailed error context
        logger.error(f"Error context: {error_context}")
        
        # Return appropriate response based on request type
        if request.headers.get('HX-Request'):
            error_html = render_to_string('audit/_error_alert.html', {
                'title': 'Error Loading Follow-up Actions',
                'message': 'There was an error loading the follow-up actions. Please try again later.',
                'error': str(e),
                'error_type': e.__class__.__name__,
                'debug': getattr(settings, 'DEBUG', False)
            })
            return HttpResponse(error_html, status=500)
            
        return JsonResponse(
            {
                'success': False,
                'error': 'An error occurred while loading follow-up actions.',
                'detail': str(e),
                'error_type': e.__class__.__name__
            },
            status=500
        )

@login_required
@require_GET
def htmx_issueretest_list(request):
    org = request.organization
    recommendation_id = request.GET.get('recommendation')
    qs = IssueRetest.objects.filter(organization=org)
    if recommendation_id:
        qs = qs.filter(recommendation_id=recommendation_id)
    html = render_to_string('audit/_issueretest_list_partial.html', {'issueretests': qs})
    return JsonResponse({'html': html})

@login_required
@require_GET
def htmx_note_list(request):
    org = request.organization
    object_id = request.GET.get('object_id')
    content_type_id = request.GET.get('content_type_id')
    qs = Note.objects.filter(organization=org)
    if object_id and content_type_id:
        qs = qs.filter(object_id=object_id, content_type_id=content_type_id)
    html = render_to_string('audit/_note_list_partial.html', {'notes': qs})
    return JsonResponse({'html': html})

class NoteDetailView(AuditPermissionMixin, DetailView):
    model = Note
    template_name = 'audit/note_detail.html'
    context_object_name = 'note'

# ─── ISSUE WORKING PAPER VIEWS ───────────────────────────────────────────────
class IssueWorkingPaperListView(AuditPermissionMixin, ListView):
    model = IssueWorkingPaper
    template_name = 'audit/issueworkingpaper_list.html'
    context_object_name = 'working_papers'
    paginate_by = 20

    def get_queryset(self):
        issue_pk = self.kwargs.get('issue_pk')
        organization = self.request.organization
        return IssueWorkingPaper.objects.filter(issue_id=issue_pk, organization=organization)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['issue_pk'] = self.kwargs.get('issue_pk')
        return context

class IssueWorkingPaperCreateView(AuditPermissionMixin, SuccessMessageMixin, CreateView):
    model = IssueWorkingPaper
    form_class = IssueWorkingPaperForm
    template_name = 'audit/issueworkingpaper_form.html'
    success_message = _('Working paper uploaded successfully')

    def get_template_names(self):
        if self.request.htmx or self.request.headers.get('HX-Request'):
            return ['audit/issueworkingpaper_modal_form.html']
        return [self.template_name]

    def form_valid(self, form):
        response = super().form_valid(form)
        if self.request.htmx or self.request.headers.get('HX-Request'):
            working_papers = IssueWorkingPaper.objects.filter(issue=self.object.issue)
            html_list = render_to_string('audit/issueworkingpaper_list.html', {
                'working_papers': working_papers,
                'issue': self.object.issue,
            }, request=self.request)
            return JsonResponse({'form_is_valid': True, 'html_list': html_list})
        return response

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if not hasattr(self, 'object') or not self.object:
            context['issue'] = get_object_or_404(Issue, pk=self.kwargs.get('issue_pk'))
        return context

    def form_invalid(self, form):
        if self.request.htmx or self.request.headers.get('HX-Request'):
            html_form = render_to_string('audit/issueworkingpaper_modal_form.html', 
                self.get_context_data(form=form, object=None),
                request=self.request
            )
            return JsonResponse({'form_is_valid': False, 'html_form': html_form})
        return super().form_invalid(form)

    def get_success_url(self):
        return reverse_lazy('audit:issue-detail', kwargs={'pk': self.object.issue.pk})

class IssueWorkingPaperUpdateView(AuditPermissionMixin, SuccessMessageMixin, UpdateView):
    model = IssueWorkingPaper
    form_class = IssueWorkingPaperForm
    template_name = 'audit/issueworkingpaper_form.html'
    success_message = _('Working paper updated successfully')

    def get_template_names(self):
        if self.request.htmx or self.request.headers.get('HX-Request'):
            return ['audit/issueworkingpaper_modal_form.html']
        return [self.template_name]

    def form_valid(self, form):
        response = super().form_valid(form)
        if self.request.htmx or self.request.headers.get('HX-Request'):
            working_papers = IssueWorkingPaper.objects.filter(issue=self.object.issue)
            html_list = render_to_string('audit/issueworkingpaper_list.html', {
                'working_papers': working_papers,
                'issue': self.object.issue,
            }, request=self.request)
            return JsonResponse({'form_is_valid': True, 'html_list': html_list})
        return response

    def form_invalid(self, form):
        if self.request.htmx or self.request.headers.get('HX-Request'):
            html_form = render_to_string('audit/issueworkingpaper_modal_form.html', {
                'form': form,
                'object': self.object,
            }, request=self.request)
            return JsonResponse({'form_is_valid': False, 'html_form': html_form})
        return super().form_invalid(form)

    def get_success_url(self):
        return reverse_lazy('audit:issue-detail', kwargs={'pk': self.object.issue_id})

class IssueWorkingPaperDeleteView(AuditPermissionMixin, DeleteView):
    model = IssueWorkingPaper
    template_name = 'audit/issueworkingpaper_confirm_delete.html'

    def get_template_names(self):
        if self.request.htmx or self.request.headers.get('HX-Request'):
            return ['audit/issueworkingpaper_confirm_delete.html']
        return [self.template_name]

    def delete(self, request, *args, **kwargs):
        self.object = self.get_object()
        issue = self.object.issue
        self.object.delete()
        if self.request.htmx or self.request.headers.get('HX-Request'):
            working_papers = IssueWorkingPaper.objects.filter(issue=issue)
            html_list = render_to_string('audit/issueworkingpaper_list.html', {
                'working_papers': working_papers,
                'issue': issue,
            }, request=self.request)
            return JsonResponse({'form_is_valid': True, 'html_list': html_list})
        return super().delete(request, *args, **kwargs)

class IssueWorkingPaperDetailView(AuditPermissionMixin, DetailView):
    model = IssueWorkingPaper
    template_name = 'audit/issueworkingpaper_detail.html'
    context_object_name = 'working_paper'

# ─── API VIEWSET ─────────────────────────────────────────────────────────────
from rest_framework import mixins
class IssueWorkingPaperViewSet(viewsets.ModelViewSet):
    serializer_class = IssueWorkingPaperSerializer
    permission_classes = [permissions.IsAuthenticated, IsOrgManagerOrReadOnly]

    def get_queryset(self):
        issue_pk = self.kwargs.get('issue_pk')
        qs = IssueWorkingPaper.objects.all()
        if issue_pk:
            qs = qs.filter(issue_id=issue_pk)
        return qs.filter(organization=self.request.organization)

    def perform_create(self, serializer):
        serializer.save(
            organization=self.request.organization,
            created_by=self.request.user
        )
