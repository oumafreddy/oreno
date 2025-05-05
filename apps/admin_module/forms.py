from django import forms
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Submit, Row, Column, Fieldset, ButtonHolder
from users.models import CustomUser, OrganizationRole
from organizations.models import OrganizationSettings

class UserActivationForm(forms.ModelForm):
    class Meta:
        model = CustomUser
        fields = ['is_active']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_tag = False
        self.helper.layout = Layout(
            Fieldset('Account Status', 'is_active'),
            ButtonHolder(Submit('submit', 'Save', css_class='btn-primary'))
        )

class UserRoleForm(forms.ModelForm):
    class Meta:
        model = OrganizationRole
        fields = ['role']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_tag = False
        self.helper.layout = Layout(
            Fieldset('Role Assignment', 'role'),
            ButtonHolder(Submit('submit', 'Save', css_class='btn-primary'))
        )

class AdminOrganizationSettingsForm(forms.ModelForm):
    class Meta:
        model = OrganizationSettings
        fields = ['organization', 'subscription_plan', 'is_active', 'additional_settings']
        widgets = {'additional_settings': forms.Textarea(attrs={'rows': 4})}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_tag = False
        self.helper.layout = Layout(
            Fieldset('Organization Settings', 'organization', 'subscription_plan', 'is_active', 'additional_settings'),
            ButtonHolder(Submit('submit', 'Save', css_class='btn-primary'))
        ) 