# apps/core/mixins/permissions.py

from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied

class OrganizationPermissionMixin(LoginRequiredMixin):
    """
    Mixin that checks if the user has permission to access the organization.
    """
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        
        # Get the organization from the view's get_object method
        obj = self.get_object()
        if not obj or not hasattr(obj, 'organization'):
            raise PermissionDenied("Object does not belong to an organization")
            
        # Check if user has access to the organization
        if not request.user.organization == obj.organization:
            raise PermissionDenied("You do not have permission to access this organization")
            
        return super().dispatch(request, *args, **kwargs) 