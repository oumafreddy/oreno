from django.shortcuts import render
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView, TemplateView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from core.middleware import get_current_organization
from core.mixins.permissions import OrganizationPermissionMixin
from .models import ContractType, Party, Contract, ContractParty, ContractMilestone
from .forms import ContractTypeForm, PartyForm, ContractForm, ContractPartyForm, ContractMilestoneForm, PartyFilterForm, ContractTypeFilterForm, ContractMilestoneFilterForm
import json
from django.db.models import Count
from django.db.models.functions import ExtractYear
from django.db.models import Q
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from datetime import timedelta
from django.db import models
from collections import Counter

# --- Dashboard View ---
class ContractsDashboardView(OrganizationPermissionMixin, LoginRequiredMixin, TemplateView):
    template_name = 'contracts/dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Use organization from request
        org = self.request.organization
        
        # Final safety check
        if not org:
            # Return empty context if no organization found
            context.update({
                'contract_count': 0,
                'party_count': 0,
                'milestone_count': 0,
                'recent_contracts': [],
                'contract_status_dist': {'Draft': 0, 'Active': 0, 'Expired': 0},
                'contract_type_dist': {'General': 0},
                'milestone_type_dist': {'Payment': 0, 'Delivery': 0},
                'milestone_status_dist': {'Completed': 0, 'Pending': 0},
                'contract_party_dist': {'No Parties': 0},
                'contract_expiry_dist': {'2024': 0, '2025': 0},
            })
            return context
        
        from contracts.models import Contract, ContractMilestone, Party, ContractType
        from django.db.models import Count, Q
        from django.db.models.functions import ExtractYear
        
        # Summary counts with explicit organization filtering
        contract_count = Contract.objects.filter(organization=org).count()
        party_count = Party.objects.filter(organization=org).count()
        milestone_count = ContractMilestone.objects.filter(organization=org).count()
        
        context['contract_count'] = contract_count
        context['party_count'] = party_count
        context['milestone_count'] = milestone_count
        
        # Debugging: Print counts for verification
        print(f"ContractsDashboardView: Organization: {org.name} (ID: {org.id})")
        print(f"ContractsDashboardView: Contract count: {contract_count}")
        print(f"ContractsDashboardView: Party count: {party_count}")
        print(f"ContractsDashboardView: Milestone count: {milestone_count}")
        
        # Recent contracts
        context['recent_contracts'] = Contract.objects.filter(organization=org).order_by('-start_date')[:8]
        
        # Contract status distribution
        status_dist = Contract.objects.filter(organization=org).values_list('status', flat=True)
        status_counter = Counter(status_dist)
        # Map status values to display names
        status_mapping = {
            'draft': 'Draft',
            'active': 'Active',
            'expired': 'Expired',
            'terminated': 'Terminated',
            'pending': 'Pending'
        }
        contract_status_chart = {}
        for status, count in status_counter.items():
            display_name = status_mapping.get(status, status.title())
            contract_status_chart[display_name] = count
        context['contract_status_dist'] = contract_status_chart or {'Draft': 0, 'Active': 0, 'Expired': 0}
        
        # Contract type distribution
        type_dist = Contract.objects.filter(organization=org).values_list('contract_type__name', flat=True)
        type_counter = Counter(type_dist)
        context['contract_type_dist'] = dict(type_counter) or {'General': 0}
        
        # Milestone type distribution - with explicit organization filtering
        milestone_type_dist = ContractMilestone.objects.filter(organization=org).values_list('milestone_type', flat=True)
        milestone_type_counter = Counter(milestone_type_dist)
        context['milestone_type_dist'] = dict(milestone_type_counter) or {'Payment': 0, 'Delivery': 0}
        
        # Milestone status distribution (using is_completed) - with explicit organization filtering
        milestone_status_dist = ContractMilestone.objects.filter(organization=org).values_list('is_completed', flat=True)
        # Convert boolean values to human-readable strings for charting
        milestone_status_mapped = [
            'Completed' if status else 'Pending' for status in milestone_status_dist
        ]
        milestone_status_counter = Counter(milestone_status_mapped)
        context['milestone_status_dist'] = dict(milestone_status_counter) or {'Pending': 0}
        
        # Debugging: Print milestone status distribution
        print(f"ContractsDashboardView: Milestone status distribution: {context['milestone_status_dist']}")
        
        # Contracts by party (all parties with contracts)
        party_dist = Party.objects.filter(organization=org).annotate(
            num_contracts=Count('contracts', filter=Q(contracts__organization=org))
        ).filter(num_contracts__gt=0).order_by('-num_contracts')
        contract_party_chart = {party.name: party.num_contracts for party in party_dist}
        context['contract_party_dist'] = contract_party_chart or {'No Parties': 0}
        
        # Contract expiry distribution (by year)
        expiry_dist = Contract.objects.filter(organization=org, end_date__isnull=False).annotate(
            expiry_year=ExtractYear('end_date')
        ).values('expiry_year').annotate(count=Count('id')).order_by('expiry_year')
        contract_expiry_chart = {str(item['expiry_year']): item['count'] for item in expiry_dist}
        context['contract_expiry_dist'] = contract_expiry_chart or {'2024': 0, '2025': 0}
        
        return context

# ─── REPORTS VIEW ────────────────────────────────────────────────────────────
class ContractsReportsView(OrganizationPermissionMixin, LoginRequiredMixin, TemplateView):
    template_name = 'contracts/reports.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        organization = self.request.organization
        
        # Get contract statuses for filters
        contract_statuses = Contract.objects.filter(organization=organization).values_list('status', flat=True).distinct()
        context['contract_statuses'] = sorted(list(contract_statuses))
        
        # Get contract types for filters
        contract_types = ContractType.objects.filter(organization=organization).values_list('name', flat=True).distinct()
        context['contract_types'] = sorted(list(contract_types))
        
        # Get parties for filters
        parties = Party.objects.filter(organization=organization).values_list('name', flat=True).distinct()
        context['parties'] = sorted(list(parties))
        
        # Get milestone types for filters
        milestone_types = ContractMilestone.objects.filter(organization=organization).values_list('milestone_type', flat=True).distinct()
        context['milestone_types'] = sorted(list(milestone_types))
        
        # Get milestone statuses for filters
        milestone_statuses = ContractMilestone.objects.filter(organization=organization).values_list('is_completed', flat=True).distinct()
        context['milestone_statuses'] = sorted(list(milestone_statuses))
        
        return context

# --- ContractType Views ---
class ContractTypeListView(OrganizationPermissionMixin, LoginRequiredMixin, ListView):
    model = ContractType
    template_name = 'contracts/contracttype_list.html'
    context_object_name = 'contracttypes'
    paginate_by = 20
    def get_queryset(self):
        qs = super().get_queryset().filter(organization=self.request.organization)
        form = ContractTypeFilterForm(self.request.GET)
        if form.is_valid():
            q = form.cleaned_data.get('q')
            if q:
                qs = qs.filter(name__icontains=q)
        return qs
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['filter_form'] = ContractTypeFilterForm(self.request.GET)
        return context

class ContractTypeDetailView(OrganizationPermissionMixin, LoginRequiredMixin, DetailView):
    model = ContractType
    template_name = 'contracts/contracttype_detail.html'
    context_object_name = 'contracttype'
    def get_queryset(self):
        return super().get_queryset().filter(organization=self.request.organization)

class ContractTypeCreateView(OrganizationPermissionMixin, LoginRequiredMixin, CreateView):
    model = ContractType
    form_class = ContractTypeForm
    template_name = 'contracts/contracttype_form.html'
    success_url = reverse_lazy('contracts:contracttype-list')
    def form_valid(self, form):
        form.instance.organization = self.request.organization
        return super().form_valid(form)
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['organization'] = self.request.organization
        return kwargs

class ContractTypeUpdateView(OrganizationPermissionMixin, LoginRequiredMixin, UpdateView):
    model = ContractType
    form_class = ContractTypeForm
    template_name = 'contracts/contracttype_form.html'
    success_url = reverse_lazy('contracts:contracttype-list')
    def form_valid(self, form):
        form.instance.organization = self.request.organization
        return super().form_valid(form)
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['organization'] = self.request.organization
        return kwargs

class ContractTypeDeleteView(OrganizationPermissionMixin, LoginRequiredMixin, DeleteView):
    model = ContractType
    template_name = 'contracts/contracttype_confirm_delete.html'
    success_url = reverse_lazy('contracts:contracttype-list')
    def get_queryset(self):
        return super().get_queryset().filter(organization=self.request.organization)

# --- Party Views ---
class PartyListView(OrganizationPermissionMixin, LoginRequiredMixin, ListView):
    model = Party
    template_name = 'contracts/party_list.html'
    context_object_name = 'parties'
    paginate_by = 20
    def get_queryset(self):
        qs = super().get_queryset().filter(organization=self.request.organization)
        form = PartyFilterForm(self.request.GET)
        if form.is_valid():
            q = form.cleaned_data.get('q')
            if q:
                qs = qs.filter(
                    models.Q(name__icontains=q) | 
                    models.Q(legal_entity_name__icontains=q)
                )
            party_type = form.cleaned_data.get('party_type')
            if party_type:
                qs = qs.filter(party_type=party_type)
            contact_person = form.cleaned_data.get('contact_person')
            if contact_person:
                qs = qs.filter(contact_person__icontains=contact_person)
        return qs
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['filter_form'] = PartyFilterForm(self.request.GET)
        return context

class PartyDetailView(OrganizationPermissionMixin, LoginRequiredMixin, DetailView):
    model = Party
    template_name = 'contracts/party_detail.html'
    context_object_name = 'party'
    def get_queryset(self):
        return super().get_queryset().filter(organization=self.request.organization)

class PartyCreateView(OrganizationPermissionMixin, LoginRequiredMixin, CreateView):
    model = Party
    form_class = PartyForm
    template_name = 'contracts/party_form.html'
    success_url = reverse_lazy('contracts:party-list')
    def form_valid(self, form):
        form.instance.organization = self.request.organization
        form.instance.created_by = self.request.user
        form.instance.updated_by = self.request.user
        return super().form_valid(form)
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['organization'] = self.request.organization
        return kwargs

class PartyUpdateView(OrganizationPermissionMixin, LoginRequiredMixin, UpdateView):
    model = Party
    form_class = PartyForm
    template_name = 'contracts/party_form.html'
    success_url = reverse_lazy('contracts:party-list')
    def form_valid(self, form):
        form.instance.organization = self.request.organization
        form.instance.updated_by = self.request.user
        return super().form_valid(form)
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['organization'] = self.request.organization
        return kwargs

class PartyDeleteView(OrganizationPermissionMixin, LoginRequiredMixin, DeleteView):
    model = Party
    template_name = 'contracts/party_confirm_delete.html'
    success_url = reverse_lazy('contracts:party-list')
    def get_queryset(self):
        return super().get_queryset().filter(organization=self.request.organization)

# --- Contract Views ---
class ContractListView(OrganizationPermissionMixin, LoginRequiredMixin, ListView):
    model = Contract
    template_name = 'contracts/contract_list.html'
    context_object_name = 'contracts'
    def get_queryset(self):
        return super().get_queryset().filter(organization=self.request.organization)

class ContractDetailView(OrganizationPermissionMixin, LoginRequiredMixin, DetailView):
    model = Contract
    template_name = 'contracts/contract_detail.html'
    context_object_name = 'contract'
    def get_queryset(self):
        return super().get_queryset().filter(organization=self.request.organization)

class ContractCreateView(OrganizationPermissionMixin, LoginRequiredMixin, CreateView):
    model = Contract
    form_class = ContractForm
    template_name = 'contracts/contract_form.html'
    success_url = reverse_lazy('contracts:contract-list')
    def form_valid(self, form):
        form.instance.organization = self.request.organization
        form.instance.created_by = self.request.user
        form.instance.updated_by = self.request.user
        return super().form_valid(form)
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['organization'] = self.request.organization
        return kwargs

class ContractUpdateView(OrganizationPermissionMixin, LoginRequiredMixin, UpdateView):
    model = Contract
    form_class = ContractForm
    template_name = 'contracts/contract_form.html'
    success_url = reverse_lazy('contracts:contract-list')
    def form_valid(self, form):
        form.instance.organization = self.request.organization
        form.instance.updated_by = self.request.user
        return super().form_valid(form)
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['organization'] = self.request.organization
        return kwargs

class ContractDeleteView(OrganizationPermissionMixin, LoginRequiredMixin, DeleteView):
    model = Contract
    template_name = 'contracts/contract_confirm_delete.html'
    success_url = reverse_lazy('contracts:contract-list')
    def get_queryset(self):
        return super().get_queryset().filter(organization=self.request.organization)

# --- ContractParty Views ---
class ContractPartyListView(OrganizationPermissionMixin, LoginRequiredMixin, ListView):
    model = ContractParty
    template_name = 'contracts/contractparty_list.html'
    context_object_name = 'contractparties'
    def get_queryset(self):
        return super().get_queryset().filter(organization=self.request.organization)

class ContractPartyDetailView(OrganizationPermissionMixin, LoginRequiredMixin, DetailView):
    model = ContractParty
    template_name = 'contracts/contractparty_detail.html'
    context_object_name = 'contractparty'
    def get_queryset(self):
        return super().get_queryset().filter(organization=self.request.organization)

class ContractPartyCreateView(OrganizationPermissionMixin, LoginRequiredMixin, CreateView):
    model = ContractParty
    form_class = ContractPartyForm
    template_name = 'contracts/contractparty_form.html'
    success_url = reverse_lazy('contracts:contractparty-list')
    def form_valid(self, form):
        form.instance.organization = self.request.organization
        return super().form_valid(form)
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['organization'] = self.request.organization
        return kwargs

class ContractPartyUpdateView(OrganizationPermissionMixin, LoginRequiredMixin, UpdateView):
    model = ContractParty
    form_class = ContractPartyForm
    template_name = 'contracts/contractparty_form.html'
    success_url = reverse_lazy('contracts:contractparty-list')
    def form_valid(self, form):
        form.instance.organization = self.request.organization
        return super().form_valid(form)
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['organization'] = self.request.organization
        return kwargs

class ContractPartyDeleteView(OrganizationPermissionMixin, LoginRequiredMixin, DeleteView):
    model = ContractParty
    template_name = 'contracts/contractparty_confirm_delete.html'
    success_url = reverse_lazy('contracts:contractparty-list')
    def get_queryset(self):
        return super().get_queryset().filter(organization=self.request.organization)

# --- ContractMilestone Views ---
class ContractMilestoneListView(OrganizationPermissionMixin, LoginRequiredMixin, ListView):
    model = ContractMilestone
    template_name = 'contracts/contractmilestone_list.html'
    context_object_name = 'contractmilestones'
    paginate_by = 20
    def get_queryset(self):
        qs = ContractMilestone.objects.filter(organization=self.request.user.organization)
        form = ContractMilestoneFilterForm(self.request.GET)
        if form.is_valid():
            q = form.cleaned_data.get('q')
            if q:
                qs = qs.filter(name__icontains=q)
            is_completed = form.cleaned_data.get('is_completed')
            if is_completed == '1':
                qs = qs.filter(is_completed=True)
            elif is_completed == '0':
                qs = qs.filter(is_completed=False)
        return qs
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['filter_form'] = ContractMilestoneFilterForm(self.request.GET)
        return context

class ContractMilestoneDetailView(OrganizationPermissionMixin, LoginRequiredMixin, DetailView):
    model = ContractMilestone
    template_name = 'contracts/contractmilestone_detail.html'
    context_object_name = 'contractmilestone'
    def get_queryset(self):
        return super().get_queryset().filter(organization=self.request.organization)

class ContractMilestoneCreateView(OrganizationPermissionMixin, LoginRequiredMixin, CreateView):
    model = ContractMilestone
    form_class = ContractMilestoneForm
    template_name = 'contracts/contractmilestone_form.html'
    success_url = reverse_lazy('contracts:contractmilestone-list')
    def form_valid(self, form):
        form.instance.organization = self.request.organization
        form.instance.created_by = self.request.user
        form.instance.updated_by = self.request.user
        return super().form_valid(form)
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['organization'] = self.request.organization
        return kwargs

class ContractMilestoneUpdateView(OrganizationPermissionMixin, LoginRequiredMixin, UpdateView):
    model = ContractMilestone
    form_class = ContractMilestoneForm
    template_name = 'contracts/contractmilestone_form.html'
    success_url = reverse_lazy('contracts:contractmilestone-list')
    def form_valid(self, form):
        form.instance.organization = self.request.organization
        form.instance.updated_by = self.request.user
        return super().form_valid(form)
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['organization'] = self.request.organization
        return kwargs

class ContractMilestoneDeleteView(OrganizationPermissionMixin, LoginRequiredMixin, DeleteView):
    model = ContractMilestone
    template_name = 'contracts/contractmilestone_confirm_delete.html'
    success_url = reverse_lazy('contracts:contractmilestone-list')
    def get_queryset(self):
        return super().get_queryset().filter(organization=self.request.organization)

@login_required
def api_status_data(request):
    # Ensure we have the correct organization
    org = request.organization
    
    if not org:
        return JsonResponse({'error': 'No organization found'}, status=400)
    
    from .models import Contract
    from django.db.models import Count
    status_qs = Contract.objects.filter(organization=org).values('status').annotate(count=Count('id'))
    status_data = {s['status']: s['count'] for s in status_qs}
    return JsonResponse(status_data, safe=False)

@login_required
def api_type_data(request):
    # Ensure we have the correct organization
    org = request.organization
    
    if not org:
        return JsonResponse({'error': 'No organization found'}, status=400)
    
    from .models import Contract
    from django.db.models import Count
    type_qs = Contract.objects.filter(organization=org).values('contract_type').annotate(count=Count('id'))
    type_data = {s['contract_type']: s['count'] for s in type_qs}
    return JsonResponse(type_data, safe=False)

@login_required
def api_party_data(request):
    # Ensure we have the correct organization
    org = request.organization
    
    if not org:
        return JsonResponse({'error': 'No organization found'}, status=400)
    
    from .models import Party
    from django.db.models import Count
    party_qs = Party.objects.filter(organization=org).values('party_type').annotate(count=Count('id'))
    party_data = {s['party_type']: s['count'] for s in party_qs}
    return JsonResponse(party_data, safe=False)

@login_required
def api_milestone_type_data(request):
    """API endpoint for milestone type data used in dashboards."""
    # Ensure we have the correct organization
    org = request.organization
    
    if not org:
        return JsonResponse({'error': 'No organization found'}, status=400)
    
    milestones = ContractMilestone.objects.filter(organization=org)
    
    # Get milestone type distribution
    milestone_type_dist = milestones.values_list('milestone_type', flat=True)
    milestone_type_counter = Counter(milestone_type_dist)
    
    data = dict(milestone_type_counter) or {'Payment': 0, 'Delivery': 0}
    return JsonResponse(data)

@login_required
def api_expiry_data(request):
    """API endpoint for contract expiry data used in dashboards."""
    # Ensure we have the correct organization
    org = request.organization
    
    if not org:
        return JsonResponse({'error': 'No organization found'}, status=400)
    
    contracts = Contract.objects.filter(organization=org)
    today = timezone.now().date()
    
    data = {
        'total': contracts.count(),
        'expired': contracts.filter(end_date__lt=today).count(),
        'expiring_30_days': contracts.filter(
            end_date__gte=today,
            end_date__lte=today + timedelta(days=30)
        ).count(),
        'expiring_90_days': contracts.filter(
            end_date__gt=today + timedelta(days=30),
            end_date__lte=today + timedelta(days=90)
        ).count(),
        'valid': contracts.filter(end_date__gt=today + timedelta(days=90)).count(),
    }
    return JsonResponse(data)

@login_required
def api_milestone_status_data(request):
    """API endpoint for milestone status data used in dashboards."""
    # Ensure we have the correct organization
    org = request.organization
    
    if not org:
        return JsonResponse({'error': 'No organization found'}, status=400)
    
    milestones = ContractMilestone.objects.filter(organization=org)
    
    # Convert boolean values to human-readable strings for charting
    milestone_status_dist = milestones.values_list('is_completed', flat=True)
    milestone_status_mapped = [
        'Completed' if status else 'Pending' for status in milestone_status_dist
    ]
    milestone_status_counter = Counter(milestone_status_mapped)
    
    data = dict(milestone_status_counter) or {'Pending': 0}
    return JsonResponse(data)
