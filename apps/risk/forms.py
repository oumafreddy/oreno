from django import forms
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit
from .models import RiskRegister, RiskMatrixConfig, Risk, Control, KRI, RiskAssessment
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

class RiskRegisterForm(OrganizationScopedModelForm):
    class Meta:
        model = RiskRegister
        fields = '__all__'

class RiskMatrixConfigForm(OrganizationScopedModelForm):
    class Meta:
        model = RiskMatrixConfig
        exclude = ('organization',)

class RiskForm(OrganizationScopedModelForm):
    class Meta:
        model = Risk
        exclude = ('organization',)

class ControlForm(OrganizationScopedModelForm):
    class Meta:
        model = Control
        exclude = ('organization',)

class KRIForm(OrganizationScopedModelForm):
    class Meta:
        model = KRI
        exclude = ('organization',)

class RiskAssessmentForm(OrganizationScopedModelForm):
    class Meta:
        model = RiskAssessment
        exclude = ('organization',)

# If any risk forms add direct email/phone fields in the future, use the following pattern:
# widgets = {'contact_email': EmailInput(attrs={'type': 'email'}), 'contact_phone': TextInput(attrs={'pattern': r'^[\\d\\+\\-]+$', 'title': 'Enter a valid phone number (digits, +, - only).'})} 