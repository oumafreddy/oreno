# apps/users/forms.py
from django import forms
from django.contrib.auth.forms import UserCreationForm, UserChangeForm
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError
from django.contrib.auth import password_validation
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Submit, Row, Column, Fieldset, ButtonHolder
from crispy_bootstrap5.bootstrap5 import FloatingField

from users.models import CustomUser, Profile, OrganizationRole

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

class CustomUserCreationForm(BaseUserForm, UserCreationForm):
    password1 = forms.CharField(
        label=_("Password"),
        strip=False,
        widget=forms.PasswordInput(attrs={'autocomplete': 'new-password'}),
        help_text=password_validation.password_validators_help_text_html(),
    )
    password2 = forms.CharField(
        label=_("Password confirmation"),
        widget=forms.PasswordInput(attrs={'autocomplete': 'new-password'}),
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

class AdminUserCreationForm(BaseUserForm, UserCreationForm):
    """
    Form for admin users to create users within their organization.
    Organization field is pre-filled and hidden.
    """
    password1 = forms.CharField(
        label=_("Password"),
        strip=False,
        widget=forms.PasswordInput(attrs={'autocomplete': 'new-password'}),
        help_text=password_validation.password_validators_help_text_html(),
    )
    password2 = forms.CharField(
        label=_("Password confirmation"),
        widget=forms.PasswordInput(attrs={'autocomplete': 'new-password'}),
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
        fields = ('email', 'username', 'first_name', 'last_name', 'organization', 'role')
        widgets = {
            'organization': forms.Select(attrs={'class': 'form-select'}),
            'role': forms.Select(attrs={'class': 'form-select'}),
        }

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
