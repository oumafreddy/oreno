# apps/users/admin.py
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.translation import gettext_lazy as _
from django.contrib.auth.models import Permission
from django.contrib.contenttypes.models import ContentType
from django.db.models import Q
from django.utils.safestring import mark_safe
from reversion.admin import VersionAdmin

from users.models import CustomUser, Profile, OTP, OrganizationRole, PasswordHistory, PasswordPolicy, AccountLockout, SecurityAuditLog

@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin, VersionAdmin):
    """
    Enhanced admin interface for CustomUser with version control and organization context.
    Note: Tenant data cleanup/anonymization is handled by signals and management commands, not by admin cascade deletion.
    User deletion is disabled in the admin for multi-tenant safety. Use the management command or a custom view for deletion and cleanup.
    """
    list_display = (
        'email', 'username', 'get_full_name', 'organization', 'role',
        'is_staff', 'is_active', 'setup_status', 'last_login', 'date_joined'
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
    readonly_fields = ('date_joined', 'last_login', 'admin_delete_help', 'is_first_time_setup_complete')
    
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
        (_('Account Setup'), {
            'fields': ('is_admin_created', 'is_first_time_setup_complete'),
            'classes': ('collapse',)
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
                'organization', 'role', 'is_staff', 'is_active', 'is_admin_created'
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
        # Only superusers can delete users, not organization admins
        if not request.user.is_superuser:
            return False
        return True

    def admin_delete_help(self, obj=None):
        return mark_safe(
            '<div style="color: #b94a48; font-weight: bold;">'
            'User deletion and tenant data cleanup must be performed via the '
            '<b>management command</b> or a <b>custom view</b>.<br>'
            'This is required for multi-tenant safety and to avoid database errors.'
            '</div>'
        )
    admin_delete_help.short_description = 'Delete User (Important Notice)'

    def setup_status(self, obj):
        """Display setup status with color coding."""
        if obj.is_first_time_setup_complete:
            return mark_safe('<span style="color: green;">✓ Complete</span>')
        else:
            return mark_safe('<span style="color: orange;">⚠ Pending</span>')
    setup_status.short_description = 'Setup Status'

    def save_model(self, request, obj, form, change):
        """Override to automatically set admin_created flag for new users."""
        if not change:  # New user being created
            obj.is_admin_created = True
            obj.is_first_time_setup_complete = False
        super().save_model(request, obj, form, change)

@admin.register(Profile)
class ProfileAdmin(VersionAdmin):
    """
    Admin interface for user profiles with version control.
    """
    list_display = ('user', 'get_organization', 'avatar')
    list_filter = ('user__organization',)
    search_fields = ('user__email', 'user__username')
    
    def get_organization(self, obj):
        return obj.user.organization
    get_organization.short_description = _('Organization')
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if not request.user.is_superuser:
            return qs.filter(user__organization=request.user.organization)
        return qs
    
    def has_add_permission(self, request):
        """Prevent direct profile creation - profiles are created via signals"""
        return False

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


@admin.register(PasswordHistory)
class PasswordHistoryAdmin(VersionAdmin):
    """
    Admin interface for password history with version control.
    """
    list_display = ('user', 'created_at')
    list_filter = ('created_at',)
    search_fields = ('user__email',)
    readonly_fields = ('password_hash', 'created_at')
    ordering = ('-created_at',)
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if not request.user.is_superuser:
            return qs.filter(user__organization=request.user.organization)
        return qs
    
    def has_add_permission(self, request):
        """Prevent manual creation of password history entries"""
        return False


@admin.register(PasswordPolicy)
class PasswordPolicyAdmin(VersionAdmin):
    list_display = ('organization', 'min_length', 'history_count', 'enable_expiration', 'expiration_days', 'enable_lockout')
    list_filter = ('enable_expiration', 'enable_lockout', 'enable_breach_detection')
    search_fields = ('organization__name', 'organization__code')
    readonly_fields = ('created_at', 'updated_at')


@admin.register(AccountLockout)
class AccountLockoutAdmin(VersionAdmin):
    list_display = ('user', 'ip_address', 'failed_attempts', 'locked_at', 'expires_at', 'is_active', 'reason')
    list_filter = ('is_active', 'reason', 'locked_at')
    search_fields = ('user__email', 'ip_address', 'user_agent')


@admin.register(SecurityAuditLog)
class SecurityAuditLogAdmin(VersionAdmin):
    list_display = ('user', 'event_type', 'ip_address', 'timestamp')
    list_filter = ('event_type', 'timestamp')
    search_fields = ('user__email', 'ip_address', 'user_agent')
    
    def has_change_permission(self, request, obj=None):
        """Prevent editing of password history entries"""
        return False
