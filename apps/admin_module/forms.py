from django import forms
from django.utils.translation import gettext_lazy as _
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Fieldset, Row, Column, Submit, ButtonHolder, HTML
from crispy_forms.bootstrap import PrependedText

from .models import DataExportLog

User = get_user_model()

class DataExportForm(forms.ModelForm):
    """
    Form for requesting data exports with comprehensive validation.
    """
    
    # Additional fields for export configuration
    include_attachments = forms.BooleanField(
        required=False,
        initial=True,
        label=_("Include Attachments"),
        help_text=_("Include file attachments in the export (may significantly increase file size)")
    )
    
    include_metadata = forms.BooleanField(
        required=False,
        initial=True,
        label=_("Include Metadata"),
        help_text=_("Include metadata and relationship information in the export")
    )
    
    include_audit_trail = forms.BooleanField(
        required=False,
        initial=True,
        label=_("Include Audit Trail"),
        help_text=_("Include audit trail and change history in the export")
    )
    
    date_from = forms.DateField(
        required=False,
        label=_("Date From"),
        help_text=_("Export data from this date onwards (leave blank for all data)"),
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'})
    )
    
    date_to = forms.DateField(
        required=False,
        label=_("Date To"),
        help_text=_("Export data up to this date (leave blank for all data)"),
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'})
    )
    
    # Custom selection fields
    custom_models = forms.MultipleChoiceField(
        required=False,
        label=_("Select Specific Data Types"),
        help_text=_("Choose specific data types to export (only for custom selection)"),
        choices=[
            ('audit_workplans', _('Audit Workplans')),
            ('audit_engagements', _('Audit Engagements')),
            ('audit_issues', _('Audit Issues')),
            ('risk_assessments', _('Risk Assessments')),
            ('risk_controls', _('Risk Controls')),
            ('compliance_requirements', _('Compliance Requirements')),
            ('compliance_obligations', _('Compliance Obligations')),
            ('contracts', _('Contracts')),
            ('contract_milestones', _('Contract Milestones')),
            ('legal_cases', _('Legal Cases')),
            ('legal_tasks', _('Legal Tasks')),
            ('documents', _('Documents')),
            ('users', _('Users')),
            ('organizations', _('Organization Data')),
        ],
        widget=forms.CheckboxSelectMultiple(attrs={'class': 'form-check-input'})
    )
    
    class Meta:
        model = DataExportLog
        fields = ['export_type', 'export_format', 'notes']
        widgets = {
            'export_type': forms.Select(attrs={'class': 'form-select'}),
            'export_format': forms.Select(attrs={'class': 'form-select'}),
            'notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        self.organization = kwargs.pop('organization', None)
        super().__init__(*args, **kwargs)
        
        # Set up form helper
        self.helper = FormHelper()
        self.helper.form_tag = True
        self.helper.form_class = 'form-horizontal'
        self.helper.label_class = 'col-lg-3'
        self.helper.field_class = 'col-lg-9'
        
        # Customize layout based on export type
        self.helper.layout = Layout(
            Fieldset(
                _('Export Configuration'),
                Row(
                    Column('export_type', css_class='col-md-6'),
                    Column('export_format', css_class='col-md-6'),
                ),
                Row(
                    Column('date_from', css_class='col-md-6'),
                    Column('date_to', css_class='col-md-6'),
                ),
                Row(
                    Column('include_attachments', css_class='col-md-4'),
                    Column('include_metadata', css_class='col-md-4'),
                    Column('include_audit_trail', css_class='col-md-4'),
                ),
            ),
            Fieldset(
                _('Custom Selection'),
                HTML('<div id="custom-selection-fields" style="display: none;">'),
                'custom_models',
                HTML('</div>'),
            ),
            Fieldset(
                _('Additional Information'),
                'notes',
            ),
            ButtonHolder(
                Submit('submit', _('Request Export'), css_class='btn-primary'),
                HTML('<a href="{% url "admin_module:export-list" %}" class="btn btn-secondary">Cancel</a>'),
                css_class='mt-3'
            )
        )
        
        # Add JavaScript to show/hide custom selection fields
        self.helper.layout.append(
            HTML("""
            <script>
            document.addEventListener('DOMContentLoaded', function() {
                const exportTypeField = document.getElementById('id_export_type');
                const customFields = document.getElementById('custom-selection-fields');
                
                function toggleCustomFields() {
                    if (exportTypeField.value === 'custom') {
                        customFields.style.display = 'block';
                    } else {
                        customFields.style.display = 'none';
                    }
                }
                
                exportTypeField.addEventListener('change', toggleCustomFields);
                toggleCustomFields(); // Initial state
            });
            </script>
            """)
        )
    
    def clean(self):
        cleaned_data = super().clean()
        export_type = cleaned_data.get('export_type')
        date_from = cleaned_data.get('date_from')
        date_to = cleaned_data.get('date_to')
        custom_models = cleaned_data.get('custom_models')
        
        # Validate date range
        if date_from and date_to and date_from > date_to:
            raise ValidationError(_("Start date cannot be after end date."))
        
        # Validate custom selection
        if export_type == 'custom' and not custom_models:
            raise ValidationError(_("Please select at least one data type for custom export."))
        
        # Validate user permissions
        if self.user and not self.user.role == 'admin':
            raise ValidationError(_("Only administrators can request data exports."))
        
        return cleaned_data
    
    def save(self, commit=True):
        instance = super().save(commit=False)
        
        # Set user and organization
        if self.user:
            instance.requested_by = self.user
        if self.organization:
            instance.organization = self.organization
        
        # Store custom selection details
        if instance.export_type == 'custom':
            instance.custom_selection = {
                'models': self.cleaned_data.get('custom_models', []),
                'include_attachments': self.cleaned_data.get('include_attachments', True),
                'date_from': self.cleaned_data.get('date_from'),
                'date_to': self.cleaned_data.get('date_to'),
            }
        
        if commit:
            instance.save()
        return instance


class DataExportFilterForm(forms.Form):
    """
    Form for filtering data export logs.
    """
    STATUS_CHOICES = [('', _('All Statuses'))] + DataExportLog.STATUS_CHOICES
    EXPORT_TYPE_CHOICES = [('', _('All Types'))] + DataExportLog.EXPORT_TYPE_CHOICES
    
    status = forms.ChoiceField(
        choices=STATUS_CHOICES,
        required=False,
        label=_("Status"),
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    export_type = forms.ChoiceField(
        choices=EXPORT_TYPE_CHOICES,
        required=False,
        label=_("Export Type"),
        widget=forms.Select(attrs={'class': 'form-select'})
    )
    
    date_from = forms.DateField(
        required=False,
        label=_("Date From"),
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'})
    )
    
    date_to = forms.DateField(
        required=False,
        label=_("Date To"),
        widget=forms.DateInput(attrs={'type': 'date', 'class': 'form-control'})
    )
    
    requested_by = forms.ModelChoiceField(
        queryset=User.objects.filter(role='admin'),
        required=False,
        label=_("Requested By"),
        widget=forms.Select(attrs={'class': 'form-select'})
    )

    def __init__(self, *args, **kwargs):
        self.organization = kwargs.pop('organization', None)
        super().__init__(*args, **kwargs)
        
        # Filter users by organization
        if self.organization:
            self.fields['requested_by'].queryset = User.objects.filter(
                organization=self.organization,
                role='admin'
            )
        
        # Set up form helper
        self.helper = FormHelper()
        self.helper.form_tag = False
        self.helper.layout = Layout(
            Row(
                Column('status', css_class='col-md-3'),
                Column('export_type', css_class='col-md-3'),
                Column('date_from', css_class='col-md-2'),
                Column('date_to', css_class='col-md-2'),
                Column('requested_by', css_class='col-md-2'),
            ),
        )
    
    def clean(self):
        cleaned_data = super().clean()
        date_from = cleaned_data.get('date_from')
        date_to = cleaned_data.get('date_to')
        
        if date_from and date_to and date_from > date_to:
            raise ValidationError(_("Start date cannot be after end date."))
        
        return cleaned_data 