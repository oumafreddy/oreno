from django.db import models
from django.utils.translation import gettext_lazy as _
from django.conf import settings
from simple_history.models import HistoricalRecords
from core.models.abstract_models import OrganizationOwnedModel, AuditableModel, SoftDeletionModel
from .issue import Issue
from core.models.validators import validate_file_extension, validate_file_size

class IssueWorkingPaper(OrganizationOwnedModel, AuditableModel, SoftDeletionModel):
    """
    Stores a file (working paper) related to an Issue. Supports multiple files per issue.
    """
    issue = models.ForeignKey(
        Issue,
        on_delete=models.CASCADE,
        related_name='working_papers',
        verbose_name=_('Issue'),
    )
    file = models.FileField(
        upload_to='working_papers/',
        validators=[validate_file_extension, validate_file_size],
        verbose_name=_('Working Paper File'),
    )
    description = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        verbose_name=_('Description'),
        help_text=_('Optional description for this working paper.'),
    )
    uploaded_at = models.DateTimeField(auto_now_add=True, verbose_name=_('Uploaded At'))
    history = HistoricalRecords()

    class Meta:
        app_label = 'audit'
        verbose_name = _('Issue Working Paper')
        verbose_name_plural = _('Issue Working Papers')
        ordering = ['-uploaded_at']

    def __str__(self):
        return f"{self.issue.issue_title} - {self.file.name}" 