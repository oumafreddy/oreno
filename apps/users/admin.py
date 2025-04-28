# apps/users/admin.py
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from django.db.models import Q
from reversion.admin import VersionAdmin

from .models import CustomUser, Profile, OTP, OrganizationRole

@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin, VersionAdmin):
    """
    Enhanced admin interface for CustomUser with version control and organization context.
    """
    list_display = (
        'email', 'username', 'get_full_name', 'organization', 'role',
        'is_staff', 'is_active', 'last_login', 'date_joined'
    )
    list_filter = (
        'organization', 'role', 'is_staff', 'is_active',
        'date_joined', 'last_login'
    )
    search_fields = (
        'email', 'username', 'first_name', 'last_name',
        'organization__customer_name', 'organization__customer_code'
    )
    ordering = ('-date_joined',)
    readonly_fields = ('date_joined', 'last_login')
    
    fieldsets = (
        (None, {
            'fields': ('email', 'password')
        }),
        (_('Personal info'), {
            'fields': ('username', 'first_name', 'last_name')
        }),
        (_('Organization'), {
            'fields': ('organization', 'role')
        }),
        (_('Permissions'), {
            'fields': (
                'is_active', 'is_staff', 'is_superuser',
                'groups', 'user_permissions'
            ),
            'classes': ('collapse',)
        }),
        (_('Important dates'), {
            'fields': ('last_login', 'date_joined'),
            'classes': ('collapse',)
        }),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': (
                'email', 'username', 'password1', 'password2',
                'organization', 'role', 'is_staff', 'is_active'
            )
        }),
    )
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if not request.user.is_superuser:
            # Filter users based on organization context
            return qs.filter(
                Q(organization=request.user.organization) |
                Q(organizationuser__organization=request.user.organization)
            ).distinct()
        return qs
    
    def has_change_permission(self, request, obj=None):
        if not obj:
            return True
        if request.user.is_superuser:
            return True
        return obj.organization == request.user.organization
    
    def has_delete_permission(self, request, obj=None):
        if not obj:
            return True
        if request.user.is_superuser:
            return True
        return obj.organization == request.user.organization and obj != request.user

@admin.register(Profile)
class ProfileAdmin(VersionAdmin):
    """
    Admin interface for user profiles with version control.
    """
    list_display = ('user', 'get_organization', 'avatar')
    list_filter = ('user__organization',)
    search_fields = ('user__email', 'user__username')
    readonly_fields = ('user',)
    
    def get_organization(self, obj):
        return obj.user.organization
    get_organization.short_description = _('Organization')
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if not request.user.is_superuser:
            return qs.filter(user__organization=request.user.organization)
        return qs

@admin.register(OTP)
class OTPAdmin(VersionAdmin):
    """
    Admin interface for OTP management with version control.
    """
    list_display = ('user', 'otp', 'is_verified', 'attempts', 'expires_at', 'created_at')
    list_filter = ('is_verified', 'role', 'created_at')
    search_fields = ('user__email', 'otp')
    readonly_fields = ('otp', 'created_at', 'expires_at')
    ordering = ('-created_at',)
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if not request.user.is_superuser:
            return qs.filter(user__organization=request.user.organization)
        return qs

@admin.register(OrganizationRole)
class OrganizationRoleAdmin(VersionAdmin):
    """
    Admin interface for organization roles with version control.
    """
    list_display = ('user', 'organization', 'role')
    list_filter = ('role', 'organization')
    search_fields = ('user__email', 'organization__customer_name')
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if not request.user.is_superuser:
            return qs.filter(organization=request.user.organization)
        return qs
    
    def has_change_permission(self, request, obj=None):
        if not obj:
            return True
        if request.user.is_superuser:
            return True
        return obj.organization == request.user.organization
    
    def has_delete_permission(self, request, obj=None):
        if not obj:
            return True
        if request.user.is_superuser:
            return True
        return obj.organization == request.user.organization
