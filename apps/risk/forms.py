from django import forms
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit, Layout, Row, Column
from .models import (
    RiskRegister, RiskMatrixConfig, Risk, Control, KRI, RiskAssessment,
    # COBIT models
    COBITDomain, COBITProcess, COBITCapability, COBITControl, COBITGovernance,
    # NIST models
    NISTFunction, NISTCategory, NISTSubcategory, NISTImplementation, NISTThreat, NISTIncident,
    Objective
)
from django.forms import EmailInput, TextInput
from django.core.validators import RegexValidator
from django_ckeditor_5.widgets import CKEditor5Widget

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
            # ManyToMany fields
            if hasattr(model_field, 'many_to_many') and getattr(model_field, 'many_to_many'):
                if self.organization and hasattr(field, 'queryset') and field.queryset is not None and hasattr(field.queryset.model, 'organization'):
                    field.queryset = field.queryset.filter(organization=self.organization)
        
        # Filter user fields by organization
        if self.organization:
            from users.models import CustomUser
            for field_name, field in self.fields.items():
                if hasattr(field, 'queryset') and field.queryset is not None:
                    model = field.queryset.model
                    if model.__name__ in ['CustomUser', 'User']:
                        field.queryset = field.queryset.filter(organization=self.organization)

class RiskRegisterForm(OrganizationScopedModelForm):
    class Meta:
        model = RiskRegister
        exclude = ('organization', 'created_by', 'updated_by')
        widgets = {
            'register_description': CKEditor5Widget(config_name='extends', attrs={'class': 'django_ckeditor_5'}),
            'register_creation_date': forms.DateInput(attrs={'type': 'date'}),
        }

class RiskMatrixConfigForm(OrganizationScopedModelForm):
    class Meta:
        model = RiskMatrixConfig
        exclude = ('organization', 'created_by', 'updated_by')

class RiskForm(OrganizationScopedModelForm):
    class Meta:
        model = Risk
        exclude = ('organization', 'created_by', 'updated_by')
        widgets = {
            'external_context': CKEditor5Widget(config_name='extends', attrs={'class': 'django_ckeditor_5'}),
            'internal_context': CKEditor5Widget(config_name='extends', attrs={'class': 'django_ckeditor_5'}),
            'risk_description': CKEditor5Widget(config_name='extends', attrs={'class': 'django_ckeditor_5'}),
            'controls_description': CKEditor5Widget(config_name='extends', attrs={'class': 'django_ckeditor_5'}),
            'action_plan': CKEditor5Widget(config_name='extends', attrs={'class': 'django_ckeditor_5'}),
            'kri_description': CKEditor5Widget(config_name='extends', attrs={'class': 'django_ckeditor_5'}),
            'closure_justification': CKEditor5Widget(config_name='extends', attrs={'class': 'django_ckeditor_5'}),
            'additional_notes': CKEditor5Widget(config_name='extends', attrs={'class': 'django_ckeditor_5'}),
            'date_identified': forms.DateInput(attrs={'type': 'date'}),
            'control_last_review_date': forms.DateInput(attrs={'type': 'date'}),
            'control_next_review_date': forms.DateInput(attrs={'type': 'date'}),
            'action_due_date': forms.DateInput(attrs={'type': 'date'}),
            'next_review_date': forms.DateInput(attrs={'type': 'date'}),
            'last_reviewed_date': forms.DateInput(attrs={'type': 'date'}),
            'closure_date': forms.DateInput(attrs={'type': 'date'}),
        }

    def __init__(self, *args, organization=None, request=None, **kwargs):
        super().__init__(*args, organization=organization, request=request, **kwargs)
        # Dynamically limit score choices based on active matrix
        try:
            from .models import RiskMatrixConfig
            matrix = None
            org = organization or (getattr(request, 'organization', None) if request else None)
            if org:
                matrix = RiskMatrixConfig.objects.filter(organization=org, is_active=True).first()
            if matrix:
                impact_range = [(i, str(i)) for i in range(1, min(matrix.impact_levels, 5) + 1)]
                likelihood_range = [(i, str(i)) for i in range(1, min(matrix.likelihood_levels, 5) + 1)]
                # Inherent
                if 'inherent_impact_score' in self.fields:
                    self.fields['inherent_impact_score'].widget = forms.Select(choices=impact_range)
                if 'inherent_likelihood_score' in self.fields:
                    self.fields['inherent_likelihood_score'].widget = forms.Select(choices=likelihood_range)
                # Residual
                if 'residual_impact_score' in self.fields:
                    self.fields['residual_impact_score'].widget = forms.Select(choices=impact_range)
                if 'residual_likelihood_score' in self.fields:
                    self.fields['residual_likelihood_score'].widget = forms.Select(choices=likelihood_range)
                # Optional: guide risk appetite entry by setting HTML attrs (non-enforcing)
                if 'risk_appetite' in self.fields:
                    self.fields['risk_appetite'].widget.attrs.update({
                        'min': 1,
                        'max': str(matrix.very_high_threshold),
                    })
        except Exception:
            # Fail open: keep default widgets if anything goes wrong
            from django.contrib import messages
            req = request or getattr(self, 'request', None)
            if req and hasattr(req, 'META'):
                try:
                    messages.warning(req, 'Active risk matrix not found; using default score ranges (1-5).')
                except Exception:
                    # messages framework may not be available in this context
                    pass
        # Limit objectives to active ones in current organization
        if 'objectives' in self.fields:
            qs = Objective.objects.all()
            if organization is not None:
                qs = qs.filter(organization=organization)
            self.fields['objectives'].queryset = qs.filter(status='active')

    def clean(self):
        # Ensure organization is set on instance before model.clean() runs
        if not getattr(self.instance, 'organization', None) and getattr(self, 'organization', None):
            self.instance.organization = self.organization
        return super().clean()

class ControlForm(OrganizationScopedModelForm):
    class Meta:
        model = Control
        exclude = ('organization', 'created_by', 'updated_by')
        widgets = {
            'description': CKEditor5Widget(config_name='extends', attrs={'class': 'django_ckeditor_5'}),
            'last_review_date': forms.DateInput(attrs={'type': 'date'}),
            'next_review_date': forms.DateInput(attrs={'type': 'date'}),
        }

class KRIForm(OrganizationScopedModelForm):
    class Meta:
        model = KRI
        exclude = ('organization',)
        widgets = {
            'description': CKEditor5Widget(config_name='extends', attrs={'class': 'django_ckeditor_5'}),
        }

class RiskAssessmentForm(OrganizationScopedModelForm):
    class Meta:
        model = RiskAssessment
        exclude = ('organization', 'created_by', 'updated_by')
        widgets = {
            'notes': CKEditor5Widget(config_name='extends', attrs={'class': 'django_ckeditor_5'}),
            'assessment_date': forms.DateInput(attrs={'type': 'date'}),
        }

class ObjectiveForm(OrganizationScopedModelForm):
    class Meta:
        model = Objective
        exclude = ('organization', 'created_by', 'updated_by')
        widgets = {
            'description': CKEditor5Widget(config_name='extends', attrs={'class': 'django_ckeditor_5'}),
            'start_date': forms.DateInput(attrs={'type': 'date'}),
            'end_date': forms.DateInput(attrs={'type': 'date'}),
        }

# COBIT Forms
class COBITDomainForm(OrganizationScopedModelForm):
    class Meta:
        model = COBITDomain
        exclude = ('organization', 'created_by', 'updated_by')
        widgets = {
            'description': CKEditor5Widget(config_name='extends', attrs={'class': 'django_ckeditor_5'}),
            'objectives': CKEditor5Widget(config_name='extends', attrs={'class': 'django_ckeditor_5'}),
        }

class COBITProcessForm(OrganizationScopedModelForm):
    class Meta:
        model = COBITProcess
        exclude = ('organization', 'created_by', 'updated_by')
        widgets = {
            'description': CKEditor5Widget(config_name='extends', attrs={'class': 'django_ckeditor_5'}),
            'purpose': CKEditor5Widget(config_name='extends', attrs={'class': 'django_ckeditor_5'}),
            'goals': CKEditor5Widget(config_name='extends', attrs={'class': 'django_ckeditor_5'}),
            'practices': CKEditor5Widget(config_name='extends', attrs={'class': 'django_ckeditor_5'}),
            'inputs': CKEditor5Widget(config_name='extends', attrs={'class': 'django_ckeditor_5'}),
            'outputs': CKEditor5Widget(config_name='extends', attrs={'class': 'django_ckeditor_5'}),
        }

class COBITCapabilityForm(OrganizationScopedModelForm):
    class Meta:
        model = COBITCapability
        exclude = ('organization', 'created_by', 'updated_by')
        widgets = {
            'assessment_notes': CKEditor5Widget(config_name='extends', attrs={'class': 'django_ckeditor_5'}),
            'improvement_plan': CKEditor5Widget(config_name='extends', attrs={'class': 'django_ckeditor_5'}),
            'assessment_date': forms.DateInput(attrs={'type': 'date'}),
            'next_assessment_date': forms.DateInput(attrs={'type': 'date'}),
        }

class COBITControlForm(OrganizationScopedModelForm):
    class Meta:
        model = COBITControl
        exclude = ('organization', 'created_by', 'updated_by')
        widgets = {
            'description': CKEditor5Widget(config_name='extends', attrs={'class': 'django_ckeditor_5'}),
            'last_assessment_date': forms.DateInput(attrs={'type': 'date'}),
            'next_assessment_date': forms.DateInput(attrs={'type': 'date'}),
        }

class COBITGovernanceForm(OrganizationScopedModelForm):
    class Meta:
        model = COBITGovernance
        exclude = ('organization', 'created_by', 'updated_by')
        widgets = {
            'description': CKEditor5Widget(config_name='extends', attrs={'class': 'django_ckeditor_5'}),
            'outcome_statements': CKEditor5Widget(config_name='extends', attrs={'class': 'django_ckeditor_5'}),
            'stakeholder_responsibilities': CKEditor5Widget(config_name='extends', attrs={'class': 'django_ckeditor_5'}),
        }

# NIST Forms
class NISTFunctionForm(OrganizationScopedModelForm):
    class Meta:
        model = NISTFunction
        exclude = ('organization', 'created_by', 'updated_by')
        widgets = {
            'description': CKEditor5Widget(config_name='extends', attrs={'class': 'django_ckeditor_5'}),
            'objectives': CKEditor5Widget(config_name='extends', attrs={'class': 'django_ckeditor_5'}),
        }

class NISTCategoryForm(OrganizationScopedModelForm):
    class Meta:
        model = NISTCategory
        exclude = ('organization', 'created_by', 'updated_by')
        widgets = {
            'description': CKEditor5Widget(config_name='extends', attrs={'class': 'django_ckeditor_5'}),
            'outcomes': CKEditor5Widget(config_name='extends', attrs={'class': 'django_ckeditor_5'}),
        }

class NISTSubcategoryForm(OrganizationScopedModelForm):
    class Meta:
        model = NISTSubcategory
        exclude = ('organization', 'created_by', 'updated_by')
        widgets = {
            'description': CKEditor5Widget(config_name='extends', attrs={'class': 'django_ckeditor_5'}),
            'outcomes': CKEditor5Widget(config_name='extends', attrs={'class': 'django_ckeditor_5'}),
            'informative_references': CKEditor5Widget(config_name='extends', attrs={'class': 'django_ckeditor_5'}),
        }

class NISTImplementationForm(OrganizationScopedModelForm):
    class Meta:
        model = NISTImplementation
        exclude = ('organization', 'created_by', 'updated_by')
        widgets = {
            'assessment_notes': CKEditor5Widget(config_name='extends', attrs={'class': 'django_ckeditor_5'}),
            'implementation_plan': CKEditor5Widget(config_name='extends', attrs={'class': 'django_ckeditor_5'}),
            'assessment_date': forms.DateInput(attrs={'type': 'date'}),
            'next_assessment_date': forms.DateInput(attrs={'type': 'date'}),
        }

class NISTThreatForm(OrganizationScopedModelForm):
    class Meta:
        model = NISTThreat
        exclude = ('organization', 'created_by', 'updated_by')
        widgets = {
            'description': CKEditor5Widget(config_name='extends', attrs={'class': 'django_ckeditor_5'}),
            'impact_analysis': CKEditor5Widget(config_name='extends', attrs={'class': 'django_ckeditor_5'}),
            'affected_assets': CKEditor5Widget(config_name='extends', attrs={'class': 'django_ckeditor_5'}),
            'mitigation_strategies': CKEditor5Widget(config_name='extends', attrs={'class': 'django_ckeditor_5'}),
        }

class NISTIncidentForm(OrganizationScopedModelForm):
    class Meta:
        model = NISTIncident
        exclude = ('organization', 'created_by', 'updated_by')
        widgets = {
            'description': CKEditor5Widget(config_name='extends', attrs={'class': 'django_ckeditor_5'}),
            'affected_systems': CKEditor5Widget(config_name='extends', attrs={'class': 'django_ckeditor_5'}),
            'containment_actions': CKEditor5Widget(config_name='extends', attrs={'class': 'django_ckeditor_5'}),
            'eradication_actions': CKEditor5Widget(config_name='extends', attrs={'class': 'django_ckeditor_5'}),
            'recovery_actions': CKEditor5Widget(config_name='extends', attrs={'class': 'django_ckeditor_5'}),
            'lessons_learned': CKEditor5Widget(config_name='extends', attrs={'class': 'django_ckeditor_5'}),
            'detected_date': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
            'resolved_date': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        }

# If any risk forms add direct email/phone fields in the future, use the following pattern:
# widgets = {'contact_email': EmailInput(attrs={'type': 'email'}), 'contact_phone': TextInput(attrs={'pattern': r'^[\\d\\+\\-]+$', 'title': 'Enter a valid phone number (digits, +, - only).'})} 

class RiskRegisterFilterForm(forms.Form):
    q = forms.CharField(label='Search', required=False, widget=forms.TextInput(attrs={'placeholder': 'Name or Code', 'class': 'form-control'}))
    period = forms.CharField(label='Period', required=False, widget=forms.TextInput(attrs={'placeholder': 'Period', 'class': 'form-control'}))
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'get'
        self.helper.form_show_labels = False
        self.helper.layout = Layout(
            Row(
                Column('q', css_class='col-md-6'),
                Column('period', css_class='col-md-4'),
                Column(Submit('filter', 'Filter', css_class='btn-primary mt-0'), css_class='col-md-2 align-self-end'),
            )
        )

class RiskMatrixConfigFilterForm(forms.Form):
    name = forms.CharField(label='Name', required=False, widget=forms.TextInput(attrs={'placeholder': 'Matrix Name', 'class': 'form-control'}))
    is_active = forms.ChoiceField(label='Active', required=False, choices=[('', 'All'), ('1', 'Active'), ('0', 'Inactive')], widget=forms.Select(attrs={'class': 'form-select'}))
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'get'
        self.helper.form_show_labels = False
        self.helper.layout = Layout(
            Row(
                Column('name', css_class='col-md-8'),
                Column('is_active', css_class='col-md-2'),
                Column(Submit('filter', 'Filter', css_class='btn-primary mt-0'), css_class='col-md-2 align-self-end'),
            )
        ) 

# Friendly message when active matrix is missing (form-only utility)
def get_active_matrix_or_message(request, organization):
    try:
        from .models import RiskMatrixConfig
        matrix = RiskMatrixConfig.objects.filter(organization=organization, is_active=True).first()
        if not matrix and request is not None:
            from django.contrib import messages
            messages.warning(request, 'No active risk matrix found. Please configure one to enable matrix-driven scoring.')
        return matrix
    except Exception:
        return None