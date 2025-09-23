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
from users.models import CustomUser

# CaseType Views
class CaseTypeListView(OrganizationPermissionMixin, ListView):
    model = CaseType
    template_name = 'legal/casetype_list.html'
    def get_queryset(self):
        return super().get_queryset().filter(organization=self.request.organization)

class CaseTypeDetailView(OrganizationPermissionMixin, DetailView):
    model = CaseType
    template_name = 'legal/casetype_detail.html'
    def get_queryset(self):
        return super().get_queryset().filter(organization=self.request.organization)

class CaseTypeCreateView(OrganizationPermissionMixin, CreateView):
    model = CaseType
    form_class = CaseTypeForm
    template_name = 'legal/casetype_form.html'
    success_url = reverse_lazy('legal:casetype_list')

    def form_valid(self, form):
        # Set organization automatically
        form.instance.organization = self.request.organization
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
        qs = super().get_queryset().filter(organization=self.request.organization)
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
    
    def get_queryset(self):
        return super().get_queryset().filter(organization=self.request.organization)

class LegalPartyCreateView(OrganizationPermissionMixin, CreateView):
    model = LegalParty
    form_class = LegalPartyForm
    template_name = 'legal/legalparty_form.html'
    success_url = reverse_lazy('legal:legalparty_list')

    def form_valid(self, form):
        # Set organization as ForeignKey
        form.instance.organization = self.request.organization
        return super().form_valid(form)

class LegalPartyUpdateView(OrganizationPermissionMixin, UpdateView):
    model = LegalParty
    form_class = LegalPartyForm
    template_name = 'legal/legalparty_form.html'
    success_url = reverse_lazy('legal:legalparty_list')

    def form_valid(self, form):
        # Set organization as ForeignKey
        form.instance.organization = self.request.organization
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
        qs = super().get_queryset().filter(organization=self.request.organization)
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
    
    def get_queryset(self):
        return super().get_queryset().filter(organization=self.request.organization)

class LegalCaseCreateView(OrganizationPermissionMixin, CreateView):
    model = LegalCase
    form_class = LegalCaseForm
    template_name = 'legal/legalcase_form.html'
    success_url = reverse_lazy('legal:legalcase_list')

    def form_valid(self, form):
        form.instance.organization = self.request.organization
        return super().form_valid(form)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['organization'] = self.request.organization
        return kwargs

class LegalCaseUpdateView(OrganizationPermissionMixin, UpdateView):
    model = LegalCase
    form_class = LegalCaseForm
    template_name = 'legal/legalcase_form.html'
    success_url = reverse_lazy('legal:legalcase_list')

    def form_valid(self, form):
        form.instance.organization = self.request.organization
        return super().form_valid(form)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['organization'] = self.request.organization
        return kwargs

class LegalCaseDeleteView(OrganizationPermissionMixin, DeleteView):
    model = LegalCase
    template_name = 'legal/legalcase_confirm_delete.html'
    success_url = reverse_lazy('legal:legalcase_list')

# CaseParty Views
class CasePartyListView(OrganizationPermissionMixin, ListView):
    model = CaseParty
    template_name = 'legal/caseparty_list.html'
    
    def get_queryset(self):
        return super().get_queryset().filter(case__organization=self.request.organization)

class CasePartyDetailView(OrganizationPermissionMixin, DetailView):
    model = CaseParty
    template_name = 'legal/caseparty_detail.html'
    
    def get_queryset(self):
        return super().get_queryset().filter(case__organization=self.request.organization)

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
        qs = super().get_queryset().filter(organization=self.request.organization)
        q = self.request.GET.get('q')
        if q:
            qs = qs.filter(Q(title__icontains=q) | Q(case__title__icontains=q))
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
    
    def get_queryset(self):
        return super().get_queryset().filter(organization=self.request.organization)

class LegalTaskCreateView(OrganizationPermissionMixin, CreateView):
    model = LegalTask
    form_class = LegalTaskForm
    template_name = 'legal/legaltask_form.html'
    success_url = reverse_lazy('legal:legaltask_list')

    def form_valid(self, form):
        form.instance.organization = self.request.organization
        return super().form_valid(form)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['organization'] = self.request.organization
        return kwargs

class LegalTaskUpdateView(OrganizationPermissionMixin, UpdateView):
    model = LegalTask
    form_class = LegalTaskForm
    template_name = 'legal/legaltask_form.html'
    success_url = reverse_lazy('legal:legaltask_list')

    def form_valid(self, form):
        form.instance.organization = self.request.organization
        return super().form_valid(form)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['organization'] = self.request.organization
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
        qs = super().get_queryset().filter(organization=self.request.organization)
        q = self.request.GET.get('q')
        if q:
            qs = qs.filter(Q(title__icontains=q) | Q(case__title__icontains=q))
        case_filter = self.request.GET.get('case')
        if case_filter:
            qs = qs.filter(case__title__icontains=case_filter)
        is_confidential = self.request.GET.get('is_confidential')
        if is_confidential:
            qs = qs.filter(is_confidential=is_confidential.lower() == 'true')
        return qs

class LegalDocumentDetailView(OrganizationPermissionMixin, DetailView):
    model = LegalDocument
    template_name = 'legal/legaldocument_detail.html'
    
    def get_queryset(self):
        return super().get_queryset().filter(organization=self.request.organization)

class LegalDocumentCreateView(OrganizationPermissionMixin, CreateView):
    model = LegalDocument
    form_class = LegalDocumentForm
    template_name = 'legal/legaldocument_form.html'
    success_url = reverse_lazy('legal:legaldocument_list')

    def form_valid(self, form):
        form.instance.organization = self.request.organization
        return super().form_valid(form)

class LegalDocumentUpdateView(OrganizationPermissionMixin, UpdateView):
    model = LegalDocument
    form_class = LegalDocumentForm
    template_name = 'legal/legaldocument_form.html'
    success_url = reverse_lazy('legal:legaldocument_list')

    def form_valid(self, form):
        form.instance.organization = self.request.organization
        return super().form_valid(form)

class LegalDocumentDeleteView(OrganizationPermissionMixin, DeleteView):
    model = LegalDocument
    template_name = 'legal/legaldocument_confirm_delete.html'
    success_url = reverse_lazy('legal:legaldocument_list')

# LegalArchive Views
class LegalArchiveListView(OrganizationPermissionMixin, ListView):
    model = LegalArchive
    template_name = 'legal/legalarchive_list.html'
    
    def get_queryset(self):
        return super().get_queryset().filter(organization=self.request.organization)

class LegalArchiveDetailView(OrganizationPermissionMixin, DetailView):
    model = LegalArchive
    template_name = 'legal/legalarchive_detail.html'
    
    def get_queryset(self):
        return super().get_queryset().filter(organization=self.request.organization)

class LegalArchiveCreateView(OrganizationPermissionMixin, CreateView):
    model = LegalArchive
    form_class = LegalArchiveForm
    template_name = 'legal/legalarchive_form.html'
    success_url = reverse_lazy('legal:legalarchive_list')

    def form_valid(self, form):
        form.instance.organization = self.request.organization
        return super().form_valid(form)

class LegalArchiveUpdateView(OrganizationPermissionMixin, UpdateView):
    model = LegalArchive
    form_class = LegalArchiveForm
    template_name = 'legal/legalarchive_form.html'
    success_url = reverse_lazy('legal:legalarchive_list')

    def form_valid(self, form):
        form.instance.organization = self.request.organization
        return super().form_valid(form)

class LegalArchiveDeleteView(OrganizationPermissionMixin, DeleteView):
    model = LegalArchive
    template_name = 'legal/legalarchive_confirm_delete.html'
    success_url = reverse_lazy('legal:legalarchive_list')

class LegalDashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'legal/dashboard.html'
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        # Use organization from request
        org = self.request.organization
        if not org:
            context['dashboard_error'] = 'Organization context is missing. Please contact support.'
            # Set all variables to safe defaults
            context['case_count'] = context['party_count'] = context['document_count'] = context['task_count'] = 0
            context['overdue_tasks'] = context['completed_tasks'] = context['pending_tasks'] = 0
            context['recent_cases'] = context['recent_documents'] = context['recent_tasks'] = []
            context['case_status_chart'] = {'Open': 0, 'Closed': 0, 'Archived': 0}
            context['task_status_chart'] = {'Completed': 0, 'Pending': 0, 'Overdue': 0}
            return context
        
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

        case_qs = LegalCase.objects.filter(organization=org)
        if not filter_all:
            cq = Q(created_at__year__in=year_ints)
            if month_ints:
                cq &= Q(created_at__month__in=month_ints)
            case_qs = case_qs.filter(cq)

        # Case counts
        context['case_count'] = case_qs.count()
        context['open_cases'] = LegalCase.objects.filter(organization=org, status='intake').count() + \
                                 LegalCase.objects.filter(organization=org, status='investigation').count() + \
                                 LegalCase.objects.filter(organization=org, status='litigation').count() + \
                                 LegalCase.objects.filter(organization=org, status='settlement_negotiation').count()
        context['closed_cases'] = case_qs.filter(status='closed').count()
        context['archived_cases'] = case_qs.filter(status='archived').count()
        
        # Party, document, task counts
        party_qs = LegalParty.objects.filter(organization=org)
        doc_qs = LegalDocument.objects.filter(organization=org)
        task_qs = LegalTask.objects.filter(organization=org)
        if not filter_all:
            if month_ints:
                task_qs = task_qs.filter(created_at__year__in=year_ints, created_at__month__in=month_ints)
                doc_qs = doc_qs.filter(id__isnull=False)  # no date field; keep unfiltered safely
            else:
                task_qs = task_qs.filter(created_at__year__in=year_ints)
        context['party_count'] = party_qs.count()
        context['document_count'] = doc_qs.count()
        context['task_count'] = task_qs.count()
        
        # Overdue tasks: status is 'overdue'
        context['overdue_tasks'] = task_qs.filter(status='overdue').count()
        
        # Task status chart data
        context['completed_tasks'] = task_qs.filter(status='completed').count()
        context['pending_tasks'] = task_qs.filter(status__in=['pending','in_progress']).count()
        
        # Recent activity (latest 8 cases, documents, or tasks)
        context['recent_cases'] = case_qs.order_by('-created_at')[:4]
        context['recent_documents'] = doc_qs.order_by('-id')[:2]
        context['recent_tasks'] = task_qs.order_by('-id')[:2]
        
        # Chart data for Plotly - Case Status Distribution
        from collections import Counter
        case_status_qs = case_qs.values_list('status', flat=True)
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
        task_status_qs = task_qs.values_list('status', flat=True)
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
        
        # Period filter context
        context['available_years'] = years
        context['available_months'] = months
        context['selected_years'] = selected_years
        context['selected_months'] = selected_months
        context['filter_all'] = filter_all

        return context

# ─── REPORTS VIEW ────────────────────────────────────────────────────────────
class LegalReportsView(OrganizationPermissionMixin, LoginRequiredMixin, TemplateView):
    template_name = 'legal/reports.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        organization = self.request.organization
        
        # Get case statuses for filters
        case_statuses = LegalCase.objects.filter(organization=organization).values_list('status', flat=True).distinct()
        context['case_statuses'] = sorted(list(case_statuses))
        
        # Get case types for filters
        case_types = CaseType.objects.filter(organization=organization).values_list('name', flat=True).distinct()
        context['case_types'] = sorted(list(case_types))
        
        # Get legal parties for filters
        legal_parties = LegalParty.objects.filter(organization=organization).values_list('name', flat=True).distinct()
        context['legal_parties'] = sorted(list(legal_parties))
        
        # Get task statuses for filters
        task_statuses = LegalTask.objects.filter(organization=organization).values_list('status', flat=True).distinct()
        context['task_statuses'] = sorted(list(task_statuses))
        
        # Get document titles for filters (since there's no document_type field)
        document_titles = LegalDocument.objects.filter(organization=organization).values_list('title', flat=True).distinct()
        context['document_titles'] = sorted(list(document_titles))
        
        # Get attorneys for task filters
        attorneys = CustomUser.objects.filter(organization=organization).values_list('email', flat=True).distinct()
        context['attorneys'] = sorted(list(attorneys))
        
        # Get cases for detailed reports filter
        cases = LegalCase.objects.filter(organization=organization).order_by('title')
        context['cases'] = cases
        
        # Get tasks for detailed reports filter
        tasks = LegalTask.objects.filter(organization=organization).order_by('title')
        context['tasks'] = tasks
        
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