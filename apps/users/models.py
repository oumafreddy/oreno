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
from core.utils import send_tenant_email as send_mail
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
    ROLE_RISK_CHAMPION = 'risk_champion'
    ROLE_MANAGER = 'manager'
    ROLE_STAFF = 'staff'
    ROLE_CHOICES = [
        (ROLE_ADMIN, _('Admin')),
        (ROLE_HEAD_OF_UNIT, _('Head of Unit')),
        (ROLE_RISK_CHAMPION, _('Risk Champion')),
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
        
        # Try tenant email first, fallback to standard Django send_mail
        try:
            send_mail(
                subject,
                message,
                settings.DEFAULT_FROM_EMAIL,
                [self.user.email],
                fail_silently=False
            )
        except Exception as e:
            # Log the error and try fallback
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Tenant email failed for OTP, trying fallback: {e}")
            
            # Fallback to Django's standard send_mail
            from django.core.mail import send_mail as django_send_mail
            django_send_mail(
                subject,
                message,
                settings.DEFAULT_FROM_EMAIL,
                [self.user.email],
                fail_silently=False
            )


class PasswordHistory(models.Model):
    """
    Enhanced model to track password history for preventing password reuse and security auditing.
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
    expires_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_("Expires At"),
        help_text=_("When this password expires (if password expiration is enabled)")
    )
    is_compromised = models.BooleanField(
        default=False,
        verbose_name=_("Is Compromised"),
        help_text=_("Whether this password was found in data breaches")
    )
    breach_count = models.PositiveIntegerField(
        default=0,
        verbose_name=_("Breach Count"),
        help_text=_("Number of data breaches this password was found in")
    )
    last_checked = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_("Last Checked"),
        help_text=_("When this password was last checked against breach databases")
    )
    change_reason = models.CharField(
        max_length=50,
        choices=[
            ('initial', _('Initial Password')),
            ('reset', _('Password Reset')),
            ('change', _('User Change')),
            ('admin', _('Admin Change')),
            ('expired', _('Password Expired')),
            ('compromised', _('Password Compromised')),
            ('policy', _('Policy Update')),
        ],
        default='change',
        verbose_name=_("Change Reason"),
        help_text=_("Reason for password change")
    )
    
    class Meta:
        verbose_name = _("Password History")
        verbose_name_plural = _("Password Histories")
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['user', 'created_at']),
            models.Index(fields=['user', 'is_compromised']),
            models.Index(fields=['expires_at']),
        ]
    
    def __str__(self):
        return f"Password history for {self.user.email} at {self.created_at}"
    
    @classmethod
    def store_password(cls, user, password, reason='change', expires_in_days=None, is_hashed=False):
        """
        Store a password hash in the history with enhanced features.
        """
        from django.contrib.auth.hashers import make_password
        from django.utils import timezone
        
        password_hash = password if is_hashed else make_password(password)
        
        # Calculate expiration if specified
        expires_at = None
        if expires_in_days:
            expires_at = timezone.now() + timezone.timedelta(days=expires_in_days)
        
        # Check if password is compromised
        is_compromised, breach_count = cls._check_password_breach(password)
        
        return cls.objects.create(
            user=user,
            password_hash=password_hash,
            expires_at=expires_at,
            is_compromised=is_compromised,
            breach_count=breach_count,
            last_checked=timezone.now(),
            change_reason=reason
        )
    
    @classmethod
    def is_password_reused(cls, user, password, history_count=8):
        """
        Enhanced check if a password has been used recently.
        Returns True if the password is found in recent history.
        """
        from django.contrib.auth.hashers import check_password
        
        # If the user instance is not saved yet (no primary key),
        # there cannot be any password history. Short-circuit safely.
        if not getattr(user, 'pk', None):
            return False

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
    
    @classmethod
    def get_expired_passwords(cls):
        """
        Get all expired passwords that need to be changed.
        """
        from django.utils import timezone
        return cls.objects.filter(
            expires_at__lt=timezone.now(),
            expires_at__isnull=False
        ).select_related('user')
    
    @classmethod
    def get_compromised_passwords(cls):
        """
        Get all compromised passwords that need to be changed.
        """
        return cls.objects.filter(
            is_compromised=True
        ).select_related('user')
    
    @classmethod
    def _check_password_breach(cls, password):
        """
        Check if password has been compromised using HaveIBeenPwned API.
        Returns (is_compromised, breach_count)
        """
        import hashlib
        import requests
        from django.core.cache import cache
        from django.conf import settings
        
        try:
            # Create SHA-1 hash of password
            password_hash = hashlib.sha1(password.encode('utf-8')).hexdigest().upper()
            prefix = password_hash[:5]
            suffix = password_hash[5:]
            
            # Check cache first
            cache_key = f"pwned_password_{prefix}"
            cached_results = cache.get(cache_key)
            
            if cached_results is None:
                # Make API request
                response = requests.get(f"https://api.pwnedpasswords.com/range/{prefix}", timeout=5)
                if response.status_code == 200:
                    cached_results = response.text
                    cache.set(cache_key, cached_results, 3600)  # Cache for 1 hour
                else:
                    return False, 0
            
            # Check if our password hash suffix is in the results
            for line in cached_results.split('\n'):
                if line.startswith(suffix):
                    count = int(line.split(':')[1])
                    return True, count
            
            return False, 0
            
        except Exception:
            # If API check fails, assume not compromised
            return False, 0
    
    @classmethod
    def update_breach_status(cls, user=None):
        """
        Update breach status for password history entries.
        If user is specified, only update for that user.
        """
        from django.utils import timezone
        
        queryset = cls.objects.all()
        if user:
            queryset = queryset.filter(user=user)
        
        # Only check passwords that haven't been checked recently (within 24 hours)
        queryset = queryset.filter(
            models.Q(last_checked__isnull=True) |
            models.Q(last_checked__lt=timezone.now() - timezone.timedelta(hours=24))
        )
        
        updated_count = 0
        for password_record in queryset:
            # We can't check the actual password since we only store hashes
            # This would need to be done when the password is first set
            # For now, we'll just update the last_checked timestamp
            password_record.last_checked = timezone.now()
            password_record.save(update_fields=['last_checked'])
            updated_count += 1
        
        return updated_count
    
    def is_expired(self):
        """
        Check if this password has expired.
        """
        from django.utils import timezone
        return self.expires_at and self.expires_at < timezone.now()
    
    def days_until_expiry(self):
        """
        Get number of days until password expires.
        Returns None if no expiration is set.
        """
        from django.utils import timezone
        if not self.expires_at:
            return None
        
        delta = self.expires_at - timezone.now()
        return delta.days


class PasswordPolicy(models.Model):
    """
    Model to store password policies for organizations.
    """
    organization = models.OneToOneField(
        'organizations.Organization',
        on_delete=models.CASCADE,
        related_name='password_policy',
        verbose_name=_("Organization")
    )
    
    # Password complexity requirements
    min_length = models.PositiveIntegerField(
        default=12,
        verbose_name=_("Minimum Length"),
        help_text=_("Minimum password length")
    )
    max_length = models.PositiveIntegerField(
        default=128,
        verbose_name=_("Maximum Length"),
        help_text=_("Maximum password length")
    )
    require_uppercase = models.BooleanField(
        default=True,
        verbose_name=_("Require Uppercase"),
        help_text=_("Require at least one uppercase letter")
    )
    require_lowercase = models.BooleanField(
        default=True,
        verbose_name=_("Require Lowercase"),
        help_text=_("Require at least one lowercase letter")
    )
    require_digits = models.BooleanField(
        default=True,
        verbose_name=_("Require Digits"),
        help_text=_("Require at least one digit")
    )
    require_special = models.BooleanField(
        default=True,
        verbose_name=_("Require Special Characters"),
        help_text=_("Require at least one special character")
    )
    
    # Password history
    history_count = models.PositiveIntegerField(
        default=8,
        verbose_name=_("History Count"),
        help_text=_("Number of previous passwords to remember")
    )
    
    # Password expiration
    enable_expiration = models.BooleanField(
        default=True,
        verbose_name=_("Enable Password Expiration"),
        help_text=_("Enable password expiration")
    )
    expiration_days = models.PositiveIntegerField(
        default=90,
        verbose_name=_("Expiration Days"),
        help_text=_("Number of days before password expires")
    )
    warning_days = models.PositiveIntegerField(
        default=14,
        verbose_name=_("Warning Days"),
        help_text=_("Days before expiration to show warning")
    )
    
    # Account lockout
    enable_lockout = models.BooleanField(
        default=True,
        verbose_name=_("Enable Account Lockout"),
        help_text=_("Enable account lockout after failed attempts")
    )
    max_failed_attempts = models.PositiveIntegerField(
        default=5,
        verbose_name=_("Max Failed Attempts"),
        help_text=_("Maximum failed login attempts before lockout")
    )
    lockout_duration_minutes = models.PositiveIntegerField(
        default=15,
        verbose_name=_("Lockout Duration (minutes)"),
        help_text=_("Duration of account lockout in minutes")
    )
    
    # Breach detection
    enable_breach_detection = models.BooleanField(
        default=True,
        verbose_name=_("Enable Breach Detection"),
        help_text=_("Check passwords against known data breaches")
    )
    
    # Created/Updated timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        CustomUser,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='created_password_policies',
        verbose_name=_("Created By")
    )
    updated_by = models.ForeignKey(
        CustomUser,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='updated_password_policies',
        verbose_name=_("Updated By")
    )
    
    class Meta:
        verbose_name = _("Password Policy")
        verbose_name_plural = _("Password Policies")
    
    def __str__(self):
        return f"Password Policy for {self.organization.name}"
    
    def get_validators(self):
        """
        Get list of password validators based on this policy.
        """
        from .validators import (
            EnhancedPasswordStrengthValidator,
            PasswordHistoryValidator,
            PasswordBreachValidator,
            PasswordComplexityValidator
        )
        
        validators = []
        
        # Add enhanced strength validator
        validators.append(EnhancedPasswordStrengthValidator(
            min_length=self.min_length,
            max_length=self.max_length
        ))
        
        # Add complexity validator
        validators.append(PasswordComplexityValidator(
            require_uppercase=self.require_uppercase,
            require_lowercase=self.require_lowercase,
            require_digits=self.require_digits,
            require_special=self.require_special,
            min_length=self.min_length
        ))
        
        # Add history validator
        validators.append(PasswordHistoryValidator(
            history_count=self.history_count
        ))
        
        # Add breach detection validator
        if self.enable_breach_detection:
            validators.append(PasswordBreachValidator())
        
        return validators


class AccountLockout(models.Model):
    """
    Model to track account lockouts for security.
    """
    user = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='lockouts',
        verbose_name=_("User")
    )
    ip_address = models.GenericIPAddressField(
        verbose_name=_("IP Address"),
        help_text=_("IP address that triggered the lockout")
    )
    user_agent = models.TextField(
        blank=True,
        verbose_name=_("User Agent"),
        help_text=_("Browser/user agent that triggered the lockout")
    )
    failed_attempts = models.PositiveIntegerField(
        default=1,
        verbose_name=_("Failed Attempts"),
        help_text=_("Number of failed login attempts")
    )
    locked_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_("Locked At"),
        help_text=_("When the account was locked")
    )
    expires_at = models.DateTimeField(
        verbose_name=_("Expires At"),
        help_text=_("When the lockout expires")
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name=_("Is Active"),
        help_text=_("Whether this lockout is currently active")
    )
    reason = models.CharField(
        max_length=100,
        default='failed_login',
        choices=[
            ('failed_login', _('Failed Login Attempts')),
            ('suspicious_activity', _('Suspicious Activity')),
            ('admin_lock', _('Administrative Lock')),
            ('compromised', _('Account Compromised')),
        ],
        verbose_name=_("Reason"),
        help_text=_("Reason for the lockout")
    )
    
    class Meta:
        verbose_name = _("Account Lockout")
        verbose_name_plural = _("Account Lockouts")
        ordering = ['-locked_at']
        indexes = [
            models.Index(fields=['user', 'is_active']),
            models.Index(fields=['ip_address', 'is_active']),
            models.Index(fields=['expires_at']),
        ]
    
    def __str__(self):
        return f"Lockout for {self.user.email} at {self.locked_at}"
    
    @classmethod
    def is_user_locked(cls, user, ip_address=None):
        """
        Check if a user is currently locked out.
        """
        from django.utils import timezone
        
        queryset = cls.objects.filter(
            user=user,
            is_active=True,
            expires_at__gt=timezone.now()
        )
        
        if ip_address:
            queryset = queryset.filter(ip_address=ip_address)
        
        return queryset.exists()
    
    @classmethod
    def record_failed_attempt(cls, user, ip_address, user_agent=''):
        """
        Record a failed login attempt and potentially lock the account.
        """
        from django.utils import timezone
        
        # Get or create lockout record
        lockout, created = cls.objects.get_or_create(
            user=user,
            ip_address=ip_address,
            is_active=True,
            defaults={
                'user_agent': user_agent,
                'failed_attempts': 1,
                'expires_at': timezone.now() + timezone.timedelta(minutes=15)
            }
        )
        
        if not created:
            lockout.failed_attempts += 1
            lockout.user_agent = user_agent
            lockout.save(update_fields=['failed_attempts', 'user_agent'])
        
        # Check if we should extend the lockout
        policy = getattr(user.organization, 'password_policy', None)
        if policy and policy.enable_lockout:
            if lockout.failed_attempts >= policy.max_failed_attempts:
                lockout.expires_at = timezone.now() + timezone.timedelta(
                    minutes=policy.lockout_duration_minutes
                )
                lockout.save(update_fields=['expires_at'])
        
        return lockout
    
    @classmethod
    def clear_user_lockouts(cls, user, ip_address=None):
        """
        Clear all active lockouts for a user.
        """
        queryset = cls.objects.filter(user=user, is_active=True)
        if ip_address:
            queryset = queryset.filter(ip_address=ip_address)
        
        queryset.update(is_active=False)
    
    @classmethod
    def cleanup_expired_lockouts(cls):
        """
        Clean up expired lockouts.
        """
        from django.utils import timezone
        
        expired_count = cls.objects.filter(
            expires_at__lt=timezone.now(),
            is_active=True
        ).update(is_active=False)
        
        return expired_count


class SecurityAuditLog(models.Model):
    """
    Model to log security-related events for audit purposes.
    """
    user = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='security_audit_logs',
        verbose_name=_("User")
    )
    event_type = models.CharField(
        max_length=50,
        choices=[
            ('login_success', _('Successful Login')),
            ('login_failed', _('Failed Login')),
            ('logout', _('Logout')),
            ('password_change', _('Password Changed')),
            ('password_reset', _('Password Reset')),
            ('account_locked', _('Account Locked')),
            ('account_unlocked', _('Account Unlocked')),
            ('password_expired', _('Password Expired')),
            ('password_compromised', _('Password Compromised')),
            ('suspicious_activity', _('Suspicious Activity')),
            ('admin_action', _('Administrative Action')),
        ],
        verbose_name=_("Event Type")
    )
    ip_address = models.GenericIPAddressField(
        verbose_name=_("IP Address")
    )
    user_agent = models.TextField(
        blank=True,
        verbose_name=_("User Agent")
    )
    details = models.JSONField(
        default=dict,
        verbose_name=_("Event Details"),
        help_text=_("Additional details about the event")
    )
    timestamp = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_("Timestamp")
    )
    organization = models.ForeignKey(
        'organizations.Organization',
        on_delete=models.CASCADE,
        related_name='security_audit_logs',
        verbose_name=_("Organization")
    )
    
    class Meta:
        verbose_name = _("Security Audit Log")
        verbose_name_plural = _("Security Audit Logs")
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['user', 'event_type']),
            models.Index(fields=['organization', 'timestamp']),
            models.Index(fields=['ip_address', 'timestamp']),
            models.Index(fields=['event_type', 'timestamp']),
        ]
    
    def __str__(self):
        return f"{self.event_type} for {self.user.email} at {self.timestamp}"
    
    @classmethod
    def log_event(cls, user, event_type, ip_address, user_agent='', details=None):
        """
        Log a security event.
        """
        return cls.objects.create(
            user=user,
            event_type=event_type,
            ip_address=ip_address,
            user_agent=user_agent,
            details=details or {},
            organization=user.organization
        )
    
    @classmethod
    def get_user_events(cls, user, event_types=None, days=30):
        """
        Get security events for a user.
        """
        from django.utils import timezone
        from datetime import timedelta
        
        queryset = cls.objects.filter(
            user=user,
            timestamp__gte=timezone.now() - timedelta(days=days)
        )
        
        if event_types:
            queryset = queryset.filter(event_type__in=event_types)
        
        return queryset.order_by('-timestamp')
    
    @classmethod
    def get_organization_events(cls, organization, event_types=None, days=30):
        """
        Get security events for an organization.
        """
        from django.utils import timezone
        from datetime import timedelta
        
        queryset = cls.objects.filter(
            organization=organization,
            timestamp__gte=timezone.now() - timedelta(days=days)
        )
        
        if event_types:
            queryset = queryset.filter(event_type__in=event_types)
        
        return queryset.order_by('-timestamp')
