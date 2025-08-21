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
        
        obj = None
        if hasattr(self, 'get_object') and callable(getattr(self, 'get_object', None)):
            try:
                obj = self.get_object()
            except Exception:
                obj = None

        if obj is not None:
            if not hasattr(obj, 'organization'):
                raise PermissionDenied("Object does not belong to an organization")
            if not request.organization == obj.organization:
                raise PermissionDenied("You do not have permission to access this organization")
        else:
            # For list views, ensure organization is set
            if not hasattr(request, 'organization') or request.organization is None:
                raise PermissionDenied("Organization context is missing")

        return super().dispatch(request, *args, **kwargs) 