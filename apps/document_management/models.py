from django.db import models
from django_ckeditor_5.fields import CKEditor5Field
from core.utils import send_tenant_email as send_mail
from django.conf import settings
from django.utils import timezone
from django.urls import reverse
from django.contrib.auth import get_user_model
from organizations.models import Organization
from core.models.abstract_models import TimeStampedModel, OrganizationOwnedModel, AuditableModel
from core.models.validators import validate_file_extension, validate_file_size
import secrets
from datetime import timedelta
import uuid

# Document management
class DocumentRequest(OrganizationOwnedModel, AuditableModel):
    """Model for document requests."""
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('submitted', 'Submitted'),
        ('accepted', 'Accepted'),
        ('rejected', 'Rejected')
    ]

    request_name = models.CharField(max_length=255, db_index=True, verbose_name="Request Name")
    status = models.CharField(
        max_length=10, 
        choices=STATUS_CHOICES, 
        default='pending',
        db_index=True,
        verbose_name="Status"
    )
    file = models.FileField(
        upload_to='media/', 
        null=True, 
        blank=True,
        validators=[validate_file_extension, validate_file_size],
        verbose_name="File"
    )
    due_date = models.DateField(verbose_name="Due Date")
    date_of_request = models.DateField(default=timezone.now, verbose_name="Request Date")
    request_owner = models.ForeignKey(
        get_user_model(), 
        related_name='requests_made', 
        on_delete=models.CASCADE,
        verbose_name="Request Owner"
    )
    
    requestee = models.ForeignKey(
        get_user_model(), 
        null=True, 
        blank=True, 
        on_delete=models.SET_NULL,
        related_name='requests_received',
        verbose_name="Requestee"
    )
    requestee_email = models.EmailField(null=True, blank=True, verbose_name="Requestee Email")

    requestee_identifier = models.CharField(
        max_length=255, 
        help_text="Enter details about the requestee (team, department, etc.)",
        verbose_name="Requestee Identifier"
    )
    remarks = models.TextField(blank=True, null=True, verbose_name="Remarks")
    
    upload_token = models.CharField(max_length=64, unique=True, blank=True, null=True, editable=False, db_index=True)
    token_expiry = models.DateTimeField(blank=True, null=True, help_text="When the upload link expires.")
    
    class Meta:
        verbose_name = "Document Request"
        verbose_name_plural = "Document Requests"
        ordering = ['-date_of_request', 'request_name']
        indexes = [
            models.Index(fields=['organization']),
            models.Index(fields=['request_name']),
            models.Index(fields=['status']),
            models.Index(fields=['due_date']),
            models.Index(fields=['request_owner']),
        ]
        app_label = "document_management"
        constraints = [
            models.CheckConstraint(
                check=models.Q(organization__isnull=False),
                name='organization_required_documentrequest'
            )
        ]

    def save(self, *args, **kwargs):
        if not self.upload_token:
            self.upload_token = secrets.token_urlsafe(32)
        if not self.token_expiry:
            self.token_expiry = timezone.now() + timedelta(days=7)  # Default: 7 days expiry
        super().save(*args, **kwargs)

    def get_upload_url(self):
        return settings.SITE_URL + reverse('document_management:public-upload', args=[self.upload_token])

    def send_email_to_requestee(self):
        """Send an email notification to the requestee with upload link."""
        subject = f"New Document Request: {self.request_name}"
        upload_url = self.get_upload_url()
        message = f"""
        Hello,
        
        You have a new document request: {self.request_name}.
        Due date: {self.due_date}
        
        Please use the following link to upload the requested document (no login required):
        {upload_url}
        
        This link will expire on {self.token_expiry.strftime('%Y-%m-%d %H:%M')}.
        
        Thank you,
        {self.request_owner.get_full_name()}
        """
        from_email = settings.DEFAULT_FROM_EMAIL
        recipient_list = [self.requestee_email or (self.requestee.email if self.requestee else None)]
        recipient_list = [e for e in recipient_list if e]
        if recipient_list:
            send_mail(subject, message, from_email, recipient_list)

    def __str__(self):
        return self.request_name
    
    def get_absolute_url(self):
        """Return the URL to access a particular document request instance."""
        return reverse('document_request_detail', args=[str(self.id)])
 

class Document(OrganizationOwnedModel, AuditableModel):
    """Model for documents."""
    document_request = models.ForeignKey(
        DocumentRequest,
        related_name='documents',
        on_delete=models.CASCADE,
        verbose_name="Document Request"
    )
    file = models.FileField(
        upload_to='media/', 
        validators=[validate_file_extension, validate_file_size],
        verbose_name="File"
    )
    uploaded_at = models.DateTimeField(auto_now_add=True, verbose_name="Upload Time")
    uploaded_by = models.ForeignKey(
        get_user_model(), 
        related_name='documents_uploaded', 
        on_delete=models.CASCADE,
        verbose_name="Uploaded By"
    )
    
    class Meta:
        verbose_name = "Document"
        verbose_name_plural = "Documents"
        ordering = ['-uploaded_at']
        indexes = [
            models.Index(fields=['organization']),
            models.Index(fields=['document_request']),
            models.Index(fields=['uploaded_by']),
        ]
        app_label = "document_management"
        constraints = [
            models.CheckConstraint(
                check=models.Q(organization__isnull=False),
                name='organization_required_document'
            )
        ]

    def __str__(self):
        return f'Document for {self.document_request.request_name}'
    
    def get_absolute_url(self):
        """Return the URL to access a particular document instance."""
        return reverse('document_detail', args=[str(self.id)])
