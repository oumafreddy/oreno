# oreno\apps\users\models.py
from datetime import timedelta
import logging

from django.conf import settings
from django.db import models
from django.utils import timezone
from django.contrib.auth.models import AbstractUser, Group, Permission
from django.utils.translation import gettext_lazy as _
from core.models.abstract_models import TimeStampedModel
from django.core.exceptions import ValidationError
from django.db.models import F
from django.utils.crypto import get_random_string
from django.core.mail import send_mail
from django.template.loader import render_to_string


logger = logging.getLogger(__name__)

def default_expiration():
    """Generate expiration time 10 minutes from now."""
    return timezone.now() + timedelta(minutes=10)

def default_datetime():
    """Provide a default timezone-aware datetime for registration."""
    return timezone.now()


def generate_otp_code():
    """Generate a random 6-digit numeric OTP code."""
    return get_random_string(6, allowed_chars='0123456789')


class CustomUser(AbstractUser):
    """
    Extended User model for multi-tenancy with additional fields.
    """
    ROLE_ADMIN = 'admin'
    ROLE_HEAD_OF_UNIT = 'head_of_unit'
    ROLE_MANAGER = 'manager'
    ROLE_STAFF = 'staff'
    ROLE_CHOICES = [
        (ROLE_ADMIN, _('Admin')),
        (ROLE_HEAD_OF_UNIT, _('Head of Unit')),
        (ROLE_MANAGER, _('Manager')),
        (ROLE_STAFF, _('Staff')),
    ]

    email = models.EmailField(
        unique=True,
        verbose_name=_("Email Address")
    )
    organization = models.ForeignKey(
        'organizations.Organization',
        on_delete=models.CASCADE,
        related_name='users',
        null=True,
        blank=True,
        verbose_name=_("Organization"),
        help_text=_("Organization this user belongs to.")
    )
    role = models.CharField(
        max_length=50,
        choices=ROLE_CHOICES,
        default=ROLE_STAFF,
        verbose_name=_("User Role"),
        help_text=_("Role of the user within their organization.")
    )
    registration_date = models.DateTimeField(
        default=default_datetime,
        verbose_name=_("Registration Date"),
        help_text=_("The date and time when the user registered.")
    )
    is_first_time_setup_complete = models.BooleanField(
        default=False,
        verbose_name=_("First Time Setup Complete"),
        help_text=_("Whether the user has completed their first-time setup (OTP verification and password reset).")
    )
    is_admin_created = models.BooleanField(
        default=False,
        verbose_name=_("Admin Created"),
        help_text=_("Whether this user was created by an admin (requires first-time setup).")
    )

    # Use email for authentication
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    # Permissions
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
        full = f"{self.first_name} {self.last_name}".strip()
        return full if full else self.username

    def has_org_admin_access(self, organization):
        """Check if user has admin access to the organization"""
        if self.is_superuser:
            return True
        from organizations.models import OrganizationUser
        return OrganizationUser.objects.filter(
            user=self,
            organization=organization,
            role__in=['admin', 'manager']
        ).exists()

    def has_audit_access(self, organization):
        """
        Check if user has audit access to the organization.
        Users with admin/manager roles or specific audit permissions have access.
        """
        if self.is_superuser:
            return True
        # Check if user has admin/manager role in the organization
        if self.has_org_admin_access(organization):
            return True
        from organizations.models import OrganizationUser
        return OrganizationUser.objects.filter(
            user=self,
            organization=organization,
            role__in=['admin', 'manager', 'staff']  # Staff can have audit access
        ).exists()

    def requires_first_time_setup(self):
        """
        Check if user requires first-time setup (OTP verification and password reset).
        """
        return not self.is_first_time_setup_complete

    def can_delete_users(self):
        """
        Check if user can delete other users.
        Only superusers can delete users, not organization admins.
        """
        return self.is_superuser


class Profile(models.Model):
    user = models.OneToOneField(
        CustomUser, on_delete=models.CASCADE, related_name='profile'
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
    organization = models.ForeignKey(
        'organizations.Organization', on_delete=models.CASCADE, related_name='roles'
    )
    user = models.ForeignKey(CustomUser, on_delete=models.CASCADE, related_name='user_roles')
    role = models.CharField(max_length=50, choices=CustomUser.ROLE_CHOICES, default=CustomUser.ROLE_STAFF)

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
    MAX_ATTEMPTS = 3
    OTP_LENGTH = 6

    user = models.ForeignKey(
        CustomUser, on_delete=models.CASCADE, related_name='otps'
    )
    otp = models.CharField(
        max_length=OTP_LENGTH,
        default=generate_otp_code,
        verbose_name=_("One-Time Password"),
        help_text=_("6-digit one-time verification code."),
    )
    is_verified = models.BooleanField(default=False)
    role = models.CharField(max_length=50, choices=CustomUser.ROLE_CHOICES, default=CustomUser.ROLE_STAFF)
    attempts = models.PositiveSmallIntegerField(default=0)
    expires_at = models.DateTimeField(default=default_expiration)
    created_at = models.DateTimeField(auto_now_add=True)
    is_expired = models.BooleanField(default=False)

    class Meta:
        verbose_name = _("OTP")
        verbose_name_plural = _("OTPs")
        indexes = [
            models.Index(fields=['user', 'is_verified']),
            models.Index(fields=['otp']),
            models.Index(fields=['expires_at']),
        ]
        ordering = ['-created_at']

    def __str__(self):
        return f"OTP for {self.user.email} - {self.otp} (Verified: {self.is_verified})"

    def clean(self):
        valid_roles = [r[0] for r in self._meta.get_field('role').choices]
        if self.role not in valid_roles:
            raise ValidationError({'role': _(f"Invalid role. Valid: {', '.join(valid_roles)}")})
        if not self.otp.isdigit() or len(self.otp) != self.OTP_LENGTH:
            raise ValidationError({'otp': _(f"OTP must be {self.OTP_LENGTH}-digit")})

    def save(self, *args, **kwargs):
        if not self.otp:
            self.otp = generate_otp_code()
        super().save(*args, **kwargs)

    def has_expired(self):
        return timezone.now() > self.expires_at

    def is_valid(self):
        return not self.has_expired() and self.attempts < self.MAX_ATTEMPTS

    def increment_attempts(self):
        self.attempts = F('attempts') + 1
        self.save(update_fields=['attempts'])
        self.refresh_from_db(fields=['attempts'])

    def verify(self, code):
        if self.is_verified:
            return True
        if not self.is_valid():
            return False
        if self.otp == code:
            self.is_verified = True
            self.save(update_fields=['is_verified'])
            return True
        self.increment_attempts()
        return False

    @classmethod
    def cleanup_expired(cls):
        cls.objects.filter(expires_at__lte=timezone.now()).delete()

    def send_via_email(self):
        subject = "Your OTP Code"
        message = render_to_string('users/email/otp.txt', {
            'user': self.user,
            'otp': self.otp,
            'expires_at': self.expires_at
        })
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [self.user.email],
            fail_silently=False
        )


class PasswordHistory(models.Model):
    """
    Model to track password history for preventing password reuse.
    """
    user = models.ForeignKey(
        CustomUser, 
        on_delete=models.CASCADE, 
        related_name='password_history'
    )
    password_hash = models.CharField(
        max_length=255,
        verbose_name=_("Password Hash"),
        help_text=_("Hashed version of the password")
    )
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_("Created At"),
        help_text=_("When this password was set")
    )
    
    class Meta:
        verbose_name = _("Password History")
        verbose_name_plural = _("Password Histories")
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'created_at']),
        ]
    
    def __str__(self):
        return f"Password history for {self.user.email} at {self.created_at}"
    
    @classmethod
    def store_password(cls, user, password):
        """
        Store a password hash in the history.
        """
        from django.contrib.auth.hashers import make_password
        password_hash = make_password(password)
        cls.objects.create(user=user, password_hash=password_hash)
    
    @classmethod
    def is_password_reused(cls, user, password, history_count=5):
        """
        Check if a password has been used recently.
        Returns True if the password is found in recent history.
        """
        from django.contrib.auth.hashers import check_password
        
        # Get the most recent password history entries
        recent_passwords = cls.objects.filter(user=user).order_by('-created_at')[:history_count]
        
        for password_record in recent_passwords:
            if check_password(password, password_record.password_hash):
                return True
        
        return False
    
    @classmethod
    def cleanup_old_passwords(cls, user, keep_count=10):
        """
        Remove old password history entries, keeping only the most recent ones.
        """
        all_passwords = cls.objects.filter(user=user).order_by('-created_at')
        if all_passwords.count() > keep_count:
            passwords_to_delete = all_passwords[keep_count:]
            passwords_to_delete.delete()
