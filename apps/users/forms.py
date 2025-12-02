# apps/users/forms.py
import logging
from django import forms
from django.contrib.auth.forms import UserCreationForm, UserChangeForm, SetPasswordForm
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError
from django.contrib.auth import password_validation
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Submit, Row, Column, Fieldset, ButtonHolder, HTML
from crispy_bootstrap5.bootstrap5 import FloatingField
from django.utils.html import format_html, format_html_join

from users.models import CustomUser, Profile, OrganizationRole, PasswordPolicy
from users.validators import (
    validate_password_strength, 
    get_password_strength_score,
    EnhancedPasswordStrengthValidator,
    PasswordComplexityValidator,
    PasswordHistoryValidator,
    PasswordBreachValidator
)

logger = logging.getLogger(__name__)

def get_password_policy_hints(user=None, organization=None):
    """
    Generate password policy hints based on organization policy or defaults.
    """
    hints = []
    
    # Get policy from user's organization or provided organization
    policy = None
    if user and user.organization:
        try:
            policy = user.organization.password_policy
        except PasswordPolicy.DoesNotExist:
            pass
    elif organization:
        try:
            policy = organization.password_policy
        except PasswordPolicy.DoesNotExist:
            pass
    
    if policy:
        # Use organization-specific policy
        if policy.min_length:
            hints.append(f"At least {policy.min_length} characters")
        if policy.require_uppercase:
            hints.append("One uppercase letter (A-Z)")
        if policy.require_lowercase:
            hints.append("One lowercase letter (a-z)")
        if policy.require_digits:
            hints.append("One number (0-9)")
        if policy.require_special:
            hints.append("One special character (!@#$%^&*)")
        if policy.history_count:
            hints.append(f"Different from your last {policy.history_count} passwords")
        if policy.enable_breach_detection:
            hints.append("Not found in known data breaches")
    else:
        # Use default hints
        hints = [
            "At least 12 characters",
            "One uppercase letter (A-Z)",
            "One lowercase letter (a-z)", 
            "One number (0-9)",
            "One special character (!@#$%^&*)",
            "Different from your last 8 passwords",
            "Not found in known data breaches"
        ]
    
    return hints

def render_password_policy_hints(user=None, organization=None):
    """
    Render password policy hints as HTML.
    """
    hints = get_password_policy_hints(user, organization)
    
    if not hints:
        return ""
    
    hint_items = []
    for hint in hints:
        hint_items.append(f'<li class="text-muted small">{hint}</li>')
    
    return format_html(
        '<div class="password-policy-hints mt-2">'
        '<small class="text-muted"><strong>Password Requirements:</strong></small>'
        '<ul class="list-unstyled mt-1 mb-0">'
        '{}'
        '</ul>'
        '</div>',
        format_html_join('', '{}', hint_items)
    )

class BaseUserForm(forms.ModelForm):
    """Base form with common functionality for user-related forms"""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_tag = False
        self.helper.layout = Layout(
            Fieldset(
                _('Basic Information'),
                Row(
                    Column('email', css_class='col-md-6'),
                    Column('username', css_class='col-md-6'),
                ),
                Row(
                    Column('first_name', css_class='col-md-6'),
                    Column('last_name', css_class='col-md-6'),
                ),
            ),
            Fieldset(
                _('Organization'),
                Row(
                    Column('organization', css_class='col-md-6'),
                    Column('role', css_class='col-md-6'),
                ),
            ),
            ButtonHolder(
                Submit('submit', _('Save'), css_class='btn-primary'),
                css_class='mt-3'
            )
        )

class EnhancedPasswordField(forms.CharField):
    """
    Enhanced password field with strength validation and visual feedback.
    """
    def __init__(self, *args, **kwargs):
        kwargs.setdefault('widget', forms.PasswordInput(attrs={
            'class': 'form-control',
            'data-toggle': 'password',
            'autocomplete': 'new-password'
        }))
        kwargs.setdefault('min_length', 12)
        super().__init__(*args, **kwargs)
        self.user = None
    
    def validate(self, value):
        super().validate(value)
        if value:
            # Get organization-specific validators if available
            validators = self._get_validators()
            for validator in validators:
                validator.validate(value, self.user if hasattr(self, 'user') else None)
    
    def _get_validators(self):
        """Get password validators based on organization policy."""
        validators = [
            EnhancedPasswordStrengthValidator(),
            PasswordComplexityValidator(),
        ]
        
        # Add organization-specific validators if available
        if hasattr(self, 'user') and self.user and self.user.organization:
            try:
                policy = self.user.organization.password_policy
                if policy:
                    validators = policy.get_validators()
            except PasswordPolicy.DoesNotExist:
                pass
        
        return validators

    def set_user(self, user):
        """Set the user for policy-based validation."""
        self.user = user

class CustomUserCreationForm(BaseUserForm, UserCreationForm):
    password1 = EnhancedPasswordField(
        label=_("Password"),
        strip=False,
        help_text=_("Create a strong password that meets security requirements."),
    )
    password2 = forms.CharField(
        label=_("Password confirmation"),
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'autocomplete': 'new-password'
        }),
        strip=False,
        help_text=_("Enter the same password as before, for verification."),
    )

    class Meta:
        model = CustomUser
        fields = ('email', 'username', 'first_name', 'last_name', 'organization', 'role')
        widgets = {
            'organization': forms.Select(attrs={'class': 'form-select'}),
            'role': forms.Select(attrs={'class': 'form-select'}),
        }

    def __init__(self, *args, **kwargs):
        organization = kwargs.pop('organization', None)
        super().__init__(*args, **kwargs)
        
        # Set organization for policy hints
        self.organization = organization
        
        # Add password strength meter
        self.helper.layout = Layout(
            Fieldset(
                _('Basic Information'),
                Row(
                    Column('email', css_class='col-md-6'),
                    Column('username', css_class='col-md-6'),
                ),
                Row(
                    Column('first_name', css_class='col-md-6'),
                    Column('last_name', css_class='col-md-6'),
                ),
            ),
            Fieldset(
                _('Organization'),
                Row(
                    Column('organization', css_class='col-md-6'),
                    Column('role', css_class='col-md-6'),
                ),
            ),
            Fieldset(
                _('Password'),
                'password1',
                HTML('<div id="password-strength-meter" class="mt-2"></div>'),
                HTML(render_password_policy_hints(organization=organization)),
                'password2',
            ),
            ButtonHolder(
                Submit('submit', _('Create Account'), css_class='btn-primary'),
                css_class='mt-3'
            )
        )

class AdminUserCreationForm(BaseUserForm, UserCreationForm):
    """
    Form for admin users to create users within their organization.
    Organization field is pre-filled and hidden.
    """
    password1 = EnhancedPasswordField(
        label=_("Password"),
        strip=False,
        help_text=_("Create a strong password that meets security requirements."),
    )
    password2 = forms.CharField(
        label=_("Password confirmation"),
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'autocomplete': 'new-password'
        }),
        strip=False,
        help_text=_("Enter the same password as before, for verification."),
    )

    class Meta:
        model = CustomUser
        fields = ('email', 'username', 'first_name', 'last_name', 'organization', 'role')
        widgets = {
            'organization': forms.HiddenInput(),
            'role': forms.Select(attrs={'class': 'form-select'}),
        }

    def __init__(self, *args, **kwargs):
        organization = kwargs.pop('organization', None)
        super().__init__(*args, **kwargs)
        
        if organization:
            self.fields['organization'].initial = organization
            self.fields['organization'].widget = forms.HiddenInput()
            self.organization = organization
        
        # Update layout to remove organization field from display
        self.helper.layout = Layout(
            Fieldset(
                _('Basic Information'),
                Row(
                    Column('email', css_class='col-md-6'),
                    Column('username', css_class='col-md-6'),
                ),
                Row(
                    Column('first_name', css_class='col-md-6'),
                    Column('last_name', css_class='col-md-6'),
                ),
            ),
            Fieldset(
                _('Organization'),
                'organization',  # Hidden field
                Row(
                    Column('role', css_class='col-md-6'),
                ),
            ),
            Fieldset(
                _('Password'),
                'password1',
                HTML('<div id="password-strength-meter" class="mt-2"></div>'),
                HTML(render_password_policy_hints(organization=organization)),
                'password2',
            ),
            ButtonHolder(
                Submit('submit', _('Create User'), css_class='btn-primary'),
                css_class='mt-3'
            )
        )

    def clean_password2(self):
        password1 = self.cleaned_data.get("password1")
        password2 = self.cleaned_data.get("password2")
        if password1 and password2 and password1 != password2:
            raise ValidationError(
                _("The two password fields didn't match."),
                code='password_mismatch',
            )
        return password2

    def _post_clean(self):
        super()._post_clean()
        password = self.cleaned_data.get('password2')
        if password:
            try:
                password_validation.validate_password(password, self.instance)
            except ValidationError as error:
                self.add_error('password2', error)

class CustomUserChangeForm(BaseUserForm, UserChangeForm):
    class Meta:
        model = CustomUser
        fields = ('email', 'username', 'first_name', 'last_name', 'organization', 'role', 'password_expiration_period')
        widgets = {
            'organization': forms.Select(attrs={'class': 'form-select'}),
            'role': forms.Select(attrs={'class': 'form-select'}),
            'password_expiration_period': forms.Select(attrs={'class': 'form-select'}),
        }

    def __init__(self, *args, **kwargs):
        # Extract the current user from kwargs to check if they're admin
        self.current_user = kwargs.pop('current_user', None)
        super().__init__(*args, **kwargs)
        
        # If current user is not admin, disable the role field
        if self.current_user and self.current_user.role != CustomUser.ROLE_ADMIN:
            self.fields['role'].widget.attrs['disabled'] = True
            self.fields['role'].widget.attrs['class'] = 'form-select form-control-plaintext'
            self.fields['role'].help_text = _("Only administrators can change user roles.")

    def clean(self):
        cleaned_data = super().clean()
        
        # If current user is not admin and role field is disabled, preserve the original role
        if self.current_user and self.current_user.role != CustomUser.ROLE_ADMIN:
            if self.instance and self.instance.pk:
                cleaned_data['role'] = self.instance.role
        
        return cleaned_data

class ProfileForm(forms.ModelForm):
    class Meta:
        model = Profile
        fields = ('avatar',)
        widgets = {
            'avatar': forms.ClearableFileInput(attrs={'class': 'form-control-file'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_tag = False
        self.helper.layout = Layout(
            Fieldset(
                _('Profile Picture'),
                'avatar',
            ),
            ButtonHolder(
                Submit('submit', _('Save'), css_class='btn-primary'),
                css_class='mt-3'
            )
        )

class OrganizationRoleForm(forms.ModelForm):
    class Meta:
        model = OrganizationRole
        fields = ('user', 'role')
        widgets = {
            'user': forms.Select(attrs={'class': 'form-select'}),
            'role': forms.Select(attrs={'class': 'form-select'}),
        }

    def __init__(self, *args, **kwargs):
        organization = kwargs.pop('organization', None)
        super().__init__(*args, **kwargs)
        
        if organization:
            self.fields['user'].queryset = CustomUser.objects.filter(
                organization=organization
            )
        
        self.helper = FormHelper()
        self.helper.form_tag = False
        self.helper.layout = Layout(
            Fieldset(
                _('Role Assignment'),
                Row(
                    Column('user', css_class='col-md-6'),
                    Column('role', css_class='col-md-6'),
                ),
            ),
            ButtonHolder(
                Submit('submit', _('Save'), css_class='btn-primary'),
                css_class='mt-3'
            )
        )

    def clean(self):
        cleaned_data = super().clean()
        user = cleaned_data.get('user')
        role = cleaned_data.get('role')
        
        if user and role:
            # Check if user already has this role in the organization
            if OrganizationRole.objects.filter(
                user=user,
                organization=self.instance.organization,
                role=role
            ).exists():
                raise ValidationError(_("This user already has this role in the organization."))
        
        return cleaned_data


class CustomSetPasswordForm(SetPasswordForm):
    """
    Enhanced password reset form that includes comprehensive password validation.
    Mirrors Django's SetPasswordForm signature: __init__(self, user, *args, **kwargs)
    so it works seamlessly with PasswordResetConfirmView.
    """
    def __init__(self, user, *args, **kwargs):
        # Let the parent class handle core initialization and validation wiring
        super().__init__(user, *args, **kwargs)

        # Replace the password field with our enhanced version
        self.fields['new_password1'] = EnhancedPasswordField(
            label=_("New password"),
            strip=False,
            help_text=_("Create a strong password that meets security requirements."),
        )

        # Attach user to the enhanced field and the form for policy-based validation
        if user is not None:
            self.fields['new_password1'].set_user(user)
            self.user = user

        self.fields['new_password2'] = forms.CharField(
            label=_("New password confirmation"),
            strip=False,
            widget=forms.PasswordInput(attrs={
                'class': 'form-control',
                'autocomplete': 'new-password'
            }),
        )

        # Add password strength meter + policy hints
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Fieldset(
                _('New Password'),
                'new_password1',
                HTML('<div id="password-strength-meter" class="mt-2"></div>'),
                HTML(render_password_policy_hints(user=user)),
                'new_password2',
            ),
            ButtonHolder(
                Submit('submit', _('Change Password'), css_class='btn-primary'),
                css_class='mt-3'
            )
        )
    
    def clean_new_password1(self):
        password = self.cleaned_data.get('new_password1')
        if password:
            # Validate password strength
            try:
                validate_password_strength(password)
            except ValidationError as e:
                raise ValidationError(e.messages)
            
            # Check password history if user exists
            if hasattr(self, 'user') and self.user:
                from users.models import PasswordHistory
                if PasswordHistory.is_password_reused(self.user, password):
                    raise ValidationError(
                        _("This password has been used recently. Please choose a different password.")
                    )
        
        return password


class PasswordChangeForm(forms.Form):
    """
    Enhanced password change form with comprehensive validation.
    """
    old_password = forms.CharField(
        label=_("Current Password"),
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'autocomplete': 'current-password'
        }),
        strip=False,
    )
    new_password1 = EnhancedPasswordField(
        label=_("New Password"),
        strip=False,
        help_text=_("Create a strong password that meets security requirements."),
    )
    new_password2 = forms.CharField(
        label=_("Confirm New Password"),
        widget=forms.PasswordInput(attrs={
            'class': 'form-control',
            'autocomplete': 'new-password'
        }),
        strip=False,
    )
    password_expiration_period = forms.ChoiceField(
        label=_("Password Expiration Period"),
        choices=CustomUser.PASSWORD_EXPIRATION_CHOICES,
        initial=CustomUser.PASSWORD_EXPIRATION_3_MONTHS,
        help_text=_("Choose how often your password should expire. This setting overrides organization policy."),
        widget=forms.Select(attrs={'class': 'form-control'})
    )

    def __init__(self, user, *args, **kwargs):
        self.user = user
        super().__init__(*args, **kwargs)
        
        # Set the user for password validation
        self.fields['new_password1'].set_user(user)
        
        # Set the current user's password expiration period
        self.fields['password_expiration_period'].initial = user.password_expiration_period
        
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Fieldset(
                _('Current Password'),
                'old_password',
            ),
            Fieldset(
                _('New Password'),
                'new_password1',
                HTML('<div id="password-strength-meter" class="mt-2"></div>'),
                HTML(render_password_policy_hints(user=user)),
                'new_password2',
            ),
            Fieldset(
                _('Password Expiration Settings'),
                'password_expiration_period',
            ),
            ButtonHolder(
                Submit('submit', _('Change Password'), css_class='btn-primary'),
                css_class='mt-3'
            )
        )

    def clean_old_password(self):
        old_password = self.cleaned_data.get('old_password')
        if not self.user.check_password(old_password):
            raise ValidationError(_("Your current password is incorrect."))
        return old_password

    def clean(self):
        cleaned_data = super().clean()
        new_password1 = cleaned_data.get('new_password1')
        new_password2 = cleaned_data.get('new_password2')
        
        if new_password1 and new_password2:
            if new_password1 != new_password2:
                raise ValidationError({
                    'new_password2': _("The two password fields didn't match.")
                })
        
        return cleaned_data
    
    def save(self):
        """Save the password change and update expiration period"""
        user = self.user
        new_password = self.cleaned_data['new_password1']
        expiration_period = self.cleaned_data['password_expiration_period']
        
        # Update the user's password expiration period
        user.password_expiration_period = expiration_period
        user.save(update_fields=['password_expiration_period'])
        
        # Change the password
        user.set_password(new_password)
        user.save()
        
        return user


class PasswordPolicyForm(forms.ModelForm):
    """
    Form for managing password policies.
    """
    class Meta:
        model = PasswordPolicy
        fields = [
            'min_length', 'max_length',
            'require_uppercase', 'require_lowercase', 'require_digits', 'require_special',
            'history_count', 'enable_expiration', 'expiration_days', 'warning_days',
            'enable_lockout', 'max_failed_attempts', 'lockout_duration_minutes',
            'enable_breach_detection'
        ]
        widgets = {
            'min_length': forms.NumberInput(attrs={'class': 'form-control', 'min': 8, 'max': 128}),
            'max_length': forms.NumberInput(attrs={'class': 'form-control', 'min': 12, 'max': 256}),
            'history_count': forms.NumberInput(attrs={'class': 'form-control', 'min': 1, 'max': 20}),
            'expiration_days': forms.NumberInput(attrs={'class': 'form-control', 'min': 30, 'max': 365}),
            'warning_days': forms.NumberInput(attrs={'class': 'form-control', 'min': 1, 'max': 30}),
            'max_failed_attempts': forms.NumberInput(attrs={'class': 'form-control', 'min': 1, 'max': 10}),
            'lockout_duration_minutes': forms.NumberInput(attrs={'class': 'form-control', 'min': 5, 'max': 1440}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Fieldset(
                _('Password Complexity'),
                Row(
                    Column('min_length', css_class='col-md-6'),
                    Column('max_length', css_class='col-md-6'),
                ),
                Row(
                    Column('require_uppercase', css_class='col-md-3'),
                    Column('require_lowercase', css_class='col-md-3'),
                    Column('require_digits', css_class='col-md-3'),
                    Column('require_special', css_class='col-md-3'),
                ),
            ),
            Fieldset(
                _('Password History'),
                'history_count',
            ),
            Fieldset(
                _('Password Expiration'),
                Row(
                    Column('enable_expiration', css_class='col-md-4'),
                    Column('expiration_days', css_class='col-md-4'),
                    Column('warning_days', css_class='col-md-4'),
                ),
            ),
            Fieldset(
                _('Account Lockout'),
                Row(
                    Column('enable_lockout', css_class='col-md-4'),
                    Column('max_failed_attempts', css_class='col-md-4'),
                    Column('lockout_duration_minutes', css_class='col-md-4'),
                ),
            ),
            Fieldset(
                _('Security Features'),
                'enable_breach_detection',
            ),
            ButtonHolder(
                Submit('submit', _('Save Policy'), css_class='btn-primary'),
                css_class='mt-3'
            )
        )

    def clean(self):
        cleaned_data = super().clean()
        min_length = cleaned_data.get('min_length')
        max_length = cleaned_data.get('max_length')
        expiration_days = cleaned_data.get('expiration_days')
        warning_days = cleaned_data.get('warning_days')
        
        if min_length and max_length and min_length > max_length:
            raise ValidationError(_("Minimum length cannot be greater than maximum length."))
        
        if expiration_days and warning_days and warning_days >= expiration_days:
            raise ValidationError(_("Warning days must be less than expiration days."))
        
        return cleaned_data
