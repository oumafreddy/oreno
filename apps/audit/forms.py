from django import forms
from django.utils.translation import gettext_lazy as _
from django.contrib.contenttypes.models import ContentType
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Submit, Row, Column, Fieldset, ButtonHolder
from crispy_bootstrap5.bootstrap5 import FloatingField
from django.forms import EmailInput, TextInput
from django.core.validators import RegexValidator

from organizations.models import Organization
from users.models import CustomUser

from .models import AuditWorkplan, Engagement, Issue, Approval

# ─── BASE FORM CLASS ──────────────────────────────────────────────────────────
class BaseAuditForm(forms.ModelForm):
    """Base form class with common functionality for all audit forms"""
    
    def __init__(self, *args, **kwargs):
        self.organization = kwargs.pop('organization', None)
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_tag = False
        self.helper.disable_csrf = True

# ─── WORKPLAN FORMS ──────────────────────────────────────────────────────────
class AuditWorkplanForm(BaseAuditForm):
    class Meta:
        model = AuditWorkplan
        fields = ['code', 'name', 'fiscal_year', 'objectives', 'description']
        widgets = {
            'fiscal_year': forms.NumberInput(attrs={'min': 2000, 'max': 2100}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper.layout = Layout(
            Fieldset(
                _('Basic Information'),
                Row(
                    Column(FloatingField('code'), css_class='col-md-6'),
                    Column(FloatingField('name'), css_class='col-md-6'),
                ),
                Row(
                    Column(FloatingField('fiscal_year'), css_class='col-md-6'),
                ),
            ),
            Fieldset(
                _('Details'),
                'objectives',
                'description',
            ),
            ButtonHolder(
                Submit('submit', _('Save'), css_class='btn-primary'),
                css_class='mt-3'
            )
        )

# ─── ENGAGEMENT FORMS ────────────────────────────────────────────────────────
class EngagementForm(BaseAuditForm):
    class Meta:
        model = Engagement
        fields = [
            'code', 'title', 'audit_workplan', 'engagement_type',
            'project_start_date', 'target_end_date', 'assigned_to',
            'executive_summary', 'purpose', 'background', 'scope',
            'project_objectives', 'conclusion_description', 'conclusion',
            'project_status'
        ]
        widgets = {
            'project_start_date': forms.DateInput(attrs={'type': 'date'}),
            'target_end_date': forms.DateInput(attrs={'type': 'date'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.organization:
            self.fields['audit_workplan'].queryset = AuditWorkplan.objects.filter(
                organization=self.organization
            )
            self.fields['assigned_to'].queryset = CustomUser.objects.filter(
                organization=self.organization
            )
        
        self.helper.layout = Layout(
            Fieldset(
                _('Basic Information'),
                Row(
                    Column(FloatingField('code'), css_class='col-md-6'),
                    Column(FloatingField('title'), css_class='col-md-6'),
                ),
                Row(
                    Column('audit_workplan', css_class='col-md-6'),
                    Column('engagement_type', css_class='col-md-6'),
                ),
                Row(
                    Column('project_start_date', css_class='col-md-6'),
                    Column('target_end_date', css_class='col-md-6'),
                ),
                Row(
                    Column('assigned_to', css_class='col-md-6'),
                    Column('project_status', css_class='col-md-6'),
                ),
            ),
            Fieldset(
                _('Engagement Details'),
                'executive_summary',
                'purpose',
                'background',
                'scope',
                'project_objectives',
                'conclusion_description',
                'conclusion',
            ),
            ButtonHolder(
                Submit('submit', _('Save'), css_class='btn-primary'),
                css_class='mt-3'
            )
        )

# ─── ISSUE FORMS ─────────────────────────────────────────────────────────────
class IssueForm(BaseAuditForm):
    class Meta:
        model = Issue
        fields = [
            'code', 'issue_title', 'issue_description', 'root_cause',
            'risks', 'date_identified', 'issue_owner', 'issue_owner_title',
            'audit_procedures', 'recommendation', 'engagement',
            'severity_status', 'issue_status', 'remediation_status',
            'remediation_deadline_date', 'actual_remediation_date',
            'management_action_plan', 'working_papers'
        ]
        widgets = {
            'date_identified': forms.DateInput(attrs={'type': 'date'}),
            'remediation_deadline_date': forms.DateInput(attrs={'type': 'date'}),
            'actual_remediation_date': forms.DateInput(attrs={'type': 'date'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.organization:
            self.fields['engagement'].queryset = Engagement.objects.filter(
                organization=self.organization
            )
            self.fields['issue_owner'].queryset = CustomUser.objects.filter(
                organization=self.organization
            )
        
        self.helper.layout = Layout(
            Fieldset(
                _('Basic Information'),
                Row(
                    Column(FloatingField('code'), css_class='col-md-6'),
                    Column(FloatingField('issue_title'), css_class='col-md-6'),
                ),
                Row(
                    Column('engagement', css_class='col-md-6'),
                    Column('date_identified', css_class='col-md-6'),
                ),
                Row(
                    Column('issue_owner', css_class='col-md-6'),
                    Column('issue_owner_title', css_class='col-md-6'),
                ),
                Row(
                    Column('severity_status', css_class='col-md-6'),
                    Column('issue_status', css_class='col-md-6'),
                ),
            ),
            Fieldset(
                _('Issue Details'),
                'issue_description',
                'root_cause',
                'risks',
                'audit_procedures',
                'recommendation',
            ),
            Fieldset(
                _('Remediation'),
                Row(
                    Column('remediation_status', css_class='col-md-6'),
                    Column('remediation_deadline_date', css_class='col-md-6'),
                ),
                'actual_remediation_date',
                'management_action_plan',
                'working_papers',
            ),
            ButtonHolder(
                Submit('submit', _('Save'), css_class='btn-primary'),
                css_class='mt-3'
            )
        )

# ─── APPROVAL FORMS ──────────────────────────────────────────────────────────
class ApprovalForm(BaseAuditForm):
    class Meta:
        model = Approval
        fields = ['content_type', 'object_id', 'comments']
        widgets = {
            'content_type': forms.HiddenInput(),
            'object_id': forms.HiddenInput(),
        }
    
    def __init__(self, *args, **kwargs):
        self.requester = kwargs.pop('requester', None)
        super().__init__(*args, **kwargs)
        
        self.helper.layout = Layout(
            Fieldset(
                _('Approval Request'),
                'comments',
            ),
            ButtonHolder(
                Submit('submit', _('Submit for Approval'), css_class='btn-primary'),
                css_class='mt-3'
            )
        )
    
    def clean(self):
        cleaned_data = super().clean()
        content_type = cleaned_data.get('content_type')
        object_id = cleaned_data.get('object_id')
        
        if content_type and object_id:
            try:
                obj = content_type.get_object_for_this_type(pk=object_id)
                if not obj.organization == self.organization:
                    raise forms.ValidationError(_("Invalid object for this organization"))
            except Exception:
                raise forms.ValidationError(_("Invalid object"))
        
        return cleaned_data
