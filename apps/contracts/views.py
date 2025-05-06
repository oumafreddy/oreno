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

# --- Dashboard View ---
class ContractsDashboardView(OrganizationPermissionMixin, LoginRequiredMixin, TemplateView):
    template_name = 'contracts/dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        org = self.request.tenant
        from collections import Counter
        from contracts.models import Contract, ContractMilestone, Party, ContractType
        # Summary counts
        context['contract_count'] = Contract.objects.filter(organization=org).count()
        # Only parties linked to contracts for this org
        context['party_count'] = Party.objects.filter(contracts__organization=org).distinct().count()
        context['milestone_count'] = ContractMilestone.objects.filter(organization=org).count()
        # Recent contracts
        context['recent_contracts'] = Contract.objects.filter(organization=org).order_by('-start_date')[:8]
        # Contract status distribution
        status_dist = Contract.objects.filter(organization=org).values_list('status', flat=True)
        context['contract_status_dist'] = dict(Counter(status_dist))
        # Contract type distribution
        type_dist = Contract.objects.filter(organization=org).values_list('contract_type__name', flat=True)
        context['contract_type_dist'] = dict(Counter(type_dist))
        # Milestone type distribution
        milestone_type_dist = ContractMilestone.objects.filter(organization=org).values_list('milestone_type', flat=True)
        context['milestone_type_dist'] = dict(Counter(milestone_type_dist))
        # Milestone status distribution (using is_completed)
        milestone_status_dist = ContractMilestone.objects.filter(organization=org).values_list('is_completed', flat=True)
        status_map = {True: 'Completed', False: 'Pending'}
        milestone_status_dist = [status_map.get(val, 'Unknown') for val in milestone_status_dist]
        context['milestone_status_dist'] = dict(Counter(milestone_status_dist))
        # Contracts by party (top 10)
        party_dist = Party.objects.filter(contracts__organization=org).annotate(num_contracts=Count('contracts', filter=Q(contracts__organization=org))).order_by('-num_contracts').distinct()[:10]
        context['contract_party_dist'] = {p.name: p.num_contracts for p in party_dist}
        # Contract expiry distribution (by year)
        expiry_dist = Contract.objects.filter(organization=org).annotate(expiry_year=ExtractYear('end_date')).values('expiry_year').annotate(count=Count('id')).order_by('expiry_year')
        context['contract_expiry_dist'] = {str(e['expiry_year']): e['count'] for e in expiry_dist if e['expiry_year']}
        return context

# --- ContractType Views ---
class ContractTypeListView(OrganizationPermissionMixin, LoginRequiredMixin, ListView):
    model = ContractType
    template_name = 'contracts/contracttype_list.html'
    context_object_name = 'contracttypes'
    paginate_by = 20
    def get_queryset(self):
        qs = ContractType.objects.filter(organization=self.request.user.organization)
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
        return ContractType.objects.filter(organization=self.request.user.organization)

class ContractTypeCreateView(OrganizationPermissionMixin, LoginRequiredMixin, CreateView):
    model = ContractType
    form_class = ContractTypeForm
    template_name = 'contracts/contracttype_form.html'
    success_url = reverse_lazy('contracts:contracttype-list')
    def form_valid(self, form):
        form.instance.organization = self.request.user.organization
        return super().form_valid(form)
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['organization'] = self.request.user.organization
        return kwargs

class ContractTypeUpdateView(OrganizationPermissionMixin, LoginRequiredMixin, UpdateView):
    model = ContractType
    form_class = ContractTypeForm
    template_name = 'contracts/contracttype_form.html'
    success_url = reverse_lazy('contracts:contracttype-list')
    def form_valid(self, form):
        form.instance.organization = self.request.user.organization
        return super().form_valid(form)
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['organization'] = self.request.user.organization
        return kwargs

class ContractTypeDeleteView(OrganizationPermissionMixin, LoginRequiredMixin, DeleteView):
    model = ContractType
    template_name = 'contracts/contracttype_confirm_delete.html'
    success_url = reverse_lazy('contracts:contracttype-list')
    def get_queryset(self):
        return ContractType.objects.filter(organization=self.request.user.organization)

# --- Party Views ---
class PartyListView(OrganizationPermissionMixin, LoginRequiredMixin, ListView):
    model = Party
    template_name = 'contracts/party_list.html'
    context_object_name = 'parties'
    paginate_by = 20
    def get_queryset(self):
        qs = Party.objects.all()
        form = PartyFilterForm(self.request.GET)
        if form.is_valid():
            q = form.cleaned_data.get('q')
            if q:
                qs = qs.filter(name__icontains=q)
            party_type = form.cleaned_data.get('party_type')
            if party_type:
                qs = qs.filter(party_type__icontains=party_type)
            role = form.cleaned_data.get('role')
            if role:
                qs = qs.filter(role__icontains=role)
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
        return Party.objects.all()

class PartyCreateView(OrganizationPermissionMixin, LoginRequiredMixin, CreateView):
    model = Party
    form_class = PartyForm
    template_name = 'contracts/party_form.html'
    success_url = reverse_lazy('contracts:party-list')
    def form_valid(self, form):
        form.instance.created_by = self.request.user
        form.instance.updated_by = self.request.user
        return super().form_valid(form)
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['organization'] = self.request.user.organization
        return kwargs

class PartyUpdateView(OrganizationPermissionMixin, LoginRequiredMixin, UpdateView):
    model = Party
    form_class = PartyForm
    template_name = 'contracts/party_form.html'
    success_url = reverse_lazy('contracts:party-list')
    def form_valid(self, form):
        form.instance.updated_by = self.request.user
        return super().form_valid(form)
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['organization'] = self.request.user.organization
        return kwargs

class PartyDeleteView(OrganizationPermissionMixin, LoginRequiredMixin, DeleteView):
    model = Party
    template_name = 'contracts/party_confirm_delete.html'
    success_url = reverse_lazy('contracts:party-list')

# --- Contract Views ---
class ContractListView(OrganizationPermissionMixin, LoginRequiredMixin, ListView):
    model = Contract
    template_name = 'contracts/contract_list.html'
    context_object_name = 'contracts'
    def get_queryset(self):
        return Contract.objects.filter(organization=self.request.user.organization)

class ContractDetailView(OrganizationPermissionMixin, LoginRequiredMixin, DetailView):
    model = Contract
    template_name = 'contracts/contract_detail.html'
    context_object_name = 'contract'
    def get_queryset(self):
        return Contract.objects.filter(organization=self.request.user.organization)

class ContractCreateView(OrganizationPermissionMixin, LoginRequiredMixin, CreateView):
    model = Contract
    form_class = ContractForm
    template_name = 'contracts/contract_form.html'
    success_url = reverse_lazy('contracts:contract-list')
    def form_valid(self, form):
        form.instance.organization = self.request.user.organization
        form.instance.created_by = self.request.user
        form.instance.updated_by = self.request.user
        return super().form_valid(form)
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['organization'] = self.request.user.organization
        return kwargs

class ContractUpdateView(OrganizationPermissionMixin, LoginRequiredMixin, UpdateView):
    model = Contract
    form_class = ContractForm
    template_name = 'contracts/contract_form.html'
    success_url = reverse_lazy('contracts:contract-list')
    def form_valid(self, form):
        form.instance.organization = self.request.user.organization
        form.instance.updated_by = self.request.user
        return super().form_valid(form)
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['organization'] = self.request.user.organization
        return kwargs

class ContractDeleteView(OrganizationPermissionMixin, LoginRequiredMixin, DeleteView):
    model = Contract
    template_name = 'contracts/contract_confirm_delete.html'
    success_url = reverse_lazy('contracts:contract-list')
    def get_queryset(self):
        return Contract.objects.filter(organization=self.request.user.organization)

# --- ContractParty Views ---
class ContractPartyListView(OrganizationPermissionMixin, LoginRequiredMixin, ListView):
    model = ContractParty
    template_name = 'contracts/contractparty_list.html'
    context_object_name = 'contractparties'
    def get_queryset(self):
        return ContractParty.objects.all()

class ContractPartyDetailView(OrganizationPermissionMixin, LoginRequiredMixin, DetailView):
    model = ContractParty
    template_name = 'contracts/contractparty_detail.html'
    context_object_name = 'contractparty'
    def get_queryset(self):
        return ContractParty.objects.all()

class ContractPartyCreateView(OrganizationPermissionMixin, LoginRequiredMixin, CreateView):
    model = ContractParty
    form_class = ContractPartyForm
    template_name = 'contracts/contractparty_form.html'
    success_url = reverse_lazy('contracts:contractparty-list')

class ContractPartyUpdateView(OrganizationPermissionMixin, LoginRequiredMixin, UpdateView):
    model = ContractParty
    form_class = ContractPartyForm
    template_name = 'contracts/contractparty_form.html'
    success_url = reverse_lazy('contracts:contractparty-list')

class ContractPartyDeleteView(OrganizationPermissionMixin, LoginRequiredMixin, DeleteView):
    model = ContractParty
    template_name = 'contracts/contractparty_confirm_delete.html'
    success_url = reverse_lazy('contracts:contractparty-list')

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
        return ContractMilestone.objects.filter(organization=self.request.user.organization)

class ContractMilestoneCreateView(OrganizationPermissionMixin, LoginRequiredMixin, CreateView):
    model = ContractMilestone
    form_class = ContractMilestoneForm
    template_name = 'contracts/contractmilestone_form.html'
    success_url = reverse_lazy('contracts:contractmilestone-list')
    def form_valid(self, form):
        form.instance.organization = self.request.user.organization
        form.instance.created_by = self.request.user
        form.instance.updated_by = self.request.user
        return super().form_valid(form)
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['organization'] = self.request.user.organization
        return kwargs

class ContractMilestoneUpdateView(OrganizationPermissionMixin, LoginRequiredMixin, UpdateView):
    model = ContractMilestone
    form_class = ContractMilestoneForm
    template_name = 'contracts/contractmilestone_form.html'
    success_url = reverse_lazy('contracts:contractmilestone-list')
    def form_valid(self, form):
        form.instance.organization = self.request.user.organization
        form.instance.updated_by = self.request.user
        return super().form_valid(form)
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['organization'] = self.request.user.organization
        return kwargs

class ContractMilestoneDeleteView(OrganizationPermissionMixin, LoginRequiredMixin, DeleteView):
    model = ContractMilestone
    template_name = 'contracts/contractmilestone_confirm_delete.html'
    success_url = reverse_lazy('contracts:contractmilestone-list')
    def get_queryset(self):
        return ContractMilestone.objects.filter(organization=self.request.user.organization)
