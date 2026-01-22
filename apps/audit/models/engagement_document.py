# apps/audit/models/engagement_document.py

from django.db import models
from django.utils.translation import gettext_lazy as _
from simple_history.models import HistoricalRecords
from core.models.abstract_models import OrganizationOwnedModel, AuditableModel, SoftDeletionModel
from core.models.validators import validate_engagement_document_extension, validate_file_size, validate_file_virus
from .engagement import Engagement


class EngagementDocument(OrganizationOwnedModel, AuditableModel, SoftDeletionModel):
    """
    Stores documents related to an Engagement (e.g., entry meeting minutes, 
    audit notifications, requirements lists). Supports multiple files per engagement.
    Only allows PDF, DOC, DOCX, XLSX, and PPTX file types.
    """
    engagement = models.ForeignKey(
        Engagement,
        on_delete=models.CASCADE,
        related_name='documents',
        verbose_name=_('Engagement'),
        help_text=_('The engagement this document belongs to'),
    )
    file = models.FileField(
        upload_to='audit/engagement_documents/%Y/%m/',
        validators=[validate_engagement_document_extension, validate_file_size, validate_file_virus],
        verbose_name=_('Document File'),
        help_text=_('Upload a document file (PDF, DOC, DOCX, XLSX, or PPTX only)'),
    )
    description = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        verbose_name=_('Description'),
        help_text=_('Optional description for this document (e.g., "Entry Meeting Minutes", "Audit Notification")'),
    )
    document_type = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        verbose_name=_('Document Type'),
        help_text=_('Type of document (e.g., "Entry Meeting Minutes", "Audit Notification", "Requirements List")'),
    )
    uploaded_at = models.DateTimeField(auto_now_add=True, verbose_name=_('Uploaded At'))
    history = HistoricalRecords()

    class Meta:
        app_label = 'audit'
        verbose_name = _('Engagement Document')
        verbose_name_plural = _('Engagement Documents')
        ordering = ['-uploaded_at']
        indexes = [
            models.Index(fields=['engagement', '-uploaded_at']),
            models.Index(fields=['organization', '-uploaded_at']),
        ]

    def __str__(self):
        return f"{self.engagement.title} - {self.file.name}"

    def get_file_extension(self):
        """Return the file extension in lowercase."""
        import os
        return os.path.splitext(self.file.name)[1][1:].lower() if self.file else None

    def get_file_size_display(self):
        """Return human-readable file size."""
        if not self.file:
            return None
        size = self.file.size
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size < 1024.0:
                return f"{size:.1f} {unit}"
            size /= 1024.0
        return f"{size:.1f} TB"
