from django import forms
from .models import Issue

class BaseIssueRelatedForm(forms.ModelForm):
    """
    Base form class for forms related to Issues (Recommendations, Retests, FollowUps).
    Handles issue_pk consistently and hides the issue field when issue_pk is provided.
    """
    def __init__(self, *args, **kwargs):
        self.issue_pk = kwargs.pop('issue_pk', None)
        self.organization = kwargs.pop('organization', None)
        super().__init__(*args, **kwargs)
        
        if self.issue_pk and 'issue' in self.fields:
            self.fields['issue'].widget = forms.HiddenInput()
            try:
                self.fields['issue'].initial = Issue.objects.get(
                    pk=self.issue_pk,
                    organization=self.organization
                )
            except Issue.DoesNotExist:
                pass
                
    def clean(self):
        cleaned_data = super().clean()
        if self.issue_pk and 'issue' in cleaned_data:
            try:
                issue = Issue.objects.get(
                    pk=self.issue_pk,
                    organization=self.organization
                )
                cleaned_data['issue'] = issue
            except Issue.DoesNotExist:
                self.add_error('issue', 'Invalid issue selected')
        return cleaned_data 