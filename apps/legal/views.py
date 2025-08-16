from django.urls import reverse_lazy
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView, TemplateView
from core.mixins.permissions import OrganizationPermissionMixin
from .models import CaseType, LegalParty, LegalCase, CaseParty, LegalTask, LegalDocument, LegalArchive
from .forms import (
    CaseTypeForm, LegalPartyForm, LegalCaseForm, CasePartyForm,
    LegalTaskForm, LegalDocumentForm, LegalArchiveForm
)
from django.contrib.auth.mixins import LoginRequiredMixin
from django.shortcuts import render
from django.utils import timezone
from django.db.models import Q
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required

# CaseType Views
class CaseTypeListView(OrganizationPermissionMixin, ListView):
    model = CaseType
    template_name = 'legal/casetype_list.html'
    def get_queryset(self):
        org = self.request.tenant if hasattr(self.request, 'tenant') else self.request.user.organization
        return CaseType.objects.filter(organization=org)

class CaseTypeDetailView(OrganizationPermissionMixin, DetailView):
    model = CaseType
    template_name = 'legal/casetype_detail.html'
    def get_queryset(self):
        org = self.request.tenant if hasattr(self.request, 'tenant') else self.request.user.organization
        return CaseType.objects.filter(organization=org)

class CaseTypeCreateView(OrganizationPermissionMixin, CreateView):
    model = CaseType
    form_class = CaseTypeForm
    template_name = 'legal/casetype_form.html'
    success_url = reverse_lazy('legal:casetype_list')

    def form_valid(self, form):
        # Set organization automatically
        form.instance.organization = self.request.tenant if hasattr(self.request, 'tenant') else self.request.user.organization
        return super().form_valid(form)

class CaseTypeUpdateView(OrganizationPermissionMixin, UpdateView):
    model = CaseType
    form_class = CaseTypeForm
    template_name = 'legal/casetype_form.html'
    success_url = reverse_lazy('legal:casetype_list')

class CaseTypeDeleteView(OrganizationPermissionMixin, DeleteView):
    model = CaseType
    template_name = 'legal/casetype_confirm_delete.html'
    success_url = reverse_lazy('legal:casetype_list')

# LegalParty Views
class LegalPartyListView(OrganizationPermissionMixin, ListView):
    model = LegalParty
    template_name = 'legal/legalparty_list.html'
    context_object_name = 'object_list'
    paginate_by = 20
    def get_queryset(self):
        qs = super().get_queryset()
        q = self.request.GET.get('q')
        if q:
            qs = qs.filter(name__icontains=q)
        party_type = self.request.GET.get('type')
        if party_type:
            qs = qs.filter(party_type__icontains=party_type)
        role = self.request.GET.get('role')
        if role:
            qs = qs.filter(role__icontains=role)
        return qs

class LegalPartyDetailView(OrganizationPermissionMixin, DetailView):
    model = LegalParty
    template_name = 'legal/legalparty_detail.html'

class LegalPartyCreateView(OrganizationPermissionMixin, CreateView):
    model = LegalParty
    form_class = LegalPartyForm
    template_name = 'legal/legalparty_form.html'
    success_url = reverse_lazy('legal:legalparty_list')

    def form_valid(self, form):
        # Set organization as ForeignKey
        form.instance.organization = self.request.tenant if hasattr(self.request, 'tenant') else self.request.user.organization
        return super().form_valid(form)

class LegalPartyUpdateView(OrganizationPermissionMixin, UpdateView):
    model = LegalParty
    form_class = LegalPartyForm
    template_name = 'legal/legalparty_form.html'
    success_url = reverse_lazy('legal:legalparty_list')

    def form_valid(self, form):
        # Set organization as ForeignKey
        form.instance.organization = self.request.tenant if hasattr(self.request, 'tenant') else self.request.user.organization
        return super().form_valid(form)

class LegalPartyDeleteView(OrganizationPermissionMixin, DeleteView):
    model = LegalParty
    template_name = 'legal/legalparty_confirm_delete.html'
    success_url = reverse_lazy('legal:legalparty_list')

# LegalCase Views
class LegalCaseListView(OrganizationPermissionMixin, ListView):
    model = LegalCase
    template_name = 'legal/legalcase_list.html'
    context_object_name = 'object_list'
    paginate_by = 20
    def get_queryset(self):
        qs = super().get_queryset()
        q = self.request.GET.get('q')
        if q:
            qs = qs.filter(Q(title__icontains=q) | Q(lead_attorney__icontains=q))
        case_type = self.request.GET.get('type')
        if case_type:
            qs = qs.filter(case_type__icontains=case_type)
        status = self.request.GET.get('status')
        if status:
            qs = qs.filter(status=status)
        priority = self.request.GET.get('priority')
        if priority:
            qs = qs.filter(priority=priority)
        return qs

class LegalCaseDetailView(OrganizationPermissionMixin, DetailView):
    model = LegalCase
    template_name = 'legal/legalcase_detail.html'

class LegalCaseCreateView(OrganizationPermissionMixin, CreateView):
    model = LegalCase
    form_class = LegalCaseForm
    template_name = 'legal/legalcase_form.html'
    success_url = reverse_lazy('legal:legalcase_list')

    def form_valid(self, form):
        form.instance.organization = self.request.user.organization
        return super().form_valid(form)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['organization'] = self.request.user.organization
        return kwargs

class LegalCaseUpdateView(OrganizationPermissionMixin, UpdateView):
    model = LegalCase
    form_class = LegalCaseForm
    template_name = 'legal/legalcase_form.html'
    success_url = reverse_lazy('legal:legalcase_list')

    def form_valid(self, form):
        form.instance.organization = self.request.user.organization
        return super().form_valid(form)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['organization'] = self.request.user.organization
        return kwargs

class LegalCaseDeleteView(OrganizationPermissionMixin, DeleteView):
    model = LegalCase
    template_name = 'legal/legalcase_confirm_delete.html'
    success_url = reverse_lazy('legal:legalcase_list')

# CaseParty Views
class CasePartyListView(OrganizationPermissionMixin, ListView):
    model = CaseParty
    template_name = 'legal/caseparty_list.html'

class CasePartyDetailView(OrganizationPermissionMixin, DetailView):
    model = CaseParty
    template_name = 'legal/caseparty_detail.html'

class CasePartyCreateView(OrganizationPermissionMixin, CreateView):
    model = CaseParty
    form_class = CasePartyForm
    template_name = 'legal/caseparty_form.html'
    success_url = reverse_lazy('legal:caseparty_list')

class CasePartyUpdateView(OrganizationPermissionMixin, UpdateView):
    model = CaseParty
    form_class = CasePartyForm
    template_name = 'legal/caseparty_form.html'
    success_url = reverse_lazy('legal:caseparty_list')

class CasePartyDeleteView(OrganizationPermissionMixin, DeleteView):
    model = CaseParty
    template_name = 'legal/caseparty_confirm_delete.html'
    success_url = reverse_lazy('legal:caseparty_list')

# LegalTask Views
class LegalTaskListView(OrganizationPermissionMixin, ListView):
    model = LegalTask
    template_name = 'legal/legaltask_list.html'
    context_object_name = 'object_list'
    paginate_by = 20
    def get_queryset(self):
        qs = super().get_queryset()
        q = self.request.GET.get('q')
        if q:
            qs = qs.filter(Q(title__icontains=q) | Q(legal_case__title__icontains=q))
        assigned_to = self.request.GET.get('assigned_to')
        if assigned_to:
            qs = qs.filter(assigned_to__icontains=assigned_to)
        status = self.request.GET.get('status')
        if status:
            qs = qs.filter(status=status)
        return qs

class LegalTaskDetailView(OrganizationPermissionMixin, DetailView):
    model = LegalTask
    template_name = 'legal/legaltask_detail.html'

class LegalTaskCreateView(OrganizationPermissionMixin, CreateView):
    model = LegalTask
    form_class = LegalTaskForm
    template_name = 'legal/legaltask_form.html'
    success_url = reverse_lazy('legal:legaltask_list')

    def form_valid(self, form):
        form.instance.organization = self.request.user.organization
        return super().form_valid(form)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['organization'] = self.request.user.organization
        return kwargs

class LegalTaskUpdateView(OrganizationPermissionMixin, UpdateView):
    model = LegalTask
    form_class = LegalTaskForm
    template_name = 'legal/legaltask_form.html'
    success_url = reverse_lazy('legal:legaltask_list')

    def form_valid(self, form):
        form.instance.organization = self.request.user.organization
        return super().form_valid(form)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['organization'] = self.request.user.organization
        return kwargs

class LegalTaskDeleteView(OrganizationPermissionMixin, DeleteView):
    model = LegalTask
    template_name = 'legal/legaltask_confirm_delete.html'
    success_url = reverse_lazy('legal:legaltask_list')

# LegalDocument Views
class LegalDocumentListView(OrganizationPermissionMixin, ListView):
    model = LegalDocument
    template_name = 'legal/legaldocument_list.html'
    context_object_name = 'object_list'
    paginate_by = 20
    def get_queryset(self):
        qs = super().get_queryset()
        q = self.request.GET.get('q')
        if q:
            qs = qs.filter(Q(title__icontains=q) | Q(legal_case__title__icontains=q))
        doc_type = self.request.GET.get('type')
        if doc_type:
            qs = qs.filter(document_type__icontains=doc_type)
        uploaded_by = self.request.GET.get('uploaded_by')
        if uploaded_by:
            qs = qs.filter(uploaded_by__icontains=uploaded_by)
        return qs

class LegalDocumentDetailView(OrganizationPermissionMixin, DetailView):
    model = LegalDocument
    template_name = 'legal/legaldocument_detail.html'

class LegalDocumentCreateView(OrganizationPermissionMixin, CreateView):
    model = LegalDocument
    form_class = LegalDocumentForm
    template_name = 'legal/legaldocument_form.html'
    success_url = reverse_lazy('legal:legaldocument_list')

    def form_valid(self, form):
        form.instance.organization = self.request.user.organization
        return super().form_valid(form)

class LegalDocumentUpdateView(OrganizationPermissionMixin, UpdateView):
    model = LegalDocument
    form_class = LegalDocumentForm
    template_name = 'legal/legaldocument_form.html'
    success_url = reverse_lazy('legal:legaldocument_list')

    def form_valid(self, form):
        form.instance.organization = self.request.user.organization
        return super().form_valid(form)

class LegalDocumentDeleteView(OrganizationPermissionMixin, DeleteView):
    model = LegalDocument
    template_name = 'legal/legaldocument_confirm_delete.html'
    success_url = reverse_lazy('legal:legaldocument_list')

# LegalArchive Views
class LegalArchiveListView(OrganizationPermissionMixin, ListView):
    model = LegalArchive
    template_name = 'legal/legalarchive_list.html'

class LegalArchiveDetailView(OrganizationPermissionMixin, DetailView):
    model = LegalArchive
    template_name = 'legal/legalarchive_detail.html'

class LegalArchiveCreateView(OrganizationPermissionMixin, CreateView):
    model = LegalArchive
    form_class = LegalArchiveForm
    template_name = 'legal/legalarchive_form.html'
    success_url = reverse_lazy('legal:legalarchive_list')

    def form_valid(self, form):
        form.instance.organization = self.request.user.organization
        return super().form_valid(form)

class LegalArchiveUpdateView(OrganizationPermissionMixin, UpdateView):
    model = LegalArchive
    form_class = LegalArchiveForm
    template_name = 'legal/legalarchive_form.html'
    success_url = reverse_lazy('legal:legalarchive_list')

    def form_valid(self, form):
        form.instance.organization = self.request.user.organization
        return super().form_valid(form)

class LegalArchiveDeleteView(OrganizationPermissionMixin, DeleteView):
    model = LegalArchive
    template_name = 'legal/legalarchive_confirm_delete.html'
    success_url = reverse_lazy('legal:legalarchive_list')

class LegalDashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'legal/dashboard.html'
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Robust fallback for organization context
        org = getattr(self.request, 'organization', None) or getattr(self.request.user, 'organization', None)
        if not org:
            context['dashboard_error'] = 'Organization context is missing. Please contact support.'
            # Set all variables to safe defaults
            context['case_count'] = context['party_count'] = context['document_count'] = context['task_count'] = 0
            context['overdue_tasks'] = context['completed_tasks'] = context['pending_tasks'] = 0
            context['recent_cases'] = context['recent_documents'] = context['recent_tasks'] = []
            context['case_status_chart'] = {'Open': 0, 'Closed': 0, 'Archived': 0}
            context['task_status_chart'] = {'Completed': 0, 'Pending': 0, 'Overdue': 0}
            return context
        
        # Case counts
        context['case_count'] = LegalCase.objects.filter(organization=org).count()
        context['open_cases'] = LegalCase.objects.filter(organization=org, status='intake').count() + \
                                 LegalCase.objects.filter(organization=org, status='investigation').count() + \
                                 LegalCase.objects.filter(organization=org, status='litigation').count() + \
                                 LegalCase.objects.filter(organization=org, status='settlement_negotiation').count()
        context['closed_cases'] = LegalCase.objects.filter(organization=org, status='closed').count()
        context['archived_cases'] = LegalCase.objects.filter(organization=org, status='archived').count()
        
        # Party, document, task counts
        context['party_count'] = LegalParty.objects.filter(organization=org).count()
        context['document_count'] = LegalDocument.objects.filter(organization=org).count()
        context['task_count'] = LegalTask.objects.filter(organization=org).count()
        
        # Overdue tasks: status is 'overdue'
        context['overdue_tasks'] = LegalTask.objects.filter(organization=org, status='overdue').count()
        
        # Task status chart data
        context['completed_tasks'] = LegalTask.objects.filter(organization=org, status='completed').count()
        context['pending_tasks'] = LegalTask.objects.filter(organization=org, status='pending').count() + \
                                   LegalTask.objects.filter(organization=org, status='in_progress').count()
        
        # Recent activity (latest 8 cases, documents, or tasks)
        context['recent_cases'] = LegalCase.objects.filter(organization=org).order_by('-created_at')[:4]
        context['recent_documents'] = LegalDocument.objects.filter(organization=org).order_by('-id')[:2]
        context['recent_tasks'] = LegalTask.objects.filter(organization=org).order_by('-id')[:2]
        
        # Chart data for Plotly - Case Status Distribution
        from collections import Counter
        case_status_qs = LegalCase.objects.filter(organization=org).values_list('status', flat=True)
        case_status_counter = Counter(case_status_qs)
        # Map status values to display names
        status_mapping = {
            'intake': 'Open',
            'investigation': 'Open', 
            'litigation': 'Open',
            'settlement_negotiation': 'Open',
            'closed': 'Closed',
            'archived': 'Archived'
        }
        case_status_chart = {}
        for status, count in case_status_counter.items():
            display_name = status_mapping.get(status, status.title())
            if display_name in case_status_chart:
                case_status_chart[display_name] += count
            else:
                case_status_chart[display_name] = count
        context['case_status_chart'] = case_status_chart or {'Open': 0, 'Closed': 0, 'Archived': 0}
        
        # Task Status Distribution
        task_status_qs = LegalTask.objects.filter(organization=org).values_list('status', flat=True)
        task_status_counter = Counter(task_status_qs)
        # Map task status values to display names
        task_status_mapping = {
            'pending': 'Pending',
            'in_progress': 'In Progress',
            'completed': 'Completed',
            'overdue': 'Overdue'
        }
        task_status_chart = {}
        for status, count in task_status_counter.items():
            display_name = task_status_mapping.get(status, status.title())
            task_status_chart[display_name] = count
        context['task_status_chart'] = task_status_chart or {'Pending': 0, 'In Progress': 0, 'Completed': 0, 'Overdue': 0}
        
        return context

@login_required
def api_case_status_data(request):
    org = request.user.organization
    from .models import LegalCase
    from django.db.models import Count
    status_qs = LegalCase.objects.filter(organization=org).values('status').annotate(count=Count('id'))
    status_data = {s['status']: s['count'] for s in status_qs}
    return JsonResponse(status_data, safe=False)

@login_required
def api_task_status_data(request):
    org = request.user.organization
    from .models import LegalTask
    from django.db.models import Count
    task_qs = LegalTask.objects.filter(organization=org).values('status').annotate(count=Count('id'))
    task_data = {s['status']: s['count'] for s in task_qs}
    return JsonResponse(task_data, safe=False) 