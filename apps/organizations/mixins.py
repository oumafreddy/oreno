# apps/organizations/mixins.py
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404
from django.utils.translation import gettext_lazy as _
from django.core.cache import cache
from django.db.models import Q

from .models import Organization, OrganizationUser

class OrganizationContextMixin:
    """Provides organization context and caching for views"""
    
    def get_organization(self):
        """Get the current organization with caching"""
        if hasattr(self, '_organization'):
            return self._organization
            
        org_id = self.kwargs.get('pk') or self.kwargs.get('org_pk')
        if not org_id:
            return None
            
        cache_key = f'organization_{org_id}'
        organization = cache.get(cache_key)
        
        if not organization:
            organization = get_object_or_404(
                Organization.objects.select_related('settings', 'subscription'),
                pk=org_id
            )
            cache.set(cache_key, organization, 300)  # Cache for 5 minutes
            
        self._organization = organization
        return organization
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        organization = self.get_organization()
        if organization:
            context['organization'] = organization
            context['can_edit'] = self.request.user.has_org_admin_access(organization)
        return context

class OrganizationPermissionMixin(LoginRequiredMixin):
    """Enhanced permission checks for organization access"""
    
    def get_permission_required(self):
        """Get required permissions for the view"""
        return getattr(self, 'permission_required', None)
    
    def has_permission(self, user, organization):
        """Check if user has required permissions"""
        if user.is_superuser:
            return True
            
        required_permission = self.get_permission_required()
        if not required_permission:
            return True
            
        return user.has_perm(required_permission, organization)
    
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
            
        organization = self.get_organization()
        if organization and not self.has_permission(request.user, organization):
            raise PermissionDenied(_("You don't have permission to access this organization"))
            
        return super().dispatch(request, *args, **kwargs)

class AdminRequiredMixin(OrganizationPermissionMixin):
    """Verify that current user has admin privileges for the organization"""
    
    def has_permission(self, user, organization):
        if user.is_superuser:
            return True
            
        return OrganizationUser.objects.filter(
            user=user,
            organization=organization,
            role__in=['admin', 'manager']
        ).exists()
    
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
            
        organization = self.get_organization()
        if organization and not self.has_permission(request.user, organization):
            raise PermissionDenied(_("You don't have permission to modify this organization"))
            
        return super().dispatch(request, *args, **kwargs)

class OrganizationQuerysetMixin:
    """Provides organization-scoped querysets"""
    
    def get_queryset(self):
        queryset = super().get_queryset()
        organization = self.get_organization()
        
        if organization:
            return queryset.filter(organization=organization)
        elif not self.request.user.is_superuser:
            # For non-superusers, only show organizations they have access to
            return queryset.filter(
                Q(organizationuser__user=self.request.user) |
                Q(domains__domain=self.request.get_host())
            ).distinct()
            
        return queryset

class OrganizationCacheMixin:
    """Provides caching for organization-related data"""
    
    def get_cache_key(self, prefix):
        """Generate a cache key for organization data"""
        organization = self.get_organization()
        if not organization:
            return None
        return f'{prefix}_{organization.pk}_{self.request.user.pk}'
    
    def get_cached_data(self, cache_key, get_data_func, timeout=300):
        """Get data from cache or generate it if not present"""
        if not cache_key:
            return get_data_func()
            
        data = cache.get(cache_key)
        if data is None:
            data = get_data_func()
            cache.set(cache_key, data, timeout)
        return data