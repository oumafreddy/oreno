from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404

from users.permissions import IsOrgAdmin, IsOrgManagerOrReadOnly, IsOrgStaffOrReadOnly


class OrganizationPermissionMixin(LoginRequiredMixin):
    """
    Mixin to ensure user has access to organization-scoped AI governance resources.
    Reuses existing org context/permission middleware behavior.
    """
    
    def dispatch(self, request, *args, **kwargs):
        # Ensure user is authenticated
        if not request.user.is_authenticated:
            return self.handle_no_permission()
        
        # Check if user has organization context
        if not hasattr(request, 'tenant') or not request.tenant:
            raise PermissionDenied("No organization context available")
        
        # Ensure user belongs to the organization
        if request.user.organization != request.tenant:
            raise PermissionDenied("Access denied to this organization's AI governance resources")
        
        return super().dispatch(request, *args, **kwargs)


class AIGovernanceAdminMixin(OrganizationPermissionMixin):
    """
    Mixin for AI governance admin-only views.
    Requires organization admin permissions.
    """
    
    def dispatch(self, request, *args, **kwargs):
        # Check admin permissions
        if not IsOrgAdmin().has_permission(request, self):
            raise PermissionDenied("Admin access required for AI governance management")
        
        return super().dispatch(request, *args, **kwargs)


class AIGovernanceManagerMixin(OrganizationPermissionMixin):
    """
    Mixin for AI governance manager views.
    Allows read access to all users, write access to managers and admins.
    """
    
    def dispatch(self, request, *args, **kwargs):
        # Check manager permissions for write operations
        if request.method not in ['GET', 'HEAD', 'OPTIONS']:
            if not IsOrgManagerOrReadOnly().has_permission(request, self):
                raise PermissionDenied("Manager access required for AI governance modifications")
        
        return super().dispatch(request, *args, **kwargs)


class AIGovernanceStaffMixin(OrganizationPermissionMixin):
    """
    Mixin for AI governance staff views.
    Allows read access to all users, write access to staff, managers and admins.
    """
    
    def dispatch(self, request, *args, **kwargs):
        # Check staff permissions for write operations
        if request.method not in ['GET', 'HEAD', 'OPTIONS']:
            if not IsOrgStaffOrReadOnly().has_permission(request, self):
                raise PermissionDenied("Staff access required for AI governance operations")
        
        return super().dispatch(request, *args, **kwargs)


class SecurityAwareMixin:
    """
    Mixin to add security awareness to AI governance views.
    Handles PII detection and data classification.
    """
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Add security context
        context['security_enabled'] = True
        context['pii_detection_enabled'] = True
        context['data_classification_enabled'] = True
        
        return context
    
    def check_data_access_permissions(self, obj, user):
        """
        Check if user has permission to access data based on classification.
        """
        if not hasattr(obj, 'data_classification'):
            return True
        
        # Public data - accessible to all
        if obj.data_classification == 'public':
            return True
        
        # Internal data - accessible to all organization members
        if obj.data_classification == 'internal':
            return user.organization == obj.organization
        
        # Confidential data - accessible to staff and above
        if obj.data_classification == 'confidential':
            return (user.organization == obj.organization and 
                   user.role in ['staff', 'manager', 'admin'])
        
        # Restricted data - accessible to managers and admins only
        if obj.data_classification == 'restricted':
            return (user.organization == obj.organization and 
                   user.role in ['manager', 'admin'])
        
        return False


class AuditLogMixin:
    """
    Mixin to add audit logging capabilities to AI governance views.
    """
    
    def log_ai_governance_activity(self, activity_type, details, user=None, organization=None):
        """
        Log AI governance activity for audit purposes.
        """
        from .signals import log_ai_governance_activity
        
        log_ai_governance_activity(
            activity_type=activity_type,
            details=details,
            user=user or self.request.user,
            organization=organization or self.request.tenant
        )
    
    def dispatch(self, request, *args, **kwargs):
        response = super().dispatch(request, *args, **kwargs)
        
        # Log view access
        if hasattr(self, 'get_object'):
            try:
                obj = self.get_object()
                if obj:
                    self.log_ai_governance_activity(
                        activity_type='view_accessed',
                        details={
                            'view_name': self.__class__.__name__,
                            'object_type': obj.__class__.__name__,
                            'object_id': obj.id,
                            'method': request.method
                        }
                    )
            except:
                pass  # Ignore errors in audit logging
        
        return response
