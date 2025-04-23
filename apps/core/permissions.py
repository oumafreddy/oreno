from rest_framework import permissions

class IsTenantMember(permissions.BasePermission):
    def has_permission(self, request, view):
        return (
            request.user.is_authenticated and
            request.user.organization == request.organization
        )
    def has_object_permission(self, request, view, obj):
        return obj.organization == request.organization
