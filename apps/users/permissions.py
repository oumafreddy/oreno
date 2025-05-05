from rest_framework import permissions

class IsOrgAdmin(permissions.BasePermission):
    """Allows access only to organization admins."""
    def has_permission(self, request, view):
        user = request.user
        org = getattr(user, 'organization', None)
        return user.is_authenticated and org and user.role == 'admin'

class IsOrgManagerOrReadOnly(permissions.BasePermission):
    """Allows managers full access, others read-only."""
    def has_permission(self, request, view):
        user = request.user
        org = getattr(user, 'organization', None)
        if not user.is_authenticated or not org:
            return False
        if request.method in permissions.SAFE_METHODS:
            return True
        return user.role in ['admin', 'manager']

class IsOrgStaffOrReadOnly(permissions.BasePermission):
    """Allows staff full access, others read-only."""
    def has_permission(self, request, view):
        user = request.user
        org = getattr(user, 'organization', None)
        if not user.is_authenticated or not org:
            return False
        if request.method in permissions.SAFE_METHODS:
            return True
        return user.role in ['admin', 'manager', 'staff']

# For more advanced org admin check (using has_org_admin_access):
class HasOrgAdminAccess(permissions.BasePermission):
    """Allows access if user has org admin access (custom method)."""
    def has_permission(self, request, view):
        user = request.user
        org = getattr(user, 'organization', None)
        return user.is_authenticated and org and hasattr(user, 'has_org_admin_access') and user.has_org_admin_access(org) 