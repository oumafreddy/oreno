from django import forms
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit
from .models import ContractType, Party, Contract, ContractParty, ContractMilestone
from django.forms import DateInput, EmailInput, TextInput
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

class ContractTypeForm(OrganizationScopedModelForm):
    class Meta:
        model = ContractType
        exclude = ('organization',)

class PartyForm(OrganizationScopedModelForm):
    phone_validator = RegexValidator(r'^[\d\+\-]+$', 'Enter a valid phone number (digits, +, - only).')
    class Meta:
        model = Party
        fields = '__all__'
        widgets = {
            'contact_email': EmailInput(attrs={'type': 'email'}),
            'contact_phone': TextInput(attrs={'pattern': r'^[\\d\\+\\-]+$', 'title': 'Enter a valid phone number (digits, +, - only).'}),
        }
    def clean_contact_phone(self):
        phone = self.cleaned_data.get('contact_phone')
        if phone:
            self.phone_validator(phone)
        return phone

class ContractForm(OrganizationScopedModelForm):
    class Meta:
        model = Contract
        exclude = ('organization',)
        widgets = {
            'start_date': DateInput(attrs={'type': 'date'}),
            'end_date': DateInput(attrs={'type': 'date'}),
            'termination_date': DateInput(attrs={'type': 'date'}),
        }

class ContractPartyForm(forms.ModelForm):
    class Meta:
        model = ContractParty
        fields = '__all__'

class ContractMilestoneForm(OrganizationScopedModelForm):
    class Meta:
        model = ContractMilestone
        exclude = ('organization',)
        widgets = {
            'due_date': DateInput(attrs={'type': 'date'}),
            'completion_date': DateInput(attrs={'type': 'date'}),
        } 