from django import forms
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit, Layout, Row, Column
from .models import RiskRegister, RiskMatrixConfig, Risk, Control, KRI, RiskAssessment
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