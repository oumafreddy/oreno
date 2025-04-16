# apps/organizations/mixins.py
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404
from .models import Organization

class AdminRequiredMixin(LoginRequiredMixin):
    """Verify that current user has admin privileges for the organization"""
    
    def dispatch(self, request, *args, **kwargs):
        # First check if user is authenticated
        if not request.user.is_authenticated:
            return self.handle_no_permission()
            
        # Check organization permissions if PK is present
        if 'pk' in kwargs:
            organization = get_object_or_404(Organization, pk=kwargs['pk'])
            if not self._has_admin_access(request.user, organization):
                raise PermissionDenied("You don't have permission to modify this organization")
        
        return super().dispatch(request, *args, **kwargs)

    def _has_admin_access(self, user, organization):
        """Check if user has admin access to the organization"""
        return user.organization == organization and \
               user.roles.filter(role='admin').exists()