# apps/audit/views.py

from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.db.models import Q
from django.shortcuts import get_object_or_404, redirect
from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _
from django.views.generic import (
    ListView, DetailView, CreateView, UpdateView, DeleteView,
    TemplateView
)
from django_fsm import can_proceed

from core.mixins import OrganizationMixin, OrganizationPermissionMixin
from core.decorators import skip_org_check
from organizations.models import Organization

from .models import AuditWorkplan, Engagement, Issue, Approval
from .forms import (
    AuditWorkplanForm, EngagementForm, IssueForm,
    ApprovalForm
)

from rest_framework import generics, permissions, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response

from .serializers import (
    AuditWorkplanSerializer, EngagementSerializer, IssueSerializer,
    ApprovalSerializer
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
        q = self.request.GET.get('q')
        if q:
            queryset = queryset.filter(Q(name__icontains=q) | Q(code__icontains=q))
        status = self.request.GET.get('status')
        if status:
            queryset = queryset.filter(status=status)
        return queryset

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
        ).prefetch_related('issues')
        q = self.request.GET.get('q')
        if q:
            queryset = queryset.filter(Q(name__icontains=q) | Q(code__icontains=q))
        status = self.request.GET.get('status')
        if status:
            queryset = queryset.filter(status=status)
        owner = self.request.GET.get('owner')
        if owner:
            queryset = queryset.filter(assigned_to__icontains=owner)
        return queryset

class EngagementDetailView(AuditPermissionMixin, DetailView):
    model = Engagement
    template_name = 'audit/engagement_detail.html'
    context_object_name = 'engagement'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        engagement = self.object
        
        # Add related data efficiently
        context.update({
            'issues': engagement.issues.all().select_related(
                'issue_owner', 'engagement'
            ),
            'approvals': engagement.approvals.all().select_related(
                'requester', 'approver'
            ),
            'can_submit': can_proceed(engagement.submit_for_approval),
            'can_approve': can_proceed(engagement.approve),
            'can_reject': can_proceed(engagement.reject),
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
    
    def form_valid(self, form):
        form.instance.organization = self.request.organization
        form.instance.created_by = self.request.user
        return super().form_valid(form)
    
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
            'engagement', 'issue_owner'
        )
        q = self.request.GET.get('q')
        if q:
            queryset = queryset.filter(Q(title__icontains=q) | Q(code__icontains=q))
        status = self.request.GET.get('status')
        if status:
            queryset = queryset.filter(status=status)
        priority = self.request.GET.get('priority')
        if priority:
            queryset = queryset.filter(priority=priority)
        return queryset

class IssueDetailView(AuditPermissionMixin, DetailView):
    model = Issue
    template_name = 'audit/issue_detail.html'
    context_object_name = 'issue'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        issue = self.object
        
        # Add related data efficiently
        context.update({
            'approvals': issue.approvals.all().select_related(
                'requester', 'approver'
            ),
        })
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
        from collections import Counter
        from django.utils import timezone
        
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
        context['engagement_status_dist'] = dict(Counter(engagement_status_dist))
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
        context['issue_severity_dist'] = dict(Counter(issue_severity_dist))
        # Workplan completion rates
        workplans = AuditWorkplan.objects.filter(organization=organization)
        completed_workplans = workplans.filter(state='completed').count()
        context['workplan_completion_rate'] = {'Completed': completed_workplans, 'Total': workplans.count()}
        # Approval status breakdown
        approvals = Approval.objects.filter(organization=organization)
        approval_status_dist = approvals.values_list('status', flat=True)
        context['approval_status_dist'] = dict(Counter(approval_status_dist))
        # Owner workload (engagements assigned)
        owner_workload = engagements.values_list('assigned_to__email', flat=True)
        context['engagement_owner_workload'] = dict(Counter(owner_workload))
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
