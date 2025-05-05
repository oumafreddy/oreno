from django import forms
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit
from .models import (
    ComplianceFramework,
    PolicyDocument,
    DocumentProcessing,
    ComplianceRequirement,
    ComplianceObligation,
    ComplianceEvidence,
)
from django.forms import EmailInput, TextInput
from django.core.validators import RegexValidator

class OrganizationScopedModelForm(forms.ModelForm):
    """Base form to filter organization-owned fields by current organization."""
    def __init__(self, *args, organization=None, request=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.add_input(Submit('submit', 'Save'))
        self.organization = organization or (getattr(request, 'organization', None) if request else None)
        # Filter organization-owned fields if present
        for field_name, field in self.fields.items():
            model_field = self._meta.model._meta.get_field(field_name)
            if hasattr(model_field, 'related_model') and hasattr(model_field.related_model, 'organization'):
                if self.organization:
                    self.fields[field_name].queryset = model_field.related_model.objects.filter(organization=self.organization)

class ComplianceFrameworkForm(OrganizationScopedModelForm):
    class Meta:
        model = ComplianceFramework
        fields = ['name', 'description', 'version', 'regulatory_body']

class PolicyDocumentForm(OrganizationScopedModelForm):
    class Meta:
        model = PolicyDocument
        fields = ['title', 'file', 'version', 'effective_date', 'expiration_date', 'owner', 'owner_email', 'is_anonymized']
        widgets = {
            'effective_date': forms.DateInput(attrs={'type': 'date'}),
            'expiration_date': forms.DateInput(attrs={'type': 'date'}),
            'owner_email': EmailInput(attrs={'type': 'email'}),
        }

class DocumentProcessingForm(OrganizationScopedModelForm):
    class Meta:
        model = DocumentProcessing
        fields = ['document', 'status', 'ai_model_version', 'parsed_text', 'error_message', 'completed_at', 'confidence_score']
        widgets = {
            'completed_at': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        }

class ComplianceRequirementForm(OrganizationScopedModelForm):
    class Meta:
        model = ComplianceRequirement
        fields = ['requirement_id', 'title', 'description', 'regulatory_framework', 'policy_document', 'policy_section', 'jurisdiction', 'mandatory', 'tags']

class ComplianceObligationForm(OrganizationScopedModelForm):
    phone_validator = RegexValidator(r'^[\d\+\-]+$', 'Enter a valid phone number (digits, +, - only).')
    class Meta:
        model = ComplianceObligation
        fields = ['obligation_id', 'requirement', 'description', 'due_period', 'evidence_required', 'owner', 'owner_email', 'priority', 'status', 'due_date', 'completion_date', 'is_active', 'risk']
        widgets = {
            'due_date': forms.DateInput(attrs={'type': 'date'}),
            'completion_date': forms.DateInput(attrs={'type': 'date'}),
            'owner_email': EmailInput(attrs={'type': 'email'}),
        }
    def clean_owner_email(self):
        email = self.cleaned_data.get('owner_email')
        if email and '@' not in email:
            raise forms.ValidationError('Enter a valid email address.')
        return email

class ComplianceEvidenceForm(OrganizationScopedModelForm):
    class Meta:
        model = ComplianceEvidence
        fields = ['obligation', 'document', 'validity_start', 'validity_end', 'notes']
        widgets = {
            'validity_start': forms.DateInput(attrs={'type': 'date'}),
            'validity_end': forms.DateInput(attrs={'type': 'date'}),
        } 