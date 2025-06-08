from django import forms
from django.utils.translation import gettext_lazy as _
from django.contrib.contenttypes.models import ContentType
from django.contrib.auth import get_user_model
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Submit, Row, Column, Fieldset, ButtonHolder
from crispy_bootstrap5.bootstrap5 import FloatingField
from django.forms import EmailInput, TextInput
from django.core.validators import RegexValidator
from django_ckeditor_5.widgets import CKEditor5Widget
from django.core.exceptions import ValidationError

from organizations.models import Organization
from users.models import CustomUser

from .models import AuditWorkplan, Engagement, Issue, Approval, Objective
from .models.followupaction import FollowUpAction
from .models.issueretest import IssueRetest
from .models.note import Note, Notification
from .models.procedure import Procedure
from .models.procedureresult import ProcedureResult
from .models.recommendation import Recommendation
from .models.issue_working_paper import IssueWorkingPaper
from .models.engagement import Engagement
from .models.risk import Risk

# ─── BASE FORM CLASS ──────────────────────────────────────────────────────────
class BaseAuditForm(forms.ModelForm):
    """Base form class with common functionality for all audit forms"""
    
    def __init__(self, *args, **kwargs):
        self.organization = kwargs.pop('organization', None)
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_tag = False
        self.helper.disable_csrf = True
        
        # Apply organization filtering to all foreign key fields
        if self.organization:
            for field_name, field in self.fields.items():
                # Filter FK fields by organization
                if hasattr(field, 'queryset') and field.queryset is not None:
                    model = field.queryset.model
                    if hasattr(model, 'organization'):
                        field.queryset = field.queryset.filter(organization=self.organization)
    
    def clean(self):
        cleaned_data = super().clean()
        
        # Ensure all related objects belong to the same organization
        if self.organization:
            for field_name, value in cleaned_data.items():
                if hasattr(value, 'organization') and hasattr(value.organization, 'pk'):
                    if value.organization.pk != self.organization.pk:
                        self.add_error(field_name, _('Selected item must belong to your organization'))
                        
        # Set organization on the form instance
        if hasattr(self.instance, 'organization') and self.organization:
            self.instance.organization = self.organization
            
        return cleaned_data

# ─── WORKPLAN FORMS ──────────────────────────────────────────────────────────
class AuditWorkplanForm(BaseAuditForm):
    class Meta:
        model = AuditWorkplan
        fields = ['code', 'name', 'fiscal_year', 'objectives', 'description', 
                 'approval_status', 'estimated_total_hours', 'priority_ranking']
        widgets = {
            'fiscal_year': forms.NumberInput(attrs={'min': 2000, 'max': 2100}),
            'objectives': CKEditor5Widget(config_name='extends', attrs={'class': 'django_ckeditor_5'}),
            'description': CKEditor5Widget(config_name='extends', attrs={'class': 'django_ckeditor_5'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Ensure CKEditor fields are properly configured
        if 'objectives' in self.fields:
            self.fields['objectives'].required = False
            # Initialize with empty string if None to prevent serialization errors
            if self.initial and 'objectives' in self.initial and self.initial['objectives'] is None:
                self.initial['objectives'] = ''
        if 'description' in self.fields:
            self.fields['description'].required = False
            # Initialize with empty string if None to prevent serialization errors
            if self.initial and 'description' in self.initial and self.initial['description'] is None:
                self.initial['description'] = ''
            
        self.helper.layout = Layout(
            Fieldset(
                _('Basic Information'),
                Row(
                    Column(FloatingField('code'), css_class='col-md-6'),
                    Column(FloatingField('name'), css_class='col-md-6'),
                ),
                Row(
                    Column(FloatingField('fiscal_year'), css_class='col-md-6'),
                    Column('approval_status', css_class='col-md-6'),
                ),
                Row(
                    Column('estimated_total_hours', css_class='col-md-6'),
                    Column('priority_ranking', css_class='col-md-6'),
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
            'code', 'title', 'annual_workplan', 'engagement_type',
            'project_start_date', 'target_end_date', 'assigned_to',
            'estimated_hours', 'criteria',
            'field_work_start_date', 'field_work_end_date', 'report_issued_date',
            'executive_summary', 'purpose', 'background', 'scope',
            'conclusion_description', 'conclusion',
            'project_status', 'approval_status'
        ]
        widgets = {
            'project_start_date': forms.DateInput(attrs={'type': 'date'}),
            'target_end_date': forms.DateInput(attrs={'type': 'date'}),
            'field_work_start_date': forms.DateInput(attrs={'type': 'date'}),
            'field_work_end_date': forms.DateInput(attrs={'type': 'date'}),
            'report_issued_date': forms.DateInput(attrs={'type': 'date'}),
            'executive_summary': CKEditor5Widget(config_name='extends', attrs={'class': 'django_ckeditor_5'}),
            'purpose': CKEditor5Widget(config_name='extends', attrs={'class': 'django_ckeditor_5'}),
            'background': CKEditor5Widget(config_name='extends', attrs={'class': 'django_ckeditor_5'}),
            'scope': CKEditor5Widget(config_name='extends', attrs={'class': 'django_ckeditor_5'}),
            'criteria': CKEditor5Widget(config_name='extends', attrs={'class': 'django_ckeditor_5'}),
            'conclusion_description': CKEditor5Widget(config_name='extends', attrs={'class': 'django_ckeditor_5'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.organization:
            self.fields['annual_workplan'].queryset = AuditWorkplan.objects.filter(
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
                    Column('annual_workplan', css_class='col-md-6'),
                    Column('engagement_type', css_class='col-md-6'),
                ),
                Row(
                    Column('project_start_date', css_class='col-md-6'),
                    Column('target_end_date', css_class='col-md-6'),
                ),
                Row(
                    Column('assigned_to', css_class='col-md-6'),
                    Column('estimated_hours', css_class='col-md-6'),
                ),
            ),
            Fieldset(
                _('Project Status'),
                Row(
                    Column('project_status', css_class='col-md-6'),
                    Column('approval_status', css_class='col-md-6'),
                ),
                Row(
                    Column('field_work_start_date', css_class='col-md-4'),
                    Column('field_work_end_date', css_class='col-md-4'),
                    Column('report_issued_date', css_class='col-md-4'),
                ),
            ),
            Fieldset(
                _('Engagement Details'),
                'criteria',
                'executive_summary',
                'purpose',
                'background',
                'scope',
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
            'risks', 'date_identified', 'issue_owner', 'secondary_owner',
            'issue_owner_email', 'issue_owner_title',
            'audit_procedures', 'issue_status', 'remediation_status',
            'target_date', 'actual_remediation_date',
            'procedure', 'impact', 'likelihood', 'risk_level',
            'issue_type', 'is_repeat_issue', 'prior_issue_reference'
        ]
        widgets = {
            'date_identified': forms.DateInput(attrs={'type': 'date'}),
            'target_date': forms.DateInput(attrs={'type': 'date'}),
            'actual_remediation_date': forms.DateInput(attrs={'type': 'date'}),
        }
    
    def __init__(self, *args, **kwargs):
        # Extract specific context parameters for filtering if available
        procedure_result_pk = kwargs.pop('procedure_result_pk', None)
        procedure_pk = kwargs.pop('procedure_pk', None)
        objective_pk = kwargs.pop('objective_pk', None)
        engagement_pk = kwargs.pop('engagement_pk', None)
        
        super().__init__(*args, **kwargs)
        
        if self.organization:
            # Base filter for organization (robust chain)
            procedure_queryset = self.fields['procedure'].queryset.filter(
                risk__objective__engagement__organization=self.organization
            )
            # Apply hierarchical filtering based on provided context
            if procedure_pk:
                procedure_queryset = procedure_queryset.filter(id=procedure_pk)
            elif objective_pk:
                procedure_queryset = procedure_queryset.filter(risk__objective_id=objective_pk)
            elif engagement_pk:
                procedure_queryset = procedure_queryset.filter(risk__objective__engagement_id=engagement_pk)
            self.fields['procedure'].queryset = procedure_queryset
            # If there's only one option and it matches our context, preselect it and make read-only
            if procedure_pk and procedure_queryset.count() == 1:
                self.fields['procedure'].initial = procedure_pk
                self.fields['procedure'].widget.attrs['readonly'] = True
            # Filter issue owners to current organization
            self.fields['issue_owner'].queryset = CustomUser.objects.filter(
                organization=self.organization
            )
            if 'secondary_owner' in self.fields:
                self.fields['secondary_owner'].queryset = CustomUser.objects.filter(
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
                    Column('procedure', css_class='col-md-6'),
                    Column('date_identified', css_class='col-md-6'),
                ),
                Row(
                    Column('issue_owner', css_class='col-md-4'),
                    Column('secondary_owner', css_class='col-md-4'),
                    Column('issue_owner_email', css_class='col-md-4'),
                ),
                Row(
                    Column('issue_type', css_class='col-md-6'),
                    Column('issue_status', css_class='col-md-6'),
                ),
            ),
            Fieldset(
                _('Risk and Severity Assessment'),
                Row(
                    Column('impact', css_class='col-md-4'),
                    Column('likelihood', css_class='col-md-4'),
                    Column('risk_level', css_class='col-md-4'),
                ),
            ),
            Fieldset(
                _('Issue Details'),
                'issue_description',
                'root_cause',
                'risks',
                'audit_procedures',
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

class WorkplanFilterForm(forms.Form):
    q = forms.CharField(label=_('Search'), required=False, widget=forms.TextInput(attrs={'placeholder': 'Name or Code', 'class': 'form-control'}))
    status = forms.ChoiceField(label=_('Status'), required=False, choices=[('', 'All')] + AuditWorkplan._meta.get_field('approval_status').choices, widget=forms.Select(attrs={'class': 'form-select'}))
    fiscal_year = forms.IntegerField(label=_('Fiscal Year'), required=False, widget=forms.NumberInput(attrs={'class': 'form-control', 'min': 2000, 'max': 2100}))
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'get'
        self.helper.form_show_labels = False
        self.helper.layout = Layout(
            Row(
                Column('q', css_class='col-md-4'),
                Column('status', css_class='col-md-3'),
                Column('fiscal_year', css_class='col-md-3'),
                Column(Submit('filter', _('Filter'), css_class='btn-primary mt-0'), css_class='col-md-2 align-self-end'),
            )
        )

class EngagementFilterForm(forms.Form):
    q = forms.CharField(label=_('Search'), required=False, widget=forms.TextInput(attrs={'placeholder': 'Title or Code', 'class': 'form-control'}))
    status = forms.ChoiceField(label=_('Status'), required=False, choices=[('', 'All')] + Engagement._meta.get_field('project_status').choices, widget=forms.Select(attrs={'class': 'form-select'}))
    owner = forms.CharField(label=_('Assigned To'), required=False, widget=forms.TextInput(attrs={'placeholder': 'Owner Email', 'class': 'form-control'}))
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'get'
        self.helper.form_show_labels = False
        self.helper.layout = Layout(
            Row(
                Column('q', css_class='col-md-4'),
                Column('status', css_class='col-md-3'),
                Column('owner', css_class='col-md-3'),
                Column(Submit('filter', _('Filter'), css_class='btn-primary mt-0'), css_class='col-md-2 align-self-end'),
            )
        )

class IssueFilterForm(forms.Form):
    q = forms.CharField(label=_('Search'), required=False, widget=forms.TextInput(attrs={'placeholder': 'Title or Code', 'class': 'form-control'}))
    status = forms.ChoiceField(label=_('Status'), required=False, choices=[('', 'All')] + Issue._meta.get_field('issue_status').choices, widget=forms.Select(attrs={'class': 'form-select'}))
    severity = forms.ChoiceField(label=_('Severity'), required=False, choices=[('', 'All')] + Issue._meta.get_field('risk_level').choices, widget=forms.Select(attrs={'class': 'form-select'}))
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'get'
        self.helper.form_show_labels = False
        self.helper.layout = Layout(
            Row(
                Column('q', css_class='col-md-4'),
                Column('status', css_class='col-md-3'),
                Column('severity', css_class='col-md-3'),
                Column(Submit('filter', _('Filter'), css_class='btn-primary mt-0'), css_class='col-md-2 align-self-end'),
            )
        )

class EngagementOverviewForm(forms.ModelForm):
    class Meta:
        model = Engagement
        fields = [
            'title', 'project_start_date', 'target_end_date', 'project_status',
            'executive_summary', 'scope', 'background', 'assigned_to', 'assigned_by',
        ]
        widgets = {
            'executive_summary': CKEditor5Widget(config_name='extends'),
            'scope': CKEditor5Widget(config_name='extends'),
            'background': CKEditor5Widget(config_name='extends'),
            'project_start_date': forms.DateInput(attrs={'type': 'date'}),
            'target_end_date': forms.DateInput(attrs={'type': 'date'}),
        }

    def __init__(self, *args, **kwargs):
        org = kwargs.pop('organization', None)
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.add_input(Submit('submit', 'Save & Continue'))
        if org:
            self.fields['assigned_to'].queryset = self.fields['assigned_to'].queryset.filter(organization=org)
            self.fields['assigned_by'].queryset = self.fields['assigned_by'].queryset.filter(organization=org)

class ObjectiveForm(BaseAuditForm):
    class Meta:
        model = Objective
        fields = [
            'title', 'description', 'priority', 'criteria',
            'assigned_to', 'status', 'estimated_hours', 'order',
            'start_date', 'completion_date'
        ]
        widgets = {
            'description': CKEditor5Widget(config_name='extends'),
            'criteria': CKEditor5Widget(config_name='extends'),
            'start_date': forms.DateInput(attrs={'type': 'date'}),
            'completion_date': forms.DateInput(attrs={'type': 'date'}),
        }

    def __init__(self, *args, **kwargs):
        # Extract specific engagement_pk for filtering if available
        engagement_pk = kwargs.pop('engagement_pk', None)
        super().__init__(*args, **kwargs)
        
        if self.organization:
            # Filter assigned_to to users in the organization
            self.fields['assigned_to'].queryset = CustomUser.objects.filter(
                organization=self.organization
            )
            
            # If engagement_pk is provided, set it as the initial value
            if engagement_pk and not self.instance.pk:
                self.fields['engagement'].initial = engagement_pk
                self.fields['engagement'].widget.attrs['readonly'] = True
        
        # Set up crispy form layout
        self.helper.layout = Layout(
            Fieldset(
                _('Objective Information'),
                'title',
                Row(
                    Column('priority', css_class='col-md-6'),
                    Column('status', css_class='col-md-6'),
                ),
                Row(
                    Column('assigned_to', css_class='col-md-6'),
                    Column('estimated_hours', css_class='col-md-6'),
                ),
                'order',
            ),
            Fieldset(
                _('Objective Details'),
                'description',
                'criteria',
            ),
            ButtonHolder(
                Submit('submit', _('Save'), css_class='btn-primary'),
                css_class='mt-3'
            )
        )

class ProcedureForm(BaseAuditForm):
    class Meta:
        model = Procedure
        fields = [
            'title', 'description', 'order', 'test_date', 'tested_by',
            'procedure_type', 'control_being_tested', 'criteria', 'sample_size',
            'sampling_method', 'planned_date', 'estimated_hours', 'actual_hours',
            'test_status', 'result', 'result_notes', 'exceptions_noted',
            'exception_details', 'conclusion', 'impact_assessment',
            'is_positive_finding', 'control_maturity', 'evidence_list',
            'evidence', 'additional_evidence', 'reviewed_by', 'review_date',
            'review_notes', 'order', 'risk'
        ]
        widgets = {
            'description': CKEditor5Widget(config_name='extends', attrs={'class': 'django_ckeditor_5'}),
            'result_notes': CKEditor5Widget(config_name='extends', attrs={'class': 'django_ckeditor_5'}),
            'exception_details': CKEditor5Widget(config_name='extends', attrs={'class': 'django_ckeditor_5'}),
            'conclusion': CKEditor5Widget(config_name='extends', attrs={'class': 'django_ckeditor_5'}),
            'impact_assessment': CKEditor5Widget(config_name='extends', attrs={'class': 'django_ckeditor_5'}),
            'evidence_list': CKEditor5Widget(config_name='extends', attrs={'class': 'django_ckeditor_5'}),
            'review_notes': CKEditor5Widget(config_name='extends', attrs={'class': 'django_ckeditor_5'}),
            'test_date': forms.DateInput(attrs={'type': 'date'}),
            'planned_date': forms.DateInput(attrs={'type': 'date'}),
            'review_date': forms.DateInput(attrs={'type': 'date'}),
        }

    def __init__(self, *args, **kwargs):
        risk_pk = kwargs.pop('risk_id', None)
        objective_pk = kwargs.pop('objective_pk', None)
        engagement_pk = kwargs.pop('engagement_pk', None)
        super().__init__(*args, **kwargs)
        if self.organization:
            risk_queryset = self.fields['risk'].queryset.filter(
                objective__engagement__organization=self.organization
            )
            if objective_pk:
                risk_queryset = risk_queryset.filter(objective_id=objective_pk)
            elif engagement_pk:
                risk_queryset = risk_queryset.filter(objective__engagement_id=engagement_pk)
            self.fields['risk'].queryset = risk_queryset
        # If creating from a risk, set it as the initial value and restrict queryset to just that risk
        if risk_pk:
            try:
                from .models.risk import Risk
                risk = Risk.objects.get(pk=risk_pk)
                self.fields['risk'].initial = risk_pk
                self.fields['risk'].queryset = self.fields['risk'].queryset.filter(pk=risk_pk)
            except Exception:
                pass

class ProcedureResultForm(BaseAuditForm):
    class Meta:
        model = ProcedureResult
        fields = [
            'procedure', 'status', 'notes', 'is_for_the_record',
            'is_positive', 'order'
        ]
        widgets = {
            'notes': CKEditor5Widget(config_name='extends', attrs={'class': 'django_ckeditor_5'}),
        }
        
    def __init__(self, *args, **kwargs):
        procedure_pk = kwargs.pop('procedure_pk', None)
        objective_pk = kwargs.pop('objective_pk', None)
        engagement_pk = kwargs.pop('engagement_pk', None)
        super().__init__(*args, **kwargs)
        if self.organization:
            procedure_queryset = self.fields['procedure'].queryset.filter(
                risk__objective__engagement__organization=self.organization
            )
            if objective_pk:
                procedure_queryset = procedure_queryset.filter(risk__objective_id=objective_pk)
            elif engagement_pk:
                procedure_queryset = procedure_queryset.filter(risk__objective__engagement_id=engagement_pk)
            self.fields['procedure'].queryset = procedure_queryset
        
        self.helper.layout = Layout(
            Fieldset(
                _('Procedure Result'),
                'procedure',
                Row(
                    Column(FloatingField('status'), css_class='col-md-4'),
                    Column(FloatingField('order'), css_class='col-md-4'),
                    Column(FloatingField('is_for_the_record'), css_class='col-md-2'),
                    Column(FloatingField('is_positive'), css_class='col-md-2'),
                ),
                'notes',
            ),
            ButtonHolder(
                Submit('submit', _('Save'), css_class='btn-primary'),
                css_class='mt-3'
            )
        )

class RiskForm(BaseAuditForm):
    """Form for creating and editing Risk objects with organization scoping."""
    
    class Meta:
        model = Risk
        fields = [
            'title', 'objective', 'description', 'category', 'status',
            'likelihood', 'impact', 'risk_appetite', 'risk_tolerance',
            'control_effectiveness', 'mitigation_plan', 'existing_controls',
            'assigned_to', 'order'
        ]
        widgets = {
            'description': CKEditor5Widget(config_name='extends', attrs={'class': 'django_ckeditor_5'}),
            'mitigation_plan': CKEditor5Widget(config_name='extends', attrs={'class': 'django_ckeditor_5'}),
            'existing_controls': CKEditor5Widget(config_name='extends', attrs={'class': 'django_ckeditor_5'}),
        }
        
    def __init__(self, *args, **kwargs):
        objective_pk = kwargs.pop('objective_pk', None)
        engagement_pk = kwargs.pop('engagement_pk', None)
        super().__init__(*args, **kwargs)
        if self.organization:
            objective_queryset = self.fields['objective'].queryset.filter(
                engagement__organization=self.organization
            )
            if engagement_pk:
                objective_queryset = objective_queryset.filter(engagement_id=engagement_pk)
            self.fields['objective'].queryset = objective_queryset
        # If creating from an objective, set it as the initial value and restrict queryset to its engagement
        if objective_pk:
            try:
                from .models.objective import Objective
                objective = Objective.objects.get(pk=objective_pk)
                self.fields['objective'].initial = objective_pk
                self.fields['objective'].queryset = self.fields['objective'].queryset.filter(engagement=objective.engagement)
            except Exception:
                pass
        self.helper.layout = Layout(
            Fieldset(
                _('Risk Information'),
                Row(
                    Column(FloatingField('title'), css_class='col-md-8'),
                    Column(FloatingField('category'), css_class='col-md-4'),
                ),
                'objective',
                'description',
            ),
            Fieldset(
                _('Risk Assessment'),
                Row(
                    Column(FloatingField('likelihood'), css_class='col-md-4'),
                    Column(FloatingField('impact'), css_class='col-md-4'),
                    Column(FloatingField('status'), css_class='col-md-4'),
                ),
                Row(
                    Column(FloatingField('risk_appetite'), css_class='col-md-4'),
                    Column(FloatingField('risk_tolerance'), css_class='col-md-4'),
                    Column(FloatingField('control_effectiveness'), css_class='col-md-4'),
                ),
            ),
            Fieldset(
                _('Risk Response'),
                'mitigation_plan',
                'existing_controls',
                Row(
                    Column(FloatingField('assigned_to'), css_class='col-md-6'),
                    Column(FloatingField('order'), css_class='col-md-6'),
                ),
            ),
            ButtonHolder(
                Submit('submit', _('Save'), css_class='btn-primary'),
                css_class='mt-3'
            )
        )

# ─── FOLLOW UP ACTION FORM ───────────────────────────────────────────────────
class FollowUpActionForm(BaseAuditForm):
    class Meta:
        model = FollowUpAction
        fields = [
            'issue', 'description', 'assigned_to', 'due_date',
            'status', 'completed_at', 'completion_evidence'
        ]
        widgets = {
            'description': CKEditor5Widget(config_name='extends', attrs={'class': 'django_ckeditor_5'}),
            'completion_evidence': CKEditor5Widget(config_name='extends', attrs={'class': 'django_ckeditor_5'}),
            'due_date': forms.DateInput(attrs={'type': 'date'}),
            'completed_at': forms.DateInput(attrs={'type': 'date'}),
        }
        
    def __init__(self, *args, **kwargs):
        procedure_pk = kwargs.pop('procedure_pk', None)
        objective_pk = kwargs.pop('objective_pk', None)
        engagement_pk = kwargs.pop('engagement_pk', None)
        super().__init__(*args, **kwargs)
        if self.organization:
            issue_queryset = self.fields['issue'].queryset.filter(
                procedure__risk__objective__engagement__organization=self.organization
            )
            if procedure_pk:
                issue_queryset = issue_queryset.filter(procedure_id=procedure_pk)
            elif objective_pk:
                issue_queryset = issue_queryset.filter(procedure__risk__objective_id=objective_pk)
            elif engagement_pk:
                issue_queryset = issue_queryset.filter(procedure__risk__objective__engagement_id=engagement_pk)
            self.fields['issue'].queryset = issue_queryset
            
            self.fields['assigned_to'].queryset = self.fields['assigned_to'].queryset.filter(
                organization=self.organization
            )
        
        self.helper.layout = Layout(
            Fieldset(
                _('Action Information'),
                'issue',
                'description',
                Row(
                    Column(FloatingField('assigned_to'), css_class='col-md-6'),
                    Column(FloatingField('due_date'), css_class='col-md-6'),
                ),
            ),
            Fieldset(
                _('Status & Completion'),
                Row(
                    Column(FloatingField('status'), css_class='col-md-6'),
                    Column(FloatingField('completed_at'), css_class='col-md-6'),
                ),
                'completion_evidence',
            ),
            ButtonHolder(
                Submit('submit', _('Save'), css_class='btn-primary'),
                css_class='mt-3'
            )
        )

# ─── ISSUE RETEST FORM ──────────────────────────────────────────────────────
class IssueRetestForm(BaseAuditForm):
    class Meta:
        model = IssueRetest
        fields = [
            'issue', 'retest_date', 'retested_by', 'result',
            'test_evidence', 'test_approach', 'notes'
        ]
        widgets = {
            'test_evidence': CKEditor5Widget(config_name='extends', attrs={'class': 'django_ckeditor_5'}),
            'test_approach': CKEditor5Widget(config_name='extends', attrs={'class': 'django_ckeditor_5'}),
            'notes': CKEditor5Widget(config_name='extends', attrs={'class': 'django_ckeditor_5'}),
            'retest_date': forms.DateInput(attrs={'type': 'date'}),
        }
        
    def __init__(self, *args, **kwargs):
        procedure_pk = kwargs.pop('procedure_pk', None)
        objective_pk = kwargs.pop('objective_pk', None)
        engagement_pk = kwargs.pop('engagement_pk', None)
        super().__init__(*args, **kwargs)
        if self.organization:
            issue_queryset = self.fields['issue'].queryset.filter(
                procedure__risk__objective__engagement__organization=self.organization
            )
            if procedure_pk:
                issue_queryset = issue_queryset.filter(procedure_id=procedure_pk)
            elif objective_pk:
                issue_queryset = issue_queryset.filter(procedure__risk__objective_id=objective_pk)
            elif engagement_pk:
                issue_queryset = issue_queryset.filter(procedure__risk__objective__engagement_id=engagement_pk)
            self.fields['issue'].queryset = issue_queryset
            
            self.fields['retested_by'].queryset = self.fields['retested_by'].queryset.filter(
                organization=self.organization
            )
        
        self.helper.layout = Layout(
            Fieldset(
                _('Retest Information'),
                'issue',
                Row(
                    Column(FloatingField('retest_date'), css_class='col-md-6'),
                    Column(FloatingField('retested_by'), css_class='col-md-6'),
                ),
                Row(
                    Column(FloatingField('result'), css_class='col-md-12'),
                ),
                'test_evidence',
                'test_approach',
                'notes',
            ),
            ButtonHolder(
                Submit('submit', _('Save'), css_class='btn-primary'),
                css_class='mt-3'
            )
        )

# ─── NOTE FORM ───────────────────────────────────────────────────────────────────
class NoteForm(BaseAuditForm):
    class Meta:
        model = Note
        fields = [
            'note_type', 'content', 'status', 'assigned_to',
            'content_type', 'object_id'
        ]
        widgets = {
            'content': CKEditor5Widget(config_name='extends', attrs={'class': 'django_ckeditor_5'}),
            'content_type': forms.HiddenInput(),
            'object_id': forms.HiddenInput(),
        }
        
    def __init__(self, *args, **kwargs):
        self.related_object = kwargs.pop('related_object', None)
        super().__init__(*args, **kwargs)
        
        # Ensure CKEditor fields are properly handled
        if 'content' in self.fields:
            # Initialize with empty string if None to prevent serialization errors
            if self.initial and 'content' in self.initial and self.initial['content'] is None:
                self.initial['content'] = ''
        
        # Set content type and object ID if related object is provided
        if self.related_object and not self.instance.pk:
            from django.contrib.contenttypes.models import ContentType
            ct = ContentType.objects.get_for_model(self.related_object)
            self.initial['content_type'] = ct.id
            self.initial['object_id'] = self.related_object.id
            
        # Filter assigned_to users by organization
        if self.organization and 'assigned_to' in self.fields:
            self.fields['assigned_to'].queryset = get_user_model().objects.filter(
                organization=self.organization
            )
        
        # Set up form layout
        self.helper.layout = Layout(
            Fieldset(
                _('Note Details'),
                Row(
                    Column('note_type', css_class='col-md-6'),
                    Column('status', css_class='col-md-6'),
                ),
                'content',
                'assigned_to',
                'content_type',
                'object_id',
            ),
            ButtonHolder(
                Submit('submit', _('Save'), css_class='btn-primary'),
                css_class='mt-3'
            )
        )

    def clean(self):
        cleaned_data = super().clean()
        content_type_id = cleaned_data.get('content_type')
        if content_type_id:
            ct = ContentType.objects.get_for_id(content_type_id)
            if ct.model != 'engagement':
                raise ValidationError('Notes can only be attached to Engagements.')
        return cleaned_data

# ─── NOTIFICATION FORM ──────────────────────────────────────────────────────────
class NotificationForm(BaseAuditForm):
    class Meta:
        model = Notification
        fields = ['user', 'note', 'message', 'notification_type', 'is_read']
        
    def __init__(self, *args, **kwargs):
        # Get specific note_pk if available
        self.note_pk = kwargs.pop('note_pk', None)
        
        super().__init__(*args, **kwargs)
        
        # Apply organization filtering
        if self.organization:
            # Filter users by organization
            if 'user' in self.fields:
                self.fields['user'].queryset = self.fields['user'].queryset.filter(
                    organization=self.organization
                )
            
            # Filter notes by organization
            if 'note' in self.fields:
                note_queryset = self.fields['note'].queryset.filter(organization=self.organization)
                
                if self.note_pk:
                    note_queryset = note_queryset.filter(id=self.note_pk)
                    if note_queryset.count() == 1:
                        self.fields['note'].initial = self.note_pk
                        
                self.fields['note'].queryset = note_queryset
        
        # Set up form layout
        self.helper.layout = Layout(
            Fieldset(
                _('Notification Details'),
                Row(
                    Column(FloatingField('user'), css_class='col-md-6'),
                    Column(FloatingField('note'), css_class='col-md-6'),
                ),
                'message',
                Row(
                    Column(FloatingField('notification_type'), css_class='col-md-6'),
                    Column('is_read', css_class='col-md-6'),
                ),
            ),
            ButtonHolder(
                Submit('submit', _('Save'), css_class='btn-primary'),
                css_class='mt-3'
            )
        )

class RecommendationForm(BaseAuditForm):
    class Meta:
        model = Recommendation
        fields = [
            'title', 'description', 'issue', 'priority',
            'cost_benefit_analysis', 'assigned_to', 'estimated_hours',
            'estimated_cost', 'order', 'implementation_status',
            'target_date', 'revised_date', 'extension_reason',
            'implementation_date', 'verification_date', 'verified_by',
            'management_action_plan', 'effectiveness_evaluation',
            'effectiveness_rating'
        ]
        widgets = {
            'description': CKEditor5Widget(config_name='extends', attrs={'class': 'django_ckeditor_5'}),
            'cost_benefit_analysis': CKEditor5Widget(config_name='extends', attrs={'class': 'django_ckeditor_5'}),
            'extension_reason': CKEditor5Widget(config_name='extends', attrs={'class': 'django_ckeditor_5'}),
            'management_action_plan': CKEditor5Widget(config_name='extends', attrs={'class': 'django_ckeditor_5'}),
            'effectiveness_evaluation': CKEditor5Widget(config_name='extends', attrs={'class': 'django_ckeditor_5'}),
            'target_date': forms.DateInput(attrs={'type': 'date'}),
            'revised_date': forms.DateInput(attrs={'type': 'date'}),
            'implementation_date': forms.DateInput(attrs={'type': 'date'}),
            'verification_date': forms.DateInput(attrs={'type': 'date'}),
        }

    def __init__(self, *args, **kwargs):
        procedure_pk = kwargs.pop('procedure_pk', None)
        objective_pk = kwargs.pop('objective_pk', None)
        engagement_pk = kwargs.pop('engagement_pk', None)
        super().__init__(*args, **kwargs)
        if self.organization:
            issue_queryset = self.fields['issue'].queryset.filter(
                procedure__risk__objective__engagement__organization=self.organization
            )
            if procedure_pk:
                issue_queryset = issue_queryset.filter(procedure_id=procedure_pk)
            elif objective_pk:
                issue_queryset = issue_queryset.filter(procedure__risk__objective_id=objective_pk)
            elif engagement_pk:
                issue_queryset = issue_queryset.filter(procedure__risk__objective__engagement_id=engagement_pk)
            self.fields['issue'].queryset = issue_queryset
            
            self.fields['assigned_to'].queryset = CustomUser.objects.filter(
                organization=self.organization
            )
            self.fields['verified_by'].queryset = CustomUser.objects.filter(
                organization=self.organization
            )
            
            # If issue_pk is provided, set it as the initial value
            if procedure_pk:
                self.fields['issue'].initial = procedure_pk
                self.fields['issue'].widget.attrs['readonly'] = True

class IssueWorkingPaperForm(BaseAuditForm):
    class Meta:
        model = IssueWorkingPaper
        fields = ['issue', 'file', 'description']
        widgets = {
            'description': forms.TextInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        issue_pk = kwargs.pop('issue_pk', None)
        super().__init__(*args, **kwargs)
        
        if self.organization:
            # Filter issue field to only show issues from this organization
            self.fields['issue'].queryset = Issue.objects.filter(
                organization=self.organization
            )
            
            # If issue_pk is provided, set it as the initial value
            if issue_pk:
                self.fields['issue'].initial = issue_pk
                self.fields['issue'].widget.attrs['readonly'] = True
        
        self.helper.layout = Layout(
            Fieldset(
                _('Working Paper Information'),
                'issue',
                'file',
                'description',
            ),
            ButtonHolder(
                Submit('submit', _('Save'), css_class='btn-primary'),
                css_class='mt-3'
            )
        )
