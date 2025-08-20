from django import forms
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit, Layout, Row, Column
from django_ckeditor_5.widgets import CKEditor5Widget
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
        
        # Filter user fields by organization
        if self.organization:
            from users.models import CustomUser
            for field_name, field in self.fields.items():
                if hasattr(field, 'queryset') and field.queryset is not None:
                    model = field.queryset.model
                    if model.__name__ in ['CustomUser', 'User']:
                        field.queryset = field.queryset.filter(organization=self.organization)

class ComplianceFrameworkForm(OrganizationScopedModelForm):
    class Meta:
        model = ComplianceFramework
        fields = ['name', 'description', 'version', 'regulatory_body']
        widgets = {
            'description': CKEditor5Widget(
                config_name='extends', 
                attrs={
                    'class': 'django_ckeditor_5',
                }
            ),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Ensure the description field is properly configured
        if 'description' in self.fields:
            self.fields['description'].widget.config_name = 'extends'
            self.fields['description'].required = False
    
    def clean_description(self):
        """Ensure description field is properly handled"""
        description = self.cleaned_data.get('description')
        # If description is empty string, convert to None to match model field
        if description == '' or description is None:
            return None
        return description

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
        widgets = {
            'description': CKEditor5Widget(config_name='extends', attrs={'class': 'django_ckeditor_5'}),
        }

class ComplianceObligationForm(OrganizationScopedModelForm):
    phone_validator = RegexValidator(r'^[\d\+\-]+$', 'Enter a valid phone number (digits, +, - only).')
    class Meta:
        model = ComplianceObligation
        fields = ['obligation_id', 'requirement', 'description', 'due_period', 'evidence_required', 'owner', 'owner_email', 'priority', 'status', 'due_date', 'completion_date', 'is_active', 'risk']
        widgets = {
            'description': CKEditor5Widget(config_name='extends', attrs={'class': 'django_ckeditor_5'}),
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
            'notes': CKEditor5Widget(config_name='extends', attrs={'class': 'django_ckeditor_5'}),
            'validity_start': forms.DateInput(attrs={'type': 'date'}),
            'validity_end': forms.DateInput(attrs={'type': 'date'}),
        }

class PolicyDocumentFilterForm(forms.Form):
    q = forms.CharField(label='Search', required=False, widget=forms.TextInput(attrs={'placeholder': 'Title or Code', 'class': 'form-control'}))
    status = forms.ChoiceField(label='Status', required=False, choices=[('', 'All'), ('active', 'Active'), ('archived', 'Archived')], widget=forms.Select(attrs={'class': 'form-select'}))
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'get'
        self.helper.form_show_labels = False
        self.helper.layout = Layout(
            Row(
                Column('q', css_class='col-md-8'),
                Column('status', css_class='col-md-2'),
                Column(Submit('filter', 'Filter', css_class='btn-primary mt-0'), css_class='col-md-2 align-self-end'),
            )
        ) 