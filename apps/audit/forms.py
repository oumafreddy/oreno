from django import forms
from django.utils.translation import gettext_lazy as _
from django.contrib.contenttypes.models import ContentType
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Submit, Row, Column, Fieldset, ButtonHolder
from crispy_bootstrap5.bootstrap5 import FloatingField
from django.forms import EmailInput, TextInput
from django.core.validators import RegexValidator
from django_ckeditor_5.widgets import CKEditor5Widget

from organizations.models import Organization
from users.models import CustomUser

from .models import AuditWorkplan, Engagement, Issue, Approval, Objective
from .models.followupaction import FollowUpAction
from .models.issueretest import IssueRetest
from .models.note import Note
from .models.procedure import Procedure
from .models.procedureresult import ProcedureResult
from .models.recommendation import Recommendation
from .models.issue_working_paper import IssueWorkingPaper
from .models.engagement import Engagement

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
            'conclusion_description', 'conclusion',
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
            'audit_procedures', 'procedure_result',
            'severity_status', 'issue_status',
        ]
        widgets = {
            'date_identified': forms.DateInput(attrs={'type': 'date'}),
        }
    
    def __init__(self, *args, **kwargs):
        # Extract specific context parameters for filtering if available
        procedure_result_pk = kwargs.pop('procedure_result_pk', None)
        procedure_pk = kwargs.pop('procedure_pk', None)
        objective_pk = kwargs.pop('objective_pk', None)
        engagement_pk = kwargs.pop('engagement_pk', None)
        
        super().__init__(*args, **kwargs)
        
        if self.organization:
            # Base filter for organization
            procedure_result_queryset = self.fields['procedure_result'].queryset.filter(
                procedure__objective__engagement__organization=self.organization
            )
            
            # Apply hierarchical filtering based on provided context
            if procedure_result_pk:
                # If specific procedure result is provided
                procedure_result_queryset = procedure_result_queryset.filter(id=procedure_result_pk)
            elif procedure_pk:
                # If specific procedure is provided
                procedure_result_queryset = procedure_result_queryset.filter(procedure_id=procedure_pk)
            elif objective_pk:
                # If specific objective is provided
                procedure_result_queryset = procedure_result_queryset.filter(procedure__objective_id=objective_pk)
            elif engagement_pk:
                # If specific engagement is provided
                procedure_result_queryset = procedure_result_queryset.filter(procedure__objective__engagement_id=engagement_pk)
            
            self.fields['procedure_result'].queryset = procedure_result_queryset
            
            # If there's only one option and it matches our context, preselect it and make read-only
            if procedure_result_pk and procedure_result_queryset.count() == 1:
                self.fields['procedure_result'].initial = procedure_result_pk
                self.fields['procedure_result'].widget.attrs['readonly'] = True
            
            # Filter issue owners to current organization
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
                    Column('procedure_result', css_class='col-md-6'),
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
    status = forms.ChoiceField(label=_('Status'), required=False, choices=[('', 'All')] + AuditWorkplan._meta.get_field('state').choices, widget=forms.Select(attrs={'class': 'form-select'}))
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
    severity = forms.ChoiceField(label=_('Severity'), required=False, choices=[('', 'All')] + Issue._meta.get_field('severity_status').choices, widget=forms.Select(attrs={'class': 'form-select'}))
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

class ObjectiveForm(forms.ModelForm):
    class Meta:
        model = Objective
        fields = ['title', 'description', 'order']
        widgets = {
            'description': CKEditor5Widget(config_name='extends'),
        }

    def __init__(self, *args, **kwargs):
        org = kwargs.pop('organization', None)
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.add_input(Submit('submit', 'Add Objective'))

# ─── FOLLOW UP ACTION FORM ───────────────────────────────────────────────────
class FollowUpActionForm(BaseAuditForm):
    class Meta:
        model = FollowUpAction
        fields = [
            'issue', 'description', 'assigned_to', 'due_date',
            'status', 'completed_at', 'notes', 'created_by'
        ]
        widgets = {
            'description': CKEditor5Widget(config_name='extends'),
            'notes': CKEditor5Widget(config_name='extends'),
            'due_date': forms.DateInput(attrs={'type': 'date'}),
            'completed_at': forms.DateTimeInput(attrs={'type': 'datetime-local'}),
        }
    def __init__(self, *args, **kwargs):
        # Extract specific context parameters for filtering
        self.issue_pk = kwargs.pop('issue_pk', None)
        procedure_pk = kwargs.pop('procedure_pk', None)
        objective_pk = kwargs.pop('objective_pk', None)
        engagement_pk = kwargs.pop('engagement_pk', None)
        
        super().__init__(*args, **kwargs)
        
        if self.organization:
            # Base filter for organization
            issue_queryset = self.fields['issue'].queryset.filter(organization=self.organization)
            
            # Apply hierarchical filtering based on provided context
            if self.issue_pk:
                # If specific issue is provided
                issue_queryset = issue_queryset.filter(id=self.issue_pk)
            elif procedure_pk:
                # If specific procedure is provided
                issue_queryset = issue_queryset.filter(procedure_result__procedure_id=procedure_pk)
            elif objective_pk:
                # If specific objective is provided
                issue_queryset = issue_queryset.filter(procedure_result__procedure__objective_id=objective_pk)
            elif engagement_pk:
                # If specific engagement is provided
                issue_queryset = issue_queryset.filter(procedure_result__procedure__objective__engagement_id=engagement_pk)
            
            self.fields['issue'].queryset = issue_queryset
            
            # If there's only one option and it matches our context, preselect it and make read-only
            if self.issue_pk and issue_queryset.count() == 1:
                self.fields['issue'].initial = self.issue_pk
                self.fields['issue'].widget.attrs['readonly'] = True
            
            # Filter assigned_to to current organization
            self.fields['assigned_to'].queryset = self.fields['assigned_to'].queryset.filter(organization=self.organization)
        
        self.helper.layout = Layout(
            Fieldset(
                _('Follow Up Action'),
                'issue',
                'description',
                Row(
                    Column('assigned_to', css_class='col-md-6'),
                    Column('due_date', css_class='col-md-6'),
                ),
                Row(
                    Column('status', css_class='col-md-6'),
                    Column('completed_at', css_class='col-md-6'),
                ),
                'notes',
                'created_by',
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
            'issue', 'retest_date', 'retested_by', 'result', 'notes'
        ]
        widgets = {
            'retest_date': forms.DateInput(attrs={'type': 'date'}),
            'notes': CKEditor5Widget(config_name='extends'),
        }
    def __init__(self, *args, **kwargs):
        self.issue_pk = kwargs.pop('issue_pk', None)
        super().__init__(*args, **kwargs)
        if self.organization:
            self.fields['retested_by'].queryset = self.fields['retested_by'].queryset.filter(organization=self.organization)
        self.helper.layout = Layout(
            Fieldset(
                _('Issue Retest'),
                'issue',
                Row(
                    Column('retest_date', css_class='col-md-6'),
                    Column('retested_by', css_class='col-md-6'),
                ),
                'result',
                'notes',
            ),
            ButtonHolder(
                Submit('submit', _('Save'), css_class='btn-primary'),
                css_class='mt-3'
            )
        )

# ─── NOTE FORM ──────────────────────────────────────────────────────────────
class NoteForm(BaseAuditForm):
    class Meta:
        model = Note
        fields = [
            'note_type', 'status', 'content', 'user', 'assigned_to', 'closed_by',
            'cleared_at', 'closed_at'
        ]
        widgets = {
            'cleared_at': forms.DateInput(attrs={'type': 'datetime-local'}),
            'closed_at': forms.DateInput(attrs={'type': 'datetime-local'}),
        }

    def __init__(self, *args, **kwargs):
        self.issue_pk = kwargs.pop('issue_pk', None)
        super().__init__(*args, **kwargs)
        # Only allow notes for Engagements
        if hasattr(self, 'instance') and self.instance.pk:
            content_object = self.instance.content_object
            if not isinstance(content_object, Engagement):
                self.fields['content'].disabled = True
                self.fields['note_type'].disabled = True
                self.fields['status'].disabled = True

    def clean(self):
        cleaned_data = super().clean()
        # Only allow notes for Engagements
        content_object = getattr(self.instance, 'content_object', None)
        if content_object and not isinstance(content_object, Engagement):
            raise forms.ValidationError(_('Notes can only be created for Engagements.'))
        return cleaned_data

# ─── PROCEDURE FORM ─────────────────────────────────────────────────────────
class ProcedureForm(BaseAuditForm):
    class Meta:
        model = Procedure
        fields = [
            'objective', 'title', 'description', 'related_risks', 'order'
        ]
        widgets = {
            'description': CKEditor5Widget(config_name='extends'),
        }
    def __init__(self, *args, **kwargs):
        # Extract specific objective_pk for filtering if available
        objective_pk = kwargs.pop('objective_pk', None)
        # Extract specific engagement_pk for filtering if available
        engagement_pk = kwargs.pop('engagement_pk', None)
        
        super().__init__(*args, **kwargs)
        
        # Filter objectives to the current organization
        if self.organization:
            objective_queryset = self.fields['objective'].queryset.filter(engagement__organization=self.organization)
            
            # Further filter by engagement if specified
            if engagement_pk:
                objective_queryset = objective_queryset.filter(engagement_id=engagement_pk)
            # Further filter by specific objective if this is for a procedure within a specific objective
            elif objective_pk:
                objective_queryset = objective_queryset.filter(id=objective_pk)
                
            self.fields['objective'].queryset = objective_queryset
            
            # If there's only one option and it matches our context, preselect it and make read-only
            if objective_pk and objective_queryset.count() == 1:
                self.fields['objective'].initial = objective_pk
                self.fields['objective'].widget.attrs['readonly'] = True
                
        self.helper.layout = Layout(
            Fieldset(
                _('Procedure'),
                'objective',
                'title',
                'description',
                'related_risks',
                'order',
            ),
            ButtonHolder(
                Submit('submit', _('Save'), css_class='btn-primary'),
                css_class='mt-3'
            )
        )

# ─── PROCEDURE RESULT FORM ──────────────────────────────────────────────────
class ProcedureResultForm(BaseAuditForm):
    class Meta:
        model = ProcedureResult
        fields = [
            'procedure', 'status', 'notes', 'is_for_the_record', 'order', 'is_positive'
        ]
        widgets = {
            'notes': CKEditor5Widget(config_name='extends'),
        }
    def __init__(self, *args, **kwargs):
        # Extract specific procedure_pk for filtering if available
        procedure_pk = kwargs.pop('procedure_pk', None)
        # Extract specific objective_pk for filtering if available
        objective_pk = kwargs.pop('objective_pk', None)
        
        super().__init__(*args, **kwargs)
        
        # Filter procedures to the current organization
        if self.organization:
            procedure_queryset = self.fields['procedure'].queryset.filter(objective__engagement__organization=self.organization)
            
            # Further filter by objective if specified
            if objective_pk:
                procedure_queryset = procedure_queryset.filter(objective_id=objective_pk)
            # Further filter by specific procedure if this is for a result within a specific procedure
            elif procedure_pk:
                procedure_queryset = procedure_queryset.filter(id=procedure_pk)
                
            self.fields['procedure'].queryset = procedure_queryset
            
            # If there's only one option and it matches our context, preselect it and make read-only
            if procedure_pk and procedure_queryset.count() == 1:
                self.fields['procedure'].initial = procedure_pk
                self.fields['procedure'].widget.attrs['readonly'] = True
        
        self.helper.layout = Layout(
            Fieldset(
                _('Procedure Result'),
                'procedure',
                'status',
                'notes',
                Row(
                    Column('is_for_the_record', css_class='col-md-6'),
                    Column('is_positive', css_class='col-md-6'),
                ),
                'order',
            ),
            ButtonHolder(
                Submit('submit', _('Save'), css_class='btn-primary'),
                css_class='mt-3'
            )
        )

# ─── RECOMMENDATION FORM ────────────────────────────────────────────────────
class RecommendationForm(BaseAuditForm):
    class Meta:
        model = Recommendation
        fields = [
            'issue', 'title', 'description', 'order'
            # Add any other business fields here as needed
        ]
        widgets = {
            'description': CKEditor5Widget(config_name='extends'),
        }

    def __init__(self, *args, **kwargs):
        # Extract specific issue_pk for filtering if available
        self.issue_pk = kwargs.pop('issue_pk', None)
        procedure_pk = kwargs.pop('procedure_pk', None)
        objective_pk = kwargs.pop('objective_pk', None)
        engagement_pk = kwargs.pop('engagement_pk', None)
        
        super().__init__(*args, **kwargs)
        
        if self.organization:
            # Base filter for organization
            issue_queryset = self.fields['issue'].queryset.filter(organization=self.organization)
            
            # Apply hierarchical filtering based on provided context
            if self.issue_pk:
                # If specific issue is provided
                issue_queryset = issue_queryset.filter(id=self.issue_pk)
            elif procedure_pk:
                # If specific procedure is provided
                issue_queryset = issue_queryset.filter(procedure_result__procedure_id=procedure_pk)
            elif objective_pk:
                # If specific objective is provided
                issue_queryset = issue_queryset.filter(procedure_result__procedure__objective_id=objective_pk)
            elif engagement_pk:
                # If specific engagement is provided
                issue_queryset = issue_queryset.filter(procedure_result__procedure__objective__engagement_id=engagement_pk)
            
            self.fields['issue'].queryset = issue_queryset
            
            # If there's only one option and it matches our context, preselect it and make read-only
            if self.issue_pk and issue_queryset.count() == 1:
                self.fields['issue'].initial = self.issue_pk
                self.fields['issue'].widget.attrs['readonly'] = True
        self.helper.layout = Layout(
            Fieldset(
                _('Recommendation'),
                'issue',
                'title',
                'description',
                'order',
            ),
            ButtonHolder(
                Submit('submit', _('Save'), css_class='btn-primary'),
                css_class='mt-3'
            )
        )

# ─── ISSUE WORKING PAPER FORM ───────────────────────────────────────────────
class IssueWorkingPaperForm(BaseAuditForm):
    class Meta:
        model = IssueWorkingPaper
        fields = ['file', 'description']
    def __init__(self, *args, **kwargs):
        self.issue_pk = kwargs.pop('issue_pk', None)
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.add_input(Submit('submit', _('Upload'), css_class='btn-primary'))
