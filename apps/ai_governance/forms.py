from django import forms

from .models import (
    ModelAsset,
    DatasetAsset,
    TestPlan,
)


class ModelAssetForm(forms.ModelForm):
    class Meta:
        model = ModelAsset
        fields = ['name', 'model_type', 'uri', 'version', 'signature', 'extra']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'model_type': forms.Select(attrs={'class': 'form-select'}),
            'uri': forms.TextInput(attrs={'class': 'form-control'}),
            'version': forms.TextInput(attrs={'class': 'form-control'}),
        }


class DatasetAssetForm(forms.ModelForm):
    class Meta:
        model = DatasetAsset
        fields = ['name', 'role', 'path', 'format', 'schema', 'sensitive_attributes', 'label', 'extra']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'role': forms.Select(attrs={'class': 'form-select'}),
            'path': forms.TextInput(attrs={'class': 'form-control'}),
            'format': forms.TextInput(attrs={'class': 'form-control'}),
            'label': forms.TextInput(attrs={'class': 'form-control'}),
        }


class TestPlanForm(forms.ModelForm):
    class Meta:
        model = TestPlan
        fields = ['name', 'model_type', 'config', 'alert_rules']
        widgets = {
            'name': forms.TextInput(attrs={'class': 'form-control'}),
            'model_type': forms.Select(attrs={'class': 'form-select'}),
        }
