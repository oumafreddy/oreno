from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from users.models import CustomUser
from organizations.models import OrganizationUser

class OrgAdminRequiredMixin(LoginRequiredMixin):
    """
    Mixin to restrict access to organization admins/managers only.
    """
    def dispatch(self, request, *args, **kwargs):
        user = request.user
        if not user.is_authenticated:
            return self.handle_no_permission()
        # Check if user is admin/manager in their organization
        if user.is_superuser:
            return super().dispatch(request, *args, **kwargs)
        if not OrganizationUser.objects.filter(user=user, organization=user.organization, role__in=[CustomUser.ROLE_ADMIN, CustomUser.ROLE_MANAGER]).exists():
            raise PermissionDenied("You do not have admin access to this organization.")
        return super().dispatch(request, *args, **kwargs) 