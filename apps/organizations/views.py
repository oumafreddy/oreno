# apps/organizations/views.py
from django.views.generic import (
    ListView, DetailView, CreateView, UpdateView, DeleteView
)
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404
from django.db import transaction
from .models import Organization, ArchivedOrganization, OrganizationSettings, Subscription
from .forms import OrganizationForm
from .mixins import AdminRequiredMixin  # Custom mixin (defined below)

class OrganizationListView(LoginRequiredMixin, ListView):
    model = Organization
    template_name = 'organizations/organization_list.html'
    context_object_name = 'organizations'
    paginate_by = 20
    ordering = ['customer_name']
    
    def get_queryset(self):
        """Add optional filtering capabilities"""
        queryset = super().get_queryset().select_related('settings', 'subscription')
        # Example filter implementation
        if 'inactive' in self.request.GET:
            queryset = queryset.filter(is_active=False)
        return queryset

class OrganizationDetailView(LoginRequiredMixin, DetailView):
    model = Organization
    template_name = 'organizations/organization_detail.html'
    context_object_name = 'organization'
    slug_field = 'pk'  # Explicitly use PK for URLs
    slug_url_kwarg = 'pk'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        organization = self.object
        
        # Add related data efficiently
        context.update({
            'settings': organization.settings,
            'subscription': organization.subscription,
            'employees': organization.get_employees().select_related('profile'),
            'user_role': self.request.user.get_organization_role(organization),
        })
        return context

class OrganizationCreateView(AdminRequiredMixin, SuccessMessageMixin, CreateView):
    model = Organization
    form_class = OrganizationForm
    template_name = 'organizations/organization_form.html'
    success_message = _("Organization %(customer_name)s was created successfully")
    
    @transaction.atomic
    def form_valid(self, form):
        """Handle creation of related models atomically"""
        form.instance.created_by = self.request.user
        response = super().form_valid(form)
        
        # Create related settings and subscription
        OrganizationSettings.objects.create(organization=self.object)
        Subscription.objects.create(organization=self.object)
        
        return response

    def get_success_url(self):
        return reverse_lazy('organizations:detail', kwargs={'pk': self.object.pk})

class OrganizationUpdateView(AdminRequiredMixin, SuccessMessageMixin, UpdateView):
    model = Organization
    form_class = OrganizationForm
    template_name = 'organizations/organization_form.html'
    success_message = _("Organization %(customer_name)s was updated successfully")
    
    def get_success_url(self):
        return reverse_lazy('organizations:detail', kwargs={'pk': self.object.pk})

class OrganizationDeleteView(AdminRequiredMixin, SuccessMessageMixin, DeleteView):
    model = Organization
    template_name = 'organizations/organization_confirm_delete.html'
    success_url = reverse_lazy('organizations:list')
    success_message = _("Organization was archived successfully")
    
    @transaction.atomic
    def delete(self, request, *args, **kwargs):
        """Archive before deletion"""
        organization = self.get_object()
        
        # Create archived record
        ArchivedOrganization.objects.create(
            original_org_id=organization.id,
            customer_code=organization.customer_code,
            customer_name=organization.customer_name,
            archived_by_user=request.user,
            # ... copy other relevant fields ...
        )
        
        return super().delete(request, *args, **kwargs)

# Custom Mixins (apps/organizations/mixins.py)
class AdminRequiredMixin(LoginRequiredMixin):
    """Verify that current user has admin privileges for the organization"""
    
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
            
        if 'pk' in kwargs:
            organization = get_object_or_404(Organization, pk=kwargs['pk'])
            if not request.user.has_org_admin_access(organization):
                raise PermissionDenied(_("You don't have permission to modify this organization"))
        
        return super().dispatch(request, *args, **kwargs)