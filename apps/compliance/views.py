# Placeholder for compliance views

from django.urls import reverse_lazy
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView, TemplateView
from core.mixins.permissions import OrganizationPermissionMixin
from .models import (
    ComplianceFramework,
    PolicyDocument,
    DocumentProcessing,
    ComplianceRequirement,
    ComplianceObligation,
    ComplianceEvidence,
)
from .forms import (
    ComplianceFrameworkForm,
    PolicyDocumentForm,
    DocumentProcessingForm,
    ComplianceRequirementForm,
    ComplianceObligationForm,
    ComplianceEvidenceForm,
    PolicyDocumentFilterForm,
)
from django.contrib.auth.mixins import LoginRequiredMixin
from django.utils import timezone
from django.db.models import Q
from collections import Counter
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from datetime import timedelta
from django.db import models

# ComplianceFramework Views
class ComplianceFrameworkListView(OrganizationPermissionMixin, LoginRequiredMixin, ListView):
    model = ComplianceFramework
    template_name = 'compliance/complianceframework_list.html'
    context_object_name = 'object_list'
    paginate_by = 20
    def get_queryset(self):
        qs = super().get_queryset()
        q = self.request.GET.get('q')
        if q:
            qs = qs.filter(Q(name__icontains=q) | Q(version__icontains=q))
        regulatory_body = self.request.GET.get('regulatory_body')
        if regulatory_body:
            qs = qs.filter(regulatory_body__icontains=regulatory_body)
        return qs

class ComplianceFrameworkDetailView(OrganizationPermissionMixin, LoginRequiredMixin, DetailView):
    model = ComplianceFramework
    template_name = 'compliance/complianceframework_detail.html'  # TODO: create template

class ComplianceFrameworkCreateView(OrganizationPermissionMixin, LoginRequiredMixin, CreateView):
    model = ComplianceFramework
    form_class = ComplianceFrameworkForm
    template_name = 'compliance/complianceframework_form.html'  # TODO: create template
    success_url = reverse_lazy('compliance:framework_list')
    def form_valid(self, form):
        form.instance.organization = self.request.tenant
        return super().form_valid(form)
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['organization'] = self.request.tenant
        return kwargs

class ComplianceFrameworkUpdateView(OrganizationPermissionMixin, LoginRequiredMixin, UpdateView):
    model = ComplianceFramework
    form_class = ComplianceFrameworkForm
    template_name = 'compliance/complianceframework_form.html'  # TODO: create template
    success_url = reverse_lazy('compliance:framework_list')
    def form_valid(self, form):
        form.instance.organization = self.request.tenant
        return super().form_valid(form)
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['organization'] = self.request.tenant
        return kwargs

class ComplianceFrameworkDeleteView(OrganizationPermissionMixin, LoginRequiredMixin, DeleteView):
    model = ComplianceFramework
    template_name = 'compliance/complianceframework_confirm_delete.html'  # TODO: create template
    success_url = reverse_lazy('compliance:framework_list')

# PolicyDocument Views
class PolicyDocumentListView(OrganizationPermissionMixin, LoginRequiredMixin, ListView):
    model = PolicyDocument
    template_name = 'compliance/policydocument_list.html'
    context_object_name = 'object_list'
    paginate_by = 20
    def get_queryset(self):
        qs = super().get_queryset()
        qs = qs.filter(organization=self.request.tenant)
        form = PolicyDocumentFilterForm(self.request.GET)
        if form.is_valid():
            q = form.cleaned_data.get('q')
            if q:
                qs = qs.filter(Q(title__icontains=q) | Q(version__icontains=q))
            status = form.cleaned_data.get('status')
            if status == 'active':
                qs = qs.filter(is_anonymized=False)
            elif status == 'archived':
                qs = qs.filter(is_anonymized=True)
        return qs
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['filter_form'] = PolicyDocumentFilterForm(self.request.GET)
        return context

class PolicyDocumentDetailView(OrganizationPermissionMixin, LoginRequiredMixin, DetailView):
    model = PolicyDocument
    template_name = 'compliance/policydocument_detail.html'  # TODO: create template

class PolicyDocumentCreateView(OrganizationPermissionMixin, LoginRequiredMixin, CreateView):
    model = PolicyDocument
    form_class = PolicyDocumentForm
    template_name = 'compliance/policydocument_form.html'  # TODO: create template
    success_url = reverse_lazy('compliance:policydocument_list')
    def form_valid(self, form):
        form.instance.organization = self.request.tenant
        return super().form_valid(form)
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['organization'] = self.request.tenant
        return kwargs

class PolicyDocumentUpdateView(OrganizationPermissionMixin, LoginRequiredMixin, UpdateView):
    model = PolicyDocument
    form_class = PolicyDocumentForm
    template_name = 'compliance/policydocument_form.html'  # TODO: create template
    success_url = reverse_lazy('compliance:policydocument_list')
    def form_valid(self, form):
        form.instance.organization = self.request.tenant
        return super().form_valid(form)
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['organization'] = self.request.tenant
        return kwargs

class PolicyDocumentDeleteView(OrganizationPermissionMixin, LoginRequiredMixin, DeleteView):
    model = PolicyDocument
    template_name = 'compliance/policydocument_confirm_delete.html'  # TODO: create template
    success_url = reverse_lazy('compliance:list')

# DocumentProcessing Views
class DocumentProcessingListView(OrganizationPermissionMixin, LoginRequiredMixin, ListView):
    model = DocumentProcessing
    template_name = 'compliance/documentprocessing_list.html'  # TODO: create template

class DocumentProcessingDetailView(OrganizationPermissionMixin, LoginRequiredMixin, DetailView):
    model = DocumentProcessing
    template_name = 'compliance/documentprocessing_detail.html'  # TODO: create template

class DocumentProcessingCreateView(OrganizationPermissionMixin, LoginRequiredMixin, CreateView):
    model = DocumentProcessing
    form_class = DocumentProcessingForm
    template_name = 'compliance/documentprocessing_form.html'  # TODO: create template
    success_url = reverse_lazy('compliance:list')
    def form_valid(self, form):
        form.instance.organization = self.request.tenant
        return super().form_valid(form)
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['organization'] = self.request.tenant
        return kwargs

class DocumentProcessingUpdateView(OrganizationPermissionMixin, LoginRequiredMixin, UpdateView):
    model = DocumentProcessing
    form_class = DocumentProcessingForm
    template_name = 'compliance/documentprocessing_form.html'  # TODO: create template
    success_url = reverse_lazy('compliance:list')
    def form_valid(self, form):
        form.instance.organization = self.request.tenant
        return super().form_valid(form)
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['organization'] = self.request.tenant
        return kwargs

class DocumentProcessingDeleteView(OrganizationPermissionMixin, LoginRequiredMixin, DeleteView):
    model = DocumentProcessing
    template_name = 'compliance/documentprocessing_confirm_delete.html'  # TODO: create template
    success_url = reverse_lazy('compliance:documentprocessing_list')

# ComplianceRequirement Views
class ComplianceRequirementListView(OrganizationPermissionMixin, LoginRequiredMixin, ListView):
    model = ComplianceRequirement
    template_name = 'compliance/compliancerequirement_list.html'
    context_object_name = 'object_list'
    paginate_by = 20
    def get_queryset(self):
        qs = super().get_queryset()
        q = self.request.GET.get('q')
        if q:
            qs = qs.filter(Q(title__icontains=q) | Q(requirement_id__icontains=q))
        framework = self.request.GET.get('framework')
        if framework:
            qs = qs.filter(regulatory_framework__icontains=framework)
        jurisdiction = self.request.GET.get('jurisdiction')
        if jurisdiction:
            qs = qs.filter(jurisdiction__icontains=jurisdiction)
        mandatory = self.request.GET.get('mandatory')
        if mandatory == 'yes':
            qs = qs.filter(mandatory=True)
        elif mandatory == 'no':
            qs = qs.filter(mandatory=False)
        return qs

class ComplianceRequirementDetailView(OrganizationPermissionMixin, LoginRequiredMixin, DetailView):
    model = ComplianceRequirement
    template_name = 'compliance/compliancerequirement_detail.html'  # TODO: create template

class ComplianceRequirementCreateView(OrganizationPermissionMixin, LoginRequiredMixin, CreateView):
    model = ComplianceRequirement
    form_class = ComplianceRequirementForm
    template_name = 'compliance/compliancerequirement_form.html'  # TODO: create template
    success_url = reverse_lazy('compliance:requirement_list')
    def form_valid(self, form):
        form.instance.organization = self.request.tenant
        return super().form_valid(form)
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['organization'] = self.request.tenant
        return kwargs

class ComplianceRequirementUpdateView(OrganizationPermissionMixin, LoginRequiredMixin, UpdateView):
    model = ComplianceRequirement
    form_class = ComplianceRequirementForm
    template_name = 'compliance/compliancerequirement_form.html'  # TODO: create template
    success_url = reverse_lazy('compliance:requirement_list')
    def form_valid(self, form):
        form.instance.organization = self.request.tenant
        return super().form_valid(form)
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['organization'] = self.request.tenant
        return kwargs

class ComplianceRequirementDeleteView(OrganizationPermissionMixin, LoginRequiredMixin, DeleteView):
    model = ComplianceRequirement
    template_name = 'compliance/compliancerequirement_confirm_delete.html'  # TODO: create template
    success_url = reverse_lazy('compliance:requirement_list')

# ComplianceObligation Views
class ComplianceObligationListView(OrganizationPermissionMixin, LoginRequiredMixin, ListView):
    model = ComplianceObligation
    template_name = 'compliance/complianceobligation_list.html'
    context_object_name = 'object_list'
    paginate_by = 20
    def get_queryset(self):
        qs = super().get_queryset()
        requirement = self.request.GET.get('requirement')
        if requirement:
            qs = qs.filter(requirement__title__icontains=requirement)
        owner = self.request.GET.get('owner')
        if owner:
            qs = qs.filter(Q(owner__icontains=owner) | Q(owner_email__icontains=owner))
        status = self.request.GET.get('status')
        if status:
            qs = qs.filter(status=status)
        priority = self.request.GET.get('priority')
        if priority:
            qs = qs.filter(priority=priority)
        return qs

class ComplianceObligationDetailView(OrganizationPermissionMixin, LoginRequiredMixin, DetailView):
    model = ComplianceObligation
    template_name = 'compliance/complianceobligation_detail.html'  # TODO: create template

class ComplianceObligationCreateView(OrganizationPermissionMixin, LoginRequiredMixin, CreateView):
    model = ComplianceObligation
    form_class = ComplianceObligationForm
    template_name = 'compliance/complianceobligation_form.html'  # TODO: create template
    success_url = reverse_lazy('compliance:obligation_list')
    def form_valid(self, form):
        form.instance.organization = self.request.tenant
        return super().form_valid(form)
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['organization'] = self.request.tenant
        return kwargs

class ComplianceObligationUpdateView(OrganizationPermissionMixin, LoginRequiredMixin, UpdateView):
    model = ComplianceObligation
    form_class = ComplianceObligationForm
    template_name = 'compliance/complianceobligation_form.html'  # TODO: create template
    success_url = reverse_lazy('compliance:obligation_list')
    def form_valid(self, form):
        form.instance.organization = self.request.tenant
        return super().form_valid(form)
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['organization'] = self.request.tenant
        return kwargs

class ComplianceObligationDeleteView(OrganizationPermissionMixin, LoginRequiredMixin, DeleteView):
    model = ComplianceObligation
    template_name = 'compliance/complianceobligation_confirm_delete.html'  # TODO: create template
    success_url = reverse_lazy('compliance:obligation_list')

# ComplianceEvidence Views
class ComplianceEvidenceListView(OrganizationPermissionMixin, LoginRequiredMixin, ListView):
    model = ComplianceEvidence
    template_name = 'compliance/complianceevidence_list.html'
    context_object_name = 'object_list'
    paginate_by = 20
    def get_queryset(self):
        qs = super().get_queryset()
        obligation = self.request.GET.get('obligation')
        if obligation:
            qs = qs.filter(obligation__icontains=obligation)
        document = self.request.GET.get('document')
        if document:
            qs = qs.filter(document__icontains=document)
        validity_start = self.request.GET.get('validity_start')
        if validity_start:
            qs = qs.filter(validity_start__gte=validity_start)
        validity_end = self.request.GET.get('validity_end')
        if validity_end:
            qs = qs.filter(validity_end__lte=validity_end)
        return qs

class ComplianceEvidenceDetailView(OrganizationPermissionMixin, LoginRequiredMixin, DetailView):
    model = ComplianceEvidence
    template_name = 'compliance/complianceevidence_detail.html'  # TODO: create template

class ComplianceEvidenceCreateView(OrganizationPermissionMixin, LoginRequiredMixin, CreateView):
    model = ComplianceEvidence
    form_class = ComplianceEvidenceForm
    template_name = 'compliance/complianceevidence_form.html'  # TODO: create template
    success_url = reverse_lazy('compliance:evidence_list')
    def form_valid(self, form):
        form.instance.organization = self.request.tenant
        return super().form_valid(form)
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['organization'] = self.request.tenant
        return kwargs

class ComplianceEvidenceUpdateView(OrganizationPermissionMixin, LoginRequiredMixin, UpdateView):
    model = ComplianceEvidence
    form_class = ComplianceEvidenceForm
    template_name = 'compliance/complianceevidence_form.html'  # TODO: create template
    success_url = reverse_lazy('compliance:evidence_list')
    def form_valid(self, form):
        form.instance.organization = self.request.tenant
        return super().form_valid(form)
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['organization'] = self.request.tenant
        return kwargs

class ComplianceEvidenceDeleteView(OrganizationPermissionMixin, LoginRequiredMixin, DeleteView):
    model = ComplianceEvidence
    template_name = 'compliance/complianceevidence_confirm_delete.html'  # TODO: create template
    success_url = reverse_lazy('compliance:evidence_list')

class ComplianceDashboardView(OrganizationPermissionMixin, LoginRequiredMixin, TemplateView):
    template_name = 'compliance/dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        org = self.request.tenant
        
        # Basic counts
        context['framework_count'] = ComplianceFramework.objects.filter(organization=org).count()
        context['requirement_count'] = ComplianceRequirement.objects.filter(organization=org).count()
        context['obligation_count'] = ComplianceObligation.objects.filter(organization=org).count()
        context['evidence_count'] = ComplianceEvidence.objects.filter(organization=org).count()
        context['policydocument_count'] = PolicyDocument.objects.filter(organization=org).count()

        # Advanced analytics: Requirement counts by framework, jurisdiction, mandatory
        framework_dist = ComplianceRequirement.objects.filter(organization=org).values_list('regulatory_framework__name', flat=True)
        framework_counter = Counter(framework_dist)
        context['requirement_framework_dist'] = dict(framework_counter) or {'General': 0}
        
        # Jurisdiction distribution
        jurisdiction_qs = ComplianceRequirement.objects.filter(organization=org).values_list('jurisdiction', flat=True)
        jurisdiction_counter = Counter(jurisdiction_qs)
        context['requirement_jurisdiction_chart'] = dict(jurisdiction_counter) or {'General': 0}
        
        # Mandatory vs Optional distribution
        mandatory_dist = ComplianceRequirement.objects.filter(organization=org).values_list('mandatory', flat=True)
        mandatory_count = sum(1 for m in mandatory_dist if m)
        optional_count = sum(1 for m in mandatory_dist if not m)
        context['requirement_mandatory_dist'] = {'Mandatory': mandatory_count, 'Optional': optional_count}

        # Obligation overdue vs. on-time, completion rates, owner workload
        obligations = ComplianceObligation.objects.filter(organization=org)
        today = timezone.now().date()
        
        # Overdue obligations (status is open/in_progress and due_date is past)
        overdue_count = obligations.filter(
            status__in=['open', 'in_progress'], 
            due_date__lt=today
        ).count()
        
        # On-time obligations (status is completed and due_date is in future or today)
        ontime_count = obligations.filter(
            status='completed', 
            due_date__gte=today
        ).count()
        
        context['obligation_overdue_ontime'] = {
            'Overdue': overdue_count, 
            'On Time': ontime_count
        } if (overdue_count or ontime_count) else {'Overdue': 0, 'On Time': 0}
        
        # Completion rates
        completed_count = obligations.filter(status='completed').count()
        total_obligations = obligations.count()
        context['obligation_completion_rate'] = {
            'Completed': completed_count, 
            'Total': total_obligations
        }
        
        # Owner workload
        owner_workload = obligations.values_list('owner__email', flat=True)
        owner_counter = Counter(owner_workload)
        context['obligation_owner_workload'] = dict(owner_counter) or {'No Owner': 0}

        # Policy document expiry distribution
        expiring_soon = PolicyDocument.objects.filter(
            organization=org, 
            expiration_date__gte=today, 
            expiration_date__lte=today.replace(year=today.year+1)
        ).count()
        expired = PolicyDocument.objects.filter(
            organization=org, 
            expiration_date__lt=today
        ).count()
        no_expiry = PolicyDocument.objects.filter(
            organization=org, 
            expiration_date__isnull=True
        ).count()
        
        context['policy_expiry_dist'] = {
            'Expiring Soon': expiring_soon, 
            'Expired': expired, 
            'No Expiry': no_expiry
        } if (expiring_soon or expired or no_expiry) else {
            'Expiring Soon': 0, 
            'Expired': 0, 
            'No Expiry': 0
        }

        # Recent activity: last 10 created/updated items from all main models
        recent = []
        for model, label, icon in [
            (ComplianceFramework, 'Framework', 'bi-diagram-3'),
            (ComplianceRequirement, 'Requirement', 'bi-list-check'),
            (ComplianceObligation, 'Obligation', 'bi-flag'),
            (ComplianceEvidence, 'Evidence', 'bi-file-earmark-check'),
            (PolicyDocument, 'Policy Document', 'bi-file-earmark-text'),
        ]:
            for obj in model.objects.filter(organization=org).order_by('-updated_at')[:3]:
                recent.append({
                    'message': f"{label}: {getattr(obj, 'title', getattr(obj, 'name', getattr(obj, 'requirement_id', getattr(obj, 'obligation_id', ''))))}",
                    'timestamp': getattr(obj, 'updated_at', timezone.now()),
                    'icon': icon,
                })
        
        # Sort by timestamp, most recent first, and limit to 10
        context['recent_activity'] = sorted(recent, key=lambda x: x['timestamp'], reverse=True)[:10]
        
        return context

# ─── REPORTS VIEW ────────────────────────────────────────────────────────────
class ComplianceReportsView(OrganizationPermissionMixin, LoginRequiredMixin, TemplateView):
    template_name = 'compliance/reports.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        organization = self.request.organization
        
        # Get framework names for filters
        frameworks = ComplianceFramework.objects.filter(organization=organization).values_list('name', flat=True).distinct()
        context['frameworks'] = sorted(list(frameworks))
        
        # Get requirement jurisdictions for filters
        jurisdictions = ComplianceRequirement.objects.filter(organization=organization).values_list('jurisdiction', flat=True).distinct()
        context['jurisdictions'] = sorted(list(jurisdictions))
        
        # Get obligation statuses for filters
        obligation_statuses = ComplianceObligation.objects.filter(organization=organization).values_list('status', flat=True).distinct()
        context['obligation_statuses'] = sorted(list(obligation_statuses))
        
        # Get obligation owners for filters
        obligation_owners = ComplianceObligation.objects.filter(organization=organization).values_list('owner__email', flat=True).distinct()
        context['obligation_owners'] = sorted(list(obligation_owners))
        
        # Get evidence types for filters (using document titles instead since evidence_type doesn't exist)
        evidence_documents = ComplianceEvidence.objects.filter(organization=organization).values_list('document__title', flat=True).distinct()
        context['evidence_types'] = sorted(list(evidence_documents))
        
        # Get policy document titles for filters (since PolicyDocument doesn't have a status field)
        policy_titles = PolicyDocument.objects.filter(organization=organization).values_list('title', flat=True).distinct()
        context['policy_statuses'] = sorted(list(policy_titles))
        
        return context

@login_required
def api_framework_data(request):
    org = request.user.organization
    from .models import ComplianceFramework
    from django.db.models import Count
    framework_qs = ComplianceFramework.objects.filter(organization=org).values('name').annotate(count=Count('id'))
    framework_data = {s['name']: s['count'] for s in framework_qs}
    return JsonResponse(framework_data, safe=False)

@login_required
def api_obligation_data(request):
    org = request.user.organization
    from .models import ComplianceObligation
    from django.db.models import Count
    obligation_qs = ComplianceObligation.objects.filter(organization=org).values('status').annotate(count=Count('id'))
    obligation_data = {s['status']: s['count'] for s in obligation_qs}
    return JsonResponse(obligation_data, safe=False)

@login_required
def api_policy_expiry_data(request):
    """API endpoint for policy expiry data used in dashboards."""
    today = timezone.now().date()
    policies = PolicyDocument.objects.filter(organization=request.user.organization)
    
    data = {
        'expired': policies.filter(expiration_date__lt=today).count(),
        'expiring_30_days': policies.filter(
            expiration_date__gte=today,
            expiration_date__lte=today + timedelta(days=30)
        ).count(),
        'expiring_90_days': policies.filter(
            expiration_date__gte=today,
            expiration_date__lte=today + timedelta(days=90)
        ).count(),
        'valid': policies.filter(
            models.Q(expiration_date__gt=today) | models.Q(expiration_date__isnull=True)
        ).count(),
    }
    return JsonResponse(data)
