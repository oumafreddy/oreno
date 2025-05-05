# apps/organizations/views.py
from rest_framework import generics, permissions, viewsets
from rest_framework.decorators import action
from rest_framework.response import Response
from .serializers import OrganizationSettingsSerializer

from django.shortcuts import render, redirect, get_object_or_404
from django.views.generic import (
    ListView, DetailView, CreateView, UpdateView, DeleteView,
    TemplateView
)
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.messages.views import SuccessMessageMixin
from django.urls import reverse_lazy
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.db.models import Q, Prefetch, Count
from django.contrib import messages
from django.http import Http404

from .models import (
    Organization, OrganizationSettings, Subscription,
    Domain, OrganizationUser
)
from .forms import OrganizationForm, OrganizationSettingsForm, SubscriptionForm
from .serializers import (
    OrganizationSerializer, OrganizationDetailSerializer,
    OrganizationSettingsSerializer, SubscriptionSerializer,
    DomainSerializer, OrganizationUserSerializer
)
from .mixins import OrganizationContextMixin, OrganizationPermissionMixin, AdminRequiredMixin
from core.permissions import IsTenantMember
from core.mixins.organization import OrganizationScopedQuerysetMixin

# API ViewSets
class OrganizationViewSet(OrganizationScopedQuerysetMixin, viewsets.ModelViewSet):
    """API endpoint for organizations."""
    serializer_class = OrganizationSerializer
    permission_classes = [permissions.IsAuthenticated, IsTenantMember]

    def get_serializer_class(self):
        if self.action == 'retrieve':
            return OrganizationDetailSerializer
        return self.serializer_class

    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)

class OrganizationSettingsViewSet(OrganizationScopedQuerysetMixin, viewsets.ModelViewSet):
    """API endpoint for organization settings."""
    serializer_class = OrganizationSettingsSerializer
    permission_classes = [permissions.IsAuthenticated, IsTenantMember]

class SubscriptionViewSet(OrganizationScopedQuerysetMixin, viewsets.ModelViewSet):
    """API endpoint for subscriptions."""
    serializer_class = SubscriptionSerializer
    permission_classes = [permissions.IsAuthenticated, IsTenantMember]

class DomainViewSet(OrganizationScopedQuerysetMixin, viewsets.ModelViewSet):
    """API endpoint for domains."""
    serializer_class = DomainSerializer
    permission_classes = [permissions.IsAuthenticated, IsTenantMember]

class OrganizationUserViewSet(OrganizationScopedQuerysetMixin, viewsets.ModelViewSet):
    """API endpoint for organization users."""
    serializer_class = OrganizationUserSerializer
    permission_classes = [permissions.IsAuthenticated, IsTenantMember]

# Web Views
class OrganizationListView(LoginRequiredMixin, ListView):
    model = Organization
    template_name = 'organizations/organization_list.html'
    context_object_name = 'organizations'
    paginate_by = 20

    def get_queryset(self):
        return Organization.objects.filter(users=self.request.user)

class OrganizationDetailView(OrganizationPermissionMixin, DetailView):
    model = Organization
    template_name = 'organizations/organization_detail.html'
    context_object_name = 'organization'

    def get_queryset(self):
        return Organization.objects.filter(users=self.request.user)

    def get_organization(self):
        return self.get_object()

    def get(self, request, *args, **kwargs):
        try:
            self.object = self.get_object()
        except Organization.DoesNotExist:
            return render(request, 'organizations/organization_not_found.html', {
                'pk': kwargs.get('pk'),
                'message': 'No organization found matching your query or you do not have permission to view it.'
            }, status=404)
        context = self.get_context_data(object=self.object)
        return self.render_to_response(context)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        organization = self.object
        user = self.request.user
        # Use the same logic as your model method
        context['can_edit_org'] = user.is_superuser or (
            hasattr(user, 'has_org_admin_access') and user.has_org_admin_access(organization)
        )
        return context

class OrganizationCreateView(LoginRequiredMixin, SuccessMessageMixin, CreateView):
    model = Organization
    form_class = OrganizationForm
    template_name = 'organizations/organization_form.html'
    success_message = _("Organization %(name)s was created successfully")

    def form_valid(self, form):
        with transaction.atomic():
            organization = form.save()
            OrganizationUser.objects.create(
                organization=organization,
                user=self.request.user,
                role='admin'
            )
            return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy('organizations:detail', kwargs={'pk': self.object.pk})

class OrganizationUpdateView(OrganizationPermissionMixin, SuccessMessageMixin, UpdateView):
    model = Organization
    form_class = OrganizationForm
    template_name = 'organizations/organization_form.html'
    success_message = _("Organization %(name)s was updated successfully")

    def get_success_url(self):
        return reverse_lazy('organizations:detail', kwargs={'pk': self.object.pk})

    def get_organization(self):
        return self.get_object()

class OrganizationDeleteView(OrganizationPermissionMixin, SuccessMessageMixin, DeleteView):
    model = Organization
    template_name = 'organizations/organization_confirm_delete.html'
    success_url = reverse_lazy('organizations:list')
    success_message = _("Organization was archived successfully")

    @transaction.atomic
    def delete(self, request, *args, **kwargs):
        organization = self.get_object()
        organization.is_active = False
        organization.save()
        messages.success(self.request, self.success_message)
        return redirect(self.success_url)

    def get_organization(self):
        return self.get_object()

class OrganizationSettingsView(OrganizationPermissionMixin, UpdateView):
    model = OrganizationSettings
    form_class = OrganizationSettingsForm
    template_name = 'organizations/settings_form.html'
    success_message = _("Organization settings were updated successfully")

    def get_object(self):
        return get_object_or_404(
            OrganizationSettings,
            organization__users=self.request.user,
            organization=self.kwargs.get('org_pk')
        )

    def get_success_url(self):
        return reverse_lazy('organizations:settings', kwargs={'org_pk': self.object.organization.pk})

    def get_organization(self):
        return self.get_object().organization

class SubscriptionUpdateView(OrganizationPermissionMixin, UpdateView):
    model = Subscription
    form_class = SubscriptionForm
    template_name = 'organizations/subscription_form.html'
    success_message = _("Subscription was updated successfully")

    def get_object(self):
        return get_object_or_404(
            Subscription,
            organization__users=self.request.user,
            organization=self.kwargs.get('org_pk')
        )

    def get_success_url(self):
        return reverse_lazy('organizations:subscription', kwargs={'org_pk': self.object.organization.pk})

    def get_organization(self):
        return self.get_object().organization

class OrganizationDashboardView(LoginRequiredMixin, TemplateView):
    template_name = 'organizations/dashboard.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user_organizations = Organization.objects.filter(users=self.request.user)
        context.update({
            'organizations': user_organizations,
            'total_organizations': user_organizations.count(),
            'active_organizations': user_organizations.filter(is_active=True).count(),
            'recent_activities': self.get_recent_activities(user_organizations)
        })
        return context

    def get_recent_activities(self, organizations):
        # Implement activity tracking logic here
        return []