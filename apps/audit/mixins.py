"""
Organization Scoping Mixins for Audit App

This module provides mixins to ensure consistent organization filtering
across all views, API endpoints, and forms in the audit app.
"""
from django.contrib.auth.mixins import LoginRequiredMixin
from django.core.exceptions import PermissionDenied, ValidationError
from django.db.models import Q
from django.http import Http404
from django.utils.translation import gettext_lazy as _
from rest_framework import permissions, exceptions

# ───────────────────────────── VIEW MIXINS ─────────────────────────────────
class AuditOrganizationScopedMixin(LoginRequiredMixin):
    """
    Main mixin for enforcing organization scoping in class-based views.
    
    This mixin performs the following functions:
    1. Ensures user is authenticated
    2. Filters querysets by the user's active organization
    3. Adds active organization to form kwargs
    4. Verifies organization permission for object detail views
    """
    def setup(self, request, *args, **kwargs):
        """Initialize attributes shared by all view methods."""
        super().setup(request, *args, **kwargs)
        # Store active organization for consistent use throughout the view
        self.active_organization = getattr(request.user, 'active_organization', None)
        if not self.active_organization and request.user.is_authenticated:
            raise PermissionDenied(_("You must have an active organization to access this resource"))
    
    def get_queryset(self):
        """Filter queryset by active organization."""
        queryset = super().get_queryset()
        if hasattr(queryset.model, 'organization'):
            return queryset.filter(organization=self.active_organization)
        return queryset

    def get_form_kwargs(self):
        """Add organization to form kwargs."""
        kwargs = super().get_form_kwargs()
        kwargs['organization'] = self.active_organization
        return kwargs

    def get_object(self, queryset=None):
        """Ensure object belongs to user's organization."""
        obj = super().get_object(queryset)
        if hasattr(obj, 'organization') and obj.organization != self.active_organization:
            raise Http404(_("Object not found in your organization"))
        return obj
        
    def form_valid(self, form):
        """Ensure form instance is associated with user's organization."""
        if hasattr(form.instance, 'organization'):
            form.instance.organization = self.active_organization
        
        # Track the user who created/updated the object
        if hasattr(form.instance, 'created_by') and not form.instance.pk:
            form.instance.created_by = self.request.user
            
        if hasattr(form.instance, 'updated_by'):
            form.instance.updated_by = self.request.user
            
        # Set a consistent last_modified_by if the model has it
        if hasattr(form.instance, 'last_modified_by'):
            form.instance.last_modified_by = self.request.user
            
        return super().form_valid(form)

# ───────────────────────────── API MIXINS ─────────────────────────────────
class OrganizationScopedApiMixin:
    """
    Mixin for DRF views and viewsets to enforce organization scoping.
    """
    def get_queryset(self):
        """Filter API queryset by user's active organization."""
        queryset = super().get_queryset()
        user = self.request.user
        if user.is_authenticated and hasattr(queryset.model, 'organization'):
            # Get active organization
            active_organization = getattr(user, 'active_organization', None)
            if not active_organization:
                return queryset.none()  # Return empty queryset if no active org
            
            return queryset.filter(organization=active_organization)
        return queryset

    def perform_create(self, serializer):
        """Set organization on created objects."""
        user = self.request.user
        active_organization = getattr(user, 'active_organization', None)
        
        if not active_organization:
            raise exceptions.ValidationError({
                'organization': _('You must have an active organization to create resources')
            })
            
        # Set organization and audit fields
        serializer_kwargs = {'organization': active_organization}
        
        # Set audit trail fields if model supports them
        model = serializer.Meta.model
        if hasattr(model, 'created_by'):
            serializer_kwargs['created_by'] = user
        if hasattr(model, 'updated_by'):
            serializer_kwargs['updated_by'] = user
        if hasattr(model, 'last_modified_by'):
            serializer_kwargs['last_modified_by'] = user
        
        serializer.save(**serializer_kwargs)

    def perform_update(self, serializer):
        """Update audit fields."""
        user = self.request.user
        
        # Set audit trail fields if model supports them
        serializer_kwargs = {}
        if hasattr(serializer.Meta.model, 'updated_by'):
            serializer_kwargs['updated_by'] = user
        if hasattr(serializer.Meta.model, 'last_modified_by'):
            serializer_kwargs['last_modified_by'] = user
            
        serializer.save(**serializer_kwargs)

# ───────────────────────────── PERMISSIONS ─────────────────────────────────
class IsInOrganizationPermission(permissions.BasePermission):
    """
    Ensures that a user is accessing object(s) in their active organization.
    """
    message = _("You do not have permission to access this object")
    
    def has_permission(self, request, view):
        """Check active organization for list actions."""
        if not request.user.is_authenticated:
            return False
            
        active_organization = getattr(request.user, 'active_organization', None)
        return active_organization is not None
    
    def has_object_permission(self, request, view, obj):
        """Check that object belongs to user's active organization."""
        if not request.user.is_authenticated:
            return False
            
        active_organization = getattr(request.user, 'active_organization', None)
        if not active_organization:
            return False
            
        # Get object's organization
        obj_organization = getattr(obj, 'organization', None)
        if obj_organization is None:
            return False  # Safety - if we can't verify org, deny access
            
        return obj_organization == active_organization

# ───────────────────────────── FORM MIXIN ─────────────────────────────────
class OrganizationFormMixin:
    """
    Mixin for forms to ensure organization scoping in field querysets
    """
    def __init__(self, *args, **kwargs):
        """Initialize with organization."""
        self.organization = kwargs.pop('organization', None)
        super().__init__(*args, **kwargs)
        
        # Filter each foreign key field by organization if applicable
        if self.organization:
            for field_name, field in self.fields.items():
                # Filter querysets for relation fields
                if hasattr(field, 'queryset') and field.queryset is not None:
                    model = field.queryset.model
                    if hasattr(model, 'organization'):
                        field.queryset = field.queryset.filter(organization=self.organization)

    def clean(self):
        """Ensure form data respects organization boundaries."""
        cleaned_data = super().clean()
        
        # Verify relations are in the same organization
        for field_name, field_value in cleaned_data.items():
            if hasattr(field_value, 'organization') and field_value.organization != self.organization:
                self.add_error(field_name, _("Selected item must be from your organization"))
                
        return cleaned_data
