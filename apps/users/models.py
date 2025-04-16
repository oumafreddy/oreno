"""
Users Models

This module defines:
    - CustomUser: An extended user model with multi-tenant support.
    - Profile: Additional user profile information.
    - OrganizationRole: Tracks the role of a user within an organization.
    - OTP: One-Time Password model for user verification.

Each model includes:
    - Verbose names and help texts to improve clarity.
    - Proper indexing for performance.
    - Relationships that integrate with the organizations app.
"""

from datetime import datetime
import os

from django.db import models
from django_ckeditor_5.fields import CKEditor5Field
from django.conf import settings
from django.utils.timezone import make_aware
from django.contrib.auth.models import AbstractUser, Group, Permission
from django.utils.translation import gettext_lazy as _

# You can eventually move this helper into a shared utilities module.
def default_datetime():
    """
    Provide a default timezone-aware datetime.
    This default is used for the user registration date.
    """
    dt = datetime(2024, 8, 1, 0, 0)
    return make_aware(dt)

class CustomUser(AbstractUser):
    """
    Extended User model for multi-tenancy with additional fields.
    
    Fields include:
        - email: Used as the unique identifier for authentication.
        - organization: The tenant association (optional for some users).
        - role: The role of the user (e.g., staff, manager, admin).
        - registration_date: When the user registered.
    
    The USERNAME_FIELD is set to email, and REQUIRED_FIELDS must include 'username'.
    """
    email = models.EmailField(
        unique=True,
        verbose_name=_("Email Address")
    )
    organization = models.ForeignKey(
        'organizations.Organization',  # Use string reference for decoupling apps
        on_delete=models.CASCADE,
        related_name='users',
        null=True,
        blank=True,
        verbose_name=_("Organization")
    )
    role = models.CharField(
        max_length=128,
        default='staff',
        verbose_name=_("User Role"),
        help_text=_("Defines the role assigned to the user.")
    )
    registration_date = models.DateTimeField(
        default=default_datetime,
        verbose_name=_("Registration Date"),
        help_text=_("The date and time when the user registered.")
    )
    
    # Use email as the unique user identifier.
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']
    
    # Override the built-in groups and permissions to use custom related names.
    groups = models.ManyToManyField(
        Group,
        related_name='customuser_set',
        blank=True,
        verbose_name=_("Groups"),
        help_text=_("The groups this user belongs to.")
    )
    user_permissions = models.ManyToManyField(
        Permission,
        related_name='customuser_set',
        blank=True,
        verbose_name=_("User Permissions"),
        help_text=_("Specific permissions granted to the user.")
    )
    
    class Meta:
        verbose_name = _("User")
        verbose_name_plural = _("Users")
        indexes = [
            models.Index(fields=['email']),
            models.Index(fields=['organization']),
            models.Index(fields=['role']),
        ]
    
    def __str__(self):
        return self.email
    
    def get_full_name(self):
        """
        Return the user's full name if available, or fall back to username.
        """
        full_name = f"{self.first_name} {self.last_name}".strip()
        return full_name if full_name else self.username
    
    # In your custom user model
    def has_org_admin_access(self, organization):
        return self.organization == organization and \
            self.roles.filter(role='admin').exists()

class Profile(models.Model):
    """
    Profile model for storing additional information for a user.
    
    Each profile is linked one-to-one with a CustomUser.
    """
    user = models.OneToOneField(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='profile',
        verbose_name=_("User")
    )
    avatar = models.ImageField(
        upload_to='avatars/',
        default='default-avatar.png',
        verbose_name=_("Profile Picture"),
        help_text=_("User's avatar image.")
    )
    
    class Meta:
        verbose_name = _("User Profile")
        verbose_name_plural = _("User Profiles")
    
    def __str__(self):
        return f"Profile for {self.user.email}"

class OrganizationRole(models.Model):
    """
    Model for managing the role of a user within a specific organization.
    
    This model establishes a many-to-one relation with both Organization and CustomUser,
    allowing each user to have a distinct role in the context of an organization.
    """
    # Optionally, you could inherit from a TimeStampedModel for audit trails.
    organization = models.ForeignKey(
        'organizations.Organization',
        on_delete=models.CASCADE,
        related_name='roles',
        verbose_name=_("Organization")
    )
    user = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='user_roles',
        verbose_name=_("User")
    )
    role = models.CharField(
        max_length=50,
        choices=[
            ('admin', _("Admin")),
            ('manager', _("Manager")),
            ('staff', _("Staff")),
        ],
        default='staff',
        db_index=True,
        verbose_name=_("Role"),
        help_text=_("Role of the user within the organization.")
    )
    
    class Meta:
        verbose_name = _("Organization Role")
        verbose_name_plural = _("Organization Roles")
        unique_together = ['organization', 'user']
        indexes = [
            models.Index(fields=['organization', 'role']),
            models.Index(fields=['user', 'role']),
        ]
    
    def __str__(self):
        return f"{self.user.email} as {self.get_role_display()} in {self.organization}"

class OTP(models.Model):
    """
    One-Time Password (OTP) model for verifying a user's identity.
    
    OTPs are associated with a user and are used to enhance security during critical operations.
    """
    # Optionally, you could inherit timestamps from a TimeStampedModel.
    user = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='otps',
        verbose_name=_("User")
    )
    otp = models.CharField(
        max_length=6,
        verbose_name=_("One-Time Password"),
        help_text=_("The OTP code for verification.")
    )
    is_verified = models.BooleanField(
        default=False,
        verbose_name=_("Verification Status"),
        help_text=_("Indicates whether this OTP has been verified.")
    )
    role = models.CharField(
        max_length=50,
        choices=[
            ('admin', _("Admin")),
            ('manager', _("Manager")),
            ('staff', _("Staff")),
        ],
        default='staff',
        verbose_name=_("Role"),
        help_text=_("Role context for the OTP usage.")
    )
    
    class Meta:
        verbose_name = _("OTP")
        verbose_name_plural = _("OTPs")
        indexes = [
            models.Index(fields=['user', 'is_verified']),
            models.Index(fields=['otp']),
        ]
    
    def __str__(self):
        return f"OTP for {self.user.email} - {self.otp} (Verified: {self.is_verified})"
