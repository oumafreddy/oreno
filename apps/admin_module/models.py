# apps/admin_module/models.py
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.contrib.auth import get_user_model
from core.models.abstract_models import TimeStampedModel

User = get_user_model()

class DataExportLog(TimeStampedModel):
    """
    Model to track data export activities for audit and compliance purposes.
    """
    EXPORT_FORMAT_CHOICES = [
        ('excel', _('Excel (.xlsx)')),
        ('csv', _('CSV')),
        ('json', _('JSON')),
        ('pdf', _('PDF')),
    ]
    
    EXPORT_TYPE_CHOICES = [
        ('full_organization', _('Full Organization Data')),
        ('audit_data', _('Audit Data Only')),
        ('risk_data', _('Risk Data Only')),
        ('compliance_data', _('Compliance Data Only')),
        ('contracts_data', _('Contracts Data Only')),
        ('legal_data', _('Legal Data Only')),
        ('document_data', _('Document Management Data Only')),
        ('user_data', _('User Data Only')),
        ('custom', _('Custom Selection')),
    ]
    
    STATUS_CHOICES = [
        ('pending', _('Pending')),
        ('processing', _('Processing')),
        ('completed', _('Completed')),
        ('failed', _('Failed')),
        ('cancelled', _('Cancelled')),
    ]
    
    # Basic information
    requested_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='data_exports',
        verbose_name=_("Requested By"),
        help_text=_("User who requested the data export")
    )
    organization = models.ForeignKey(
        'organizations.Organization',
        on_delete=models.CASCADE,
        related_name='data_exports',
        verbose_name=_("Organization"),
        help_text=_("Organization whose data was exported")
    )
    
    # Export details
    export_type = models.CharField(
        max_length=50,
        choices=EXPORT_TYPE_CHOICES,
        verbose_name=_("Export Type"),
        help_text=_("Type of data exported")
    )
    export_format = models.CharField(
        max_length=10,
        choices=EXPORT_FORMAT_CHOICES,
        default='excel',
        verbose_name=_("Export Format"),
        help_text=_("Format of the exported file")
    )
    
    # File information
    file_path = models.CharField(
        max_length=500,
        blank=True,
        null=True,
        verbose_name=_("File Path"),
        help_text=_("Path to the exported file")
    )
    file_size_bytes = models.BigIntegerField(
        null=True,
        blank=True,
        verbose_name=_("File Size (bytes)"),
        help_text=_("Size of the exported file in bytes")
    )
    file_size_mb = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True,
        verbose_name=_("File Size (MB)"),
        help_text=_("Size of the exported file in MB")
    )
    
    # Data statistics
    records_exported = models.PositiveIntegerField(
        default=0,
        verbose_name=_("Records Exported"),
        help_text=_("Number of records exported")
    )
    tables_exported = models.PositiveIntegerField(
        default=0,
        verbose_name=_("Tables Exported"),
        help_text=_("Number of database tables exported")
    )
    
    # Status and timing
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='pending',
        verbose_name=_("Status"),
        help_text=_("Current status of the export")
    )
    started_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_("Started At"),
        help_text=_("When the export process started")
    )
    completed_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_("Completed At"),
        help_text=_("When the export process completed")
    )
    processing_time_seconds = models.PositiveIntegerField(
        null=True,
        blank=True,
        verbose_name=_("Processing Time (seconds)"),
        help_text=_("Time taken to process the export in seconds")
    )
    
    # Security and audit
    ip_address = models.GenericIPAddressField(
        verbose_name=_("IP Address"),
        help_text=_("IP address of the user who requested the export")
    )
    user_agent = models.TextField(
        blank=True,
        verbose_name=_("User Agent"),
        help_text=_("Browser/user agent information")
    )
    session_id = models.CharField(
        max_length=100,
        blank=True,
        verbose_name=_("Session ID"),
        help_text=_("User session ID during export")
    )
    
    # Additional details
    custom_selection = models.JSONField(
        default=dict,
        blank=True,
        verbose_name=_("Custom Selection"),
        help_text=_("Details of custom data selection if applicable")
    )
    error_message = models.TextField(
        blank=True,
        verbose_name=_("Error Message"),
        help_text=_("Error message if export failed")
    )
    notes = models.TextField(
        blank=True,
        verbose_name=_("Notes"),
        help_text=_("Additional notes about the export")
    )
    
    # Data retention
    file_expires_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_("File Expires At"),
        help_text=_("When the exported file will be automatically deleted")
    )
    is_deleted = models.BooleanField(
        default=False,
        verbose_name=_("Is Deleted"),
        help_text=_("Whether the exported file has been deleted")
    )
    
    class Meta:
        verbose_name = _("Data Export Log")
        verbose_name_plural = _("Data Export Logs")
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['requested_by', 'created_at']),
            models.Index(fields=['organization', 'created_at']),
            models.Index(fields=['export_type', 'status']),
            models.Index(fields=['status', 'created_at']),
            models.Index(fields=['file_expires_at']),
        ]
    
    def __str__(self):
        return f"Data Export by {self.requested_by.email} - {self.export_type} ({self.status})"
    
    def save(self, *args, **kwargs):
        # Calculate file size in MB if file_size_bytes is provided
        if self.file_size_bytes and not self.file_size_mb:
            self.file_size_mb = self.file_size_bytes / (1024 * 1024)
        
        # Calculate processing time if both timestamps are available
        if self.started_at and self.completed_at and not self.processing_time_seconds:
            self.processing_time_seconds = int((self.completed_at - self.started_at).total_seconds())
        
        super().save(*args, **kwargs)
    
    @property
    def is_expired(self):
        """Check if the exported file has expired."""
        from django.utils import timezone
        return self.file_expires_at and self.file_expires_at < timezone.now()
    
    @property
    def download_url(self):
        """Get the download URL for the exported file."""
        if self.file_path and not self.is_deleted and not self.is_expired:
            return f"/admin/data-export/download/{self.id}/"
        return None
    
    def mark_as_processing(self):
        """Mark the export as processing."""
        from django.utils import timezone
        self.status = 'processing'
        self.started_at = timezone.now()
        self.save(update_fields=['status', 'started_at'])
    
    def mark_as_completed(self, file_path, file_size_bytes, records_exported, tables_exported):
        """Mark the export as completed."""
        from django.utils import timezone
        from datetime import timedelta
        
        self.status = 'completed'
        self.completed_at = timezone.now()
        self.file_path = file_path
        self.file_size_bytes = file_size_bytes
        self.records_exported = records_exported
        self.tables_exported = tables_exported
        # Set file expiration to 7 days from now
        self.file_expires_at = timezone.now() + timedelta(days=7)
        self.save()
    
    def mark_as_failed(self, error_message):
        """Mark the export as failed."""
        from django.utils import timezone
        self.status = 'failed'
        self.completed_at = timezone.now()
        self.error_message = error_message
        self.save(update_fields=['status', 'completed_at', 'error_message'])
    
    def get_file_size_display(self):
        """Get human-readable file size."""
        if not self.file_size_bytes:
            return "Unknown"
        
        size_bytes = self.file_size_bytes
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.1f} TB"
    
    def get_processing_time_display(self):
        """Get human-readable processing time."""
        if not self.processing_time_seconds:
            return "Unknown"
        
        seconds = self.processing_time_seconds
        if seconds < 60:
            return f"{seconds} seconds"
        elif seconds < 3600:
            minutes = seconds // 60
            remaining_seconds = seconds % 60
            return f"{minutes}m {remaining_seconds}s"
        else:
            hours = seconds // 3600
            remaining_minutes = (seconds % 3600) // 60
            return f"{hours}h {remaining_minutes}m"
