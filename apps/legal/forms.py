from django import forms
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit
from .models import CaseType, LegalParty, LegalCase, CaseParty, LegalTask, LegalDocument, LegalArchive, CustomUser
from django.forms import EmailInput, TextInput
from django.core.validators import RegexValidator

class CaseTypeForm(forms.ModelForm):
    class Meta:
        model = CaseType
        fields = ['name', 'description', 'default_priority']

class LegalPartyForm(forms.ModelForm):
    phone_validator = RegexValidator(r'^[\d\+\-]+$', 'Enter a valid phone number (digits, +, - only).')
    class Meta:
        model = LegalParty
        # organization is now a ForeignKey and should not be exposed in the form
        fields = ['name', 'party_type', 'contact_person', 'contact_email', 'contact_phone', 'address']
        widgets = {
            'contact_email': EmailInput(attrs={'type': 'email'}),
            'contact_phone': TextInput(attrs={'pattern': r'^[\\d\\+\\-]+$', 'title': 'Enter a valid phone number (digits, +, - only).'}),
        }

    def clean_contact_phone(self):
        phone = self.cleaned_data.get('contact_phone')
        if phone:
            self.phone_validator(phone)
        return phone

class LegalCaseForm(forms.ModelForm):
    class Meta:
        model = LegalCase
        fields = [
            'case_type', 'title', 'description', 'opened_date', 'closed_date',
            'estimated_resolution_date', 'parties',
            'risk_description', 'compliance_description',
            'status', 'priority', 'lead_attorney', 'attorneys', 'internal_notes'
        ]
        widgets = {
            'opened_date': forms.DateInput(attrs={'type': 'date'}),
            'closed_date': forms.DateInput(attrs={'type': 'date'}),
            'estimated_resolution_date': forms.DateInput(attrs={'type': 'date'}),
            'attorneys': forms.CheckboxSelectMultiple,
            'parties': forms.CheckboxSelectMultiple,
        }

    def __init__(self, *args, **kwargs):
        organization = kwargs.pop('organization', None)
        super().__init__(*args, **kwargs)
        if organization:
            self.fields['case_type'].queryset = CaseType.objects.filter(organization=organization)
            self.fields['lead_attorney'].queryset = CustomUser.objects.filter(organization=organization)
            self.fields['attorneys'].queryset = CustomUser.objects.filter(organization=organization)

class CasePartyForm(forms.ModelForm):
    class Meta:
        model = CaseParty
        fields = ['case', 'party', 'role_in_case']

class LegalTaskForm(forms.ModelForm):
    class Meta:
        model = LegalTask
        fields = ['case', 'title', 'description', 'due_date', 'completion_date', 'status', 'assigned_to']
        widgets = {
            'due_date': forms.DateInput(attrs={'type': 'date'}),
            'completion_date': forms.DateInput(attrs={'type': 'date'}),
        }

    def __init__(self, *args, **kwargs):
        organization = kwargs.pop('organization', None)
        super().__init__(*args, **kwargs)
        if organization:
            self.fields['assigned_to'].queryset = CustomUser.objects.filter(organization=organization)

class LegalDocumentForm(forms.ModelForm):
    class Meta:
        model = LegalDocument
        fields = ['case', 'title', 'description', 'file', 'version', 'is_confidential']

class LegalArchiveForm(forms.ModelForm):
    class Meta:
        model = LegalArchive
        fields = ['case', 'archive_date', 'retention_period_years', 'archive_reason', 'destruction_date']
        widgets = {
            'archive_date': forms.DateInput(attrs={'type': 'date'}),
            'destruction_date': forms.DateInput(attrs={'type': 'date'}),
        } 