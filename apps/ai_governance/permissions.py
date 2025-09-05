"""
AI Governance specific permissions.
"""

from rest_framework import permissions


class IsAIGovernanceAdmin(permissions.BasePermission):
    """
    Allows access only to users with AI governance admin permissions.
    Requires organization admin role or specific AI governance admin permission.
    """
    
    def has_permission(self, request, view):
        user = request.user
        org = getattr(user, 'organization', None)
        
        if not user.is_authenticated or not org:
            return False
        
        # Organization admins have full access
        if user.role == 'admin':
            return True
        
        # Check for specific AI governance admin permission
        if hasattr(user, 'has_perm'):
            return user.has_perm('ai_governance.admin_access')
        
        return False


class IsAIGovernanceManager(permissions.BasePermission):
    """
    Allows access to users with AI governance manager permissions.
    Includes organization admins, managers, and users with specific AI governance permissions.
    """
    
    def has_permission(self, request, view):
        user = request.user
        org = getattr(user, 'organization', None)
        
        if not user.is_authenticated or not org:
            return False
        
        # Organization admins and managers have access
        if user.role in ['admin', 'manager']:
            return True
        
        # Check for specific AI governance permissions
        if hasattr(user, 'has_perm'):
            return user.has_perm('ai_governance.manager_access')
        
        return False


class IsAIGovernanceStaff(permissions.BasePermission):
    """
    Allows access to users with AI governance staff permissions.
    Includes organization admins, managers, staff, and users with specific AI governance permissions.
    """
    
    def has_permission(self, request, view):
        user = request.user
        org = getattr(user, 'organization', None)
        
        if not user.is_authenticated or not org:
            return False
        
        # Organization admins, managers, and staff have access
        if user.role in ['admin', 'manager', 'staff']:
            return True
        
        # Check for specific AI governance permissions
        if hasattr(user, 'has_perm'):
            return user.has_perm('ai_governance.staff_access')
        
        return False


class CanExecuteTests(permissions.BasePermission):
    """
    Allows users to execute AI governance tests.
    Requires manager level access or specific test execution permission.
    """
    
    def has_permission(self, request, view):
        user = request.user
        org = getattr(user, 'organization', None)
        
        if not user.is_authenticated or not org:
            return False
        
        # Organization admins and managers can execute tests
        if user.role in ['admin', 'manager']:
            return True
        
        # Check for specific test execution permission
        if hasattr(user, 'has_perm'):
            return user.has_perm('ai_governance.execute_tests')
        
        return False


class CanViewTestResults(permissions.BasePermission):
    """
    Allows users to view test results.
    All authenticated users in the organization can view results.
    """
    
    def has_permission(self, request, view):
        user = request.user
        org = getattr(user, 'organization', None)
        
        return user.is_authenticated and org is not None


class CanManageConnectors(permissions.BasePermission):
    """
    Allows users to manage AI governance connectors.
    Requires admin level access or specific connector management permission.
    """
    
    def has_permission(self, request, view):
        user = request.user
        org = getattr(user, 'organization', None)
        
        if not user.is_authenticated or not org:
            return False
        
        # Only organization admins can manage connectors
        if user.role == 'admin':
            return True
        
        # Check for specific connector management permission
        if hasattr(user, 'has_perm'):
            return user.has_perm('ai_governance.manage_connectors')
        
        return False


class CanManageFrameworks(permissions.BasePermission):
    """
    Allows users to manage compliance frameworks.
    Requires admin level access or specific framework management permission.
    """
    
    def has_permission(self, request, view):
        user = request.user
        org = getattr(user, 'organization', None)
        
        if not user.is_authenticated or not org:
            return False
        
        # Only organization admins can manage frameworks
        if user.role == 'admin':
            return True
        
        # Check for specific framework management permission
        if hasattr(user, 'has_perm'):
            return user.has_perm('ai_governance.manage_frameworks')
        
        return False
