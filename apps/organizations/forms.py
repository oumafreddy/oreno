# apps/organizations/forms.py
from django import forms
from django.utils.translation import gettext_lazy as _
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Submit, Row, Column, Fieldset, ButtonHolder
from crispy_bootstrap5.bootstrap5 import FloatingField
from django_ckeditor_5.fields import CKEditor5Field

from .models import Organization, OrganizationSettings, Subscription

class BaseOrganizationForm(forms.ModelForm):
    """Base form with common functionality for organization-related forms"""
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_tag = False
        self.helper.layout = Layout(
            Fieldset(
                _('Basic Information'),
                Row(
                    Column('name', css_class='col-md-6'),
                    Column('code', css_class='col-md-6'),
                ),
            ),
            Fieldset(
                _('Additional Details'),
                'description',
                'logo',
            ),
            ButtonHolder(
                Submit('submit', _('Save'), css_class='btn-primary'),
                css_class='mt-3'
            )
        )
        for field in self.fields.values():
            field.widget.attrs.update({'class': 'form-control'})

class OrganizationForm(BaseOrganizationForm):
    description = CKEditor5Field(
        config_name='extends',
        blank=True,
        null=True,
        help_text=_("Detailed description of the organization")
    )

    class Meta:
        model = Organization
        fields = [
            'name',
            'code',
            'description',
            'logo',
            'website',
            'is_active'
        ]
        widgets = {
            'logo': forms.ClearableFileInput(attrs={'class': 'form-control-file'})
        }
        help_texts = {
            'name': _('The official name of the organization'),
            'code': _('Unique code to identify this organization'),
            'website': _('Organization website URL'),
            'is_active': _('Uncheck to disable all users under this organization')
        }

    def clean_code(self):
        code = self.cleaned_data['code']
        if not code.isupper():
            raise forms.ValidationError(_('Code must be uppercase'))
        return code

class OrganizationSettingsForm(forms.ModelForm):
    class Meta:
        model = OrganizationSettings
        fields = ['subscription_plan', 'is_active', 'additional_settings']
        widgets = {
            'additional_settings': forms.Textarea(attrs={'rows': 4}),
        }
        help_texts = {
            'subscription_plan': _('Current subscription plan'),
            'is_active': _('Organization subscription status'),
            'additional_settings': _('Additional organization settings in JSON format')
        }

    def clean_additional_settings(self):
        import json
        data = self.cleaned_data['additional_settings']
        try:
            if data:
                json.loads(data)
        except json.JSONDecodeError:
            raise forms.ValidationError(_('Invalid JSON format'))
        return data

class SubscriptionForm(forms.ModelForm):
    class Meta:
        model = Subscription
        fields = ['subscription_plan', 'status', 'start_date', 'end_date', 'auto_renew']
        widgets = {
            'start_date': forms.DateInput(attrs={'type': 'date'}),
            'end_date': forms.DateInput(attrs={'type': 'date'}),
        }
        help_texts = {
            'subscription_plan': _('Subscription plan type'),
            'status': _('Current subscription status'),
            'start_date': _('Subscription start date'),
            'end_date': _('Subscription end date'),
            'auto_renew': _('Automatically renew subscription')
        }

    def clean(self):
        cleaned_data = super().clean()
        start_date = cleaned_data.get('start_date')
        end_date = cleaned_data.get('end_date')
        
        if start_date and end_date and start_date > end_date:
            raise forms.ValidationError(_('End date must be after start date'))
        
        return cleaned_data