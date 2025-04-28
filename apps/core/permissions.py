from rest_framework import permissions

class IsTenantMember(permissions.BasePermission):
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        # Lazy import to avoid circular dependencies
        from organizations.models import Organization
        return isinstance(request.organization, Organization)

    def has_object_permission(self, request, view, obj):
        return obj.organization == request.organization
