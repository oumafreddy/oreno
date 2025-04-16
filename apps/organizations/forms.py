# apps/organizations/forms.py
from django import forms
from .models import Organization

class OrganizationForm(forms.ModelForm):
    class Meta:
        model = Organization
        fields = [
            'customer_code', 
            'customer_name',
            'financial_year_end_date',
            'customer_industry',
            'logo'
        ]
        widgets = {
            'financial_year_end_date': forms.DateInput(attrs={'type': 'date'}),
            'logo': forms.ClearableFileInput(attrs={'class': 'form-control-file'})
        }
        help_texts = {
            'customer_code': 'Unique 8-character organization identifier'
        }

    def clean_customer_code(self):
        code = self.cleaned_data['customer_code']
        if len(code) != 8:
            raise forms.ValidationError("Customer code must be exactly 8 characters")
        return code