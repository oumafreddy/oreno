from django import forms
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Submit, Layout, Row, Column
from .models import DocumentRequest, Document
from users.models import CustomUser
from django.forms import EmailInput, DateInput

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

class DocumentRequestForm(OrganizationScopedModelForm):
    class Meta:
        model = DocumentRequest
        exclude = ('organization', 'created_by', 'updated_by')
        widgets = {
            'due_date': DateInput(attrs={'type': 'date'}),
            'date_of_request': DateInput(attrs={'type': 'date'}),
            'requestee_email': EmailInput(attrs={'type': 'email'}),
        }

    def __init__(self, *args, organization=None, request=None, **kwargs):
        super().__init__(*args, organization=organization, request=request, **kwargs)

    def clean_requestee_email(self):
        email = self.cleaned_data.get('requestee_email')
        if email and '@' not in email:
            raise forms.ValidationError('Enter a valid email address.')
        return email

class DocumentForm(OrganizationScopedModelForm):
    class Meta:
        model = Document
        exclude = ('organization', 'created_by', 'updated_by')
        widgets = {
            'uploaded_at': DateInput(attrs={'type': 'datetime-local'}),
        }

    def __init__(self, *args, organization=None, request=None, **kwargs):
        super().__init__(*args, organization=organization, request=request, **kwargs)

class DocumentRequestFilterForm(forms.Form):
    q = forms.CharField(label='Search', required=False, widget=forms.TextInput(attrs={'placeholder': 'Request Name or Requestee', 'class': 'form-control'}))
    status = forms.ChoiceField(label='Status', required=False, choices=[('', 'All'), ('pending', 'Pending'), ('submitted', 'Submitted'), ('accepted', 'Accepted'), ('rejected', 'Rejected')], widget=forms.Select(attrs={'class': 'form-select'}))
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
