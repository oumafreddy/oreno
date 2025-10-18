from django import forms
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Row, Column, Field, Div, Submit

from .models import (
    ModelAsset,
    DatasetAsset,
    TestPlan,
    TestRun,
    TestResult,
    Metric,
    EvidenceArtifact,
    Framework,
    Clause,
    ComplianceMapping,
    ConnectorConfig,
    WebhookSubscription,
    ModelRiskAssessment,
)


class ModelAssetForm(forms.ModelForm):
    class Meta:
        model = ModelAsset
        fields = [
            'name', 'model_type', 'uri', 'version', 'signature', 'extra',
            'contains_pii', 'data_classification', 'encryption_key_id'
        ]
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'model_type': forms.Select(attrs={'class': 'form-select'}),
            'uri': forms.TextInput(attrs={'class': 'form-control'}),
            'version': forms.TextInput(attrs={'class': 'form-control'}),
            'signature': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'extra': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'contains_pii': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'data_classification': forms.Select(attrs={'class': 'form-select'}),
            'encryption_key_id': forms.TextInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.add_input(Submit('submit', 'Save'))
        self.helper.layout = Layout(
            Row(
                Column('name', css_class='col-md-6'),
                Column('model_type', css_class='col-md-6'),
            ),
            Row(
                Column('uri', css_class='col-md-8'),
                Column('version', css_class='col-md-4'),
            ),
            'signature',
            'extra',
            Div(
                Row(
                    Column('contains_pii', css_class='col-md-4'),
                    Column('data_classification', css_class='col-md-4'),
                    Column('encryption_key_id', css_class='col-md-4'),
                ),
                css_class='border-top pt-3 mt-3'
            ),
        )


class DatasetAssetForm(forms.ModelForm):
    class Meta:
        model = DatasetAsset
        fields = [
            'name', 'role', 'path', 'format', 'schema', 'sensitive_attributes', 
            'label', 'extra', 'contains_pii', 'data_classification', 
            'encryption_key_id', 'retention_date'
        ]
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'role': forms.Select(attrs={'class': 'form-select'}),
            'path': forms.TextInput(attrs={'class': 'form-control'}),
            'format': forms.TextInput(attrs={'class': 'form-control'}),
            'schema': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'sensitive_attributes': forms.Textarea(attrs={'class': 'form-control', 'rows': 2}),
            'label': forms.TextInput(attrs={'class': 'form-control'}),
            'extra': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'contains_pii': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'data_classification': forms.Select(attrs={'class': 'form-select'}),
            'encryption_key_id': forms.TextInput(attrs={'class': 'form-control'}),
            'retention_date': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.add_input(Submit('submit', 'Save'))
        self.helper.layout = Layout(
            Row(
                Column('name', css_class='col-md-6'),
                Column('role', css_class='col-md-6'),
            ),
            Row(
                Column('path', css_class='col-md-8'),
                Column('format', css_class='col-md-4'),
            ),
            'schema',
            'sensitive_attributes',
            Row(
                Column('label', css_class='col-md-6'),
                Column('retention_date', css_class='col-md-6'),
            ),
            'extra',
            Div(
                Row(
                    Column('contains_pii', css_class='col-md-4'),
                    Column('data_classification', css_class='col-md-4'),
                    Column('encryption_key_id', css_class='col-md-4'),
                ),
                css_class='border-top pt-3 mt-3'
            ),
        )


class TestPlanForm(forms.ModelForm):
    class Meta:
        model = TestPlan
        fields = ['name', 'model_type', 'config', 'alert_rules']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'model_type': forms.Select(attrs={'class': 'form-select'}),
            'config': forms.Textarea(attrs={'class': 'form-control', 'rows': 8}),
            'alert_rules': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.add_input(Submit('submit', 'Save'))
        self.helper.layout = Layout(
            Row(
                Column('name', css_class='col-md-6'),
                Column('model_type', css_class='col-md-6'),
            ),
            'config',
            'alert_rules',
        )


class TestRunForm(forms.ModelForm):
    class Meta:
        model = TestRun
        fields = [
            'model_asset', 'dataset_asset', 'test_plan', 'parameters',
            'contains_pii', 'data_classification', 'encryption_key_id', 'retention_date'
        ]
        widgets = {
            'model_asset': forms.Select(attrs={'class': 'form-select'}),
            'dataset_asset': forms.Select(attrs={'class': 'form-select'}),
            'test_plan': forms.Select(attrs={'class': 'form-select'}),
            'parameters': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'contains_pii': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'data_classification': forms.Select(attrs={'class': 'form-select'}),
            'encryption_key_id': forms.TextInput(attrs={'class': 'form-control'}),
            'retention_date': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.add_input(Submit('submit', 'Save'))
        self.helper.add_input(Submit('run_test', 'Save & Run Test', css_class='btn btn-success'))
        self.helper.layout = Layout(
            Row(
                Column('model_asset', css_class='col-md-4'),
                Column('dataset_asset', css_class='col-md-4'),
                Column('test_plan', css_class='col-md-4'),
            ),
            'parameters',
            Div(
                Row(
                    Column('contains_pii', css_class='col-md-3'),
                    Column('data_classification', css_class='col-md-3'),
                    Column('encryption_key_id', css_class='col-md-3'),
                    Column('retention_date', css_class='col-md-3'),
                ),
                css_class='border-top pt-3 mt-3'
            ),
        )


class FrameworkForm(forms.ModelForm):
    class Meta:
        model = Framework
        fields = ['code', 'title', 'version', 'metadata']
        widgets = {
            'code': forms.TextInput(attrs={'class': 'form-control'}),
            'title': forms.TextInput(attrs={'class': 'form-control'}),
            'version': forms.TextInput(attrs={'class': 'form-control'}),
            'metadata': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.add_input(Submit('submit', 'Save'))
        self.helper.layout = Layout(
            Row(
                Column('code', css_class='col-md-4'),
                Column('title', css_class='col-md-4'),
                Column('version', css_class='col-md-4'),
            ),
            'metadata',
        )


class ClauseForm(forms.ModelForm):
    class Meta:
        model = Clause
        fields = ['framework', 'clause_code', 'text', 'metadata']
        widgets = {
            'framework': forms.Select(attrs={'class': 'form-select'}),
            'clause_code': forms.TextInput(attrs={'class': 'form-control'}),
            'text': forms.Textarea(attrs={'class': 'form-control', 'rows': 6}),
            'metadata': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.add_input(Submit('submit', 'Save'))
        self.helper.layout = Layout(
            Row(
                Column('framework', css_class='col-md-6'),
                Column('clause_code', css_class='col-md-6'),
            ),
            'text',
            'metadata',
        )


class ComplianceMappingForm(forms.ModelForm):
    class Meta:
        model = ComplianceMapping
        fields = ['test_name', 'metric_name', 'clause', 'rationale', 'evidence_rule']
        widgets = {
            'test_name': forms.TextInput(attrs={'class': 'form-control'}),
            'metric_name': forms.TextInput(attrs={'class': 'form-control'}),
            'clause': forms.Select(attrs={'class': 'form-select'}),
            'rationale': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'evidence_rule': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.add_input(Submit('submit', 'Save'))
        self.helper.layout = Layout(
            Row(
                Column('test_name', css_class='col-md-6'),
                Column('metric_name', css_class='col-md-6'),
            ),
            'clause',
            'rationale',
            'evidence_rule',
        )


class ConnectorConfigForm(forms.ModelForm):
    class Meta:
        model = ConnectorConfig
        fields = ['connector_type', 'name', 'config', 'is_active']
        widgets = {
            'connector_type': forms.Select(attrs={'class': 'form-select'}),
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'config': forms.Textarea(attrs={'class': 'form-control', 'rows': 6}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.add_input(Submit('submit', 'Save'))
        self.helper.layout = Layout(
            Row(
                Column('connector_type', css_class='col-md-6'),
                Column('name', css_class='col-md-6'),
            ),
            'config',
            'is_active',
        )


class WebhookSubscriptionForm(forms.ModelForm):
    class Meta:
        model = WebhookSubscription
        fields = ['url', 'events', 'secret', 'is_active']
        widgets = {
            'url': forms.URLInput(attrs={'class': 'form-control'}),
            'events': forms.CheckboxSelectMultiple(attrs={'class': 'form-check-input'}),
            'secret': forms.TextInput(attrs={'class': 'form-control'}),
            'is_active': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.add_input(Submit('submit', 'Save'))
        self.helper.layout = Layout(
            'url',
            'events',
            Row(
                Column('secret', css_class='col-md-6'),
                Column('is_active', css_class='col-md-6'),
            ),
        )


class TestResultForm(forms.ModelForm):
    class Meta:
        model = TestResult
        fields = [
            'test_run', 'test_name', 'summary', 'passed',
            'contains_pii', 'data_classification', 'encryption_key_id'
        ]
        widgets = {
            'test_run': forms.Select(attrs={'class': 'form-select'}),
            'test_name': forms.TextInput(attrs={'class': 'form-control'}),
            'summary': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'passed': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'contains_pii': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'data_classification': forms.Select(attrs={'class': 'form-select'}),
            'encryption_key_id': forms.TextInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.add_input(Submit('submit', 'Save'))
        self.helper.layout = Layout(
            Row(
                Column('test_run', css_class='col-md-6'),
                Column('test_name', css_class='col-md-6'),
            ),
            'summary',
            Row(
                Column('passed', css_class='col-md-4'),
                Column('contains_pii', css_class='col-md-4'),
                Column('data_classification', css_class='col-md-4'),
            ),
            'encryption_key_id',
        )


class MetricForm(forms.ModelForm):
    class Meta:
        model = Metric
        fields = [
            'test_result', 'name', 'value', 'threshold', 'passed',
            'slice_key', 'slice_value', 'extra'
        ]
        widgets = {
            'test_result': forms.Select(attrs={'class': 'form-select'}),
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'value': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'threshold': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01'}),
            'passed': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'slice_key': forms.TextInput(attrs={'class': 'form-control'}),
            'slice_value': forms.TextInput(attrs={'class': 'form-control'}),
            'extra': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.add_input(Submit('submit', 'Save'))
        self.helper.layout = Layout(
            'test_result',
            Row(
                Column('name', css_class='col-md-6'),
                Column('value', css_class='col-md-3'),
                Column('threshold', css_class='col-md-3'),
            ),
            Row(
                Column('passed', css_class='col-md-4'),
                Column('slice_key', css_class='col-md-4'),
                Column('slice_value', css_class='col-md-4'),
            ),
            'extra',
        )


class EvidenceArtifactForm(forms.ModelForm):
    class Meta:
        model = EvidenceArtifact
        fields = [
            'test_run', 'artifact_type', 'file_path', 'file_info',
            'contains_pii', 'data_classification', 'encryption_key_id', 'retention_date'
        ]
        widgets = {
            'test_run': forms.Select(attrs={'class': 'form-select'}),
            'artifact_type': forms.Select(attrs={'class': 'form-select'}),
            'file_path': forms.TextInput(attrs={'class': 'form-control'}),
            'file_info': forms.Textarea(attrs={'class': 'form-control', 'rows': 3}),
            'contains_pii': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'data_classification': forms.Select(attrs={'class': 'form-select'}),
            'encryption_key_id': forms.TextInput(attrs={'class': 'form-control'}),
            'retention_date': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.add_input(Submit('submit', 'Save'))
        self.helper.layout = Layout(
            Row(
                Column('test_run', css_class='col-md-6'),
                Column('artifact_type', css_class='col-md-6'),
            ),
            'file_path',
            'file_info',
            Div(
                Row(
                    Column('contains_pii', css_class='col-md-3'),
                    Column('data_classification', css_class='col-md-3'),
                    Column('encryption_key_id', css_class='col-md-3'),
                    Column('retention_date', css_class='col-md-3'),
                ),
                css_class='border-top pt-3 mt-3'
            ),
        )


class ModelRiskAssessmentForm(forms.ModelForm):
    class Meta:
        model = ModelRiskAssessment
        fields = [
            'model_asset', 'risk_level', 'assessor', 'approval_status',
            'approver', 'approval_date', 'approval_notes', 'risk_factors', 'mitigation_measures',
            'compliance_requirements', 'evidence_documents', 'production_approved',
            'deployment_conditions', 'review_frequency_months'
        ]
        widgets = {
            'model_asset': forms.Select(attrs={'class': 'form-select'}),
            'risk_level': forms.Select(attrs={'class': 'form-select'}),
            'assessor': forms.Select(attrs={'class': 'form-select'}),
            'approval_status': forms.Select(attrs={'class': 'form-select'}),
            'approver': forms.Select(attrs={'class': 'form-select'}),
            'approval_date': forms.DateTimeInput(attrs={'class': 'form-control', 'type': 'datetime-local'}),
            'approval_notes': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'risk_factors': forms.Textarea(attrs={'class': 'form-control', 'rows': 6}),
            'mitigation_measures': forms.Textarea(attrs={'class': 'form-control', 'rows': 6}),
            'compliance_requirements': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'evidence_documents': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'production_approved': forms.CheckboxInput(attrs={'class': 'form-check-input'}),
            'deployment_conditions': forms.Textarea(attrs={'class': 'form-control', 'rows': 4}),
            'review_frequency_months': forms.NumberInput(attrs={'class': 'form-control'}),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.form_method = 'post'
        self.helper.add_input(Submit('submit', 'Save Risk Assessment'))
        self.helper.layout = Layout(
            Row(
                Column('model_asset', css_class='col-md-6'),
                Column('risk_level', css_class='col-md-6'),
            ),
            Row(
                Column('assessor', css_class='col-md-6'),
                Column('approval_status', css_class='col-md-6'),
            ),
            Row(
                Column('approver', css_class='col-md-6'),
                Column('approval_date', css_class='col-md-6'),
            ),
            Row(
                Column('review_frequency_months', css_class='col-md-6'),
            ),
            'approval_notes',
            Div(
                'risk_factors',
                css_class='border-top pt-3 mt-3'
            ),
            Div(
                'mitigation_measures',
                css_class='border-top pt-3 mt-3'
            ),
            Div(
                'compliance_requirements',
                css_class='border-top pt-3 mt-3'
            ),
            Div(
                'evidence_documents',
                css_class='border-top pt-3 mt-3'
            ),
            Div(
                Row(
                    Column('production_approved', css_class='col-md-6'),
                ),
                css_class='border-top pt-3 mt-3'
            ),
            Div(
                'deployment_conditions',
                css_class='border-top pt-3 mt-3'
            ),
        )
