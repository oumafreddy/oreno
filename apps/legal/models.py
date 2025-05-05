from django.db import models
from django.utils import timezone
from django.urls import reverse
from django_ckeditor_5.fields import CKEditor5Field
from core.models.abstract_models import TimeStampedModel, OrganizationOwnedModel, AuditableModel
from users.models import CustomUser
from organizations.models import Organization
from core.models.validators import validate_file_extension, validate_file_size
from django.core.validators import MinValueValidator, MaxValueValidator

class CaseType(OrganizationOwnedModel):
    """Standardized case categories (e.g., employment, contract disputes, regulatory)"""
    name = models.CharField(max_length=150, db_index=True)
    description = CKEditor5Field('Description', config_name='extends', blank=True, null=True)
    default_priority = models.IntegerField(default=3, validators=[MinValueValidator(1), MaxValueValidator(5)])

    class Meta:
        unique_together = ['organization', 'name']
        indexes = [models.Index(fields=['organization'])]

    def __str__(self):
        return f"{self.name} ({self.organization})"

class LegalParty(AuditableModel):
    """Parties involved in legal cases (plaintiffs, defendants, witnesses)"""
    PARTY_TYPES = [
        ('plaintiff', 'Plaintiff'),
        ('defendant', 'Defendant'),
        ('witness', 'Witness'),
        ('third_party', 'Third Party'),
    ]

    name = models.CharField(max_length=255, db_index=True)
    party_type = models.CharField(max_length=20, choices=PARTY_TYPES)
    organization = models.CharField(max_length=255, blank=True, null=True)
    contact_person = models.CharField(max_length=100, blank=True, null=True)
    contact_email = models.EmailField(blank=True, null=True)
    contact_phone = models.CharField(max_length=20, blank=True, null=True)
    address = CKEditor5Field('Address', config_name='extends', blank=True, null=True)

    def __str__(self):
        return f"{self.name} ({self.get_party_type_display()})"

class LegalCase(OrganizationOwnedModel, AuditableModel):
    """Core legal case management model"""
    STATUS_CHOICES = [
        ('intake', 'Intake'),
        ('investigation', 'Investigation'),
        ('litigation', 'Litigation'),
        ('settlement_negotiation', 'Settlement Negotiation'),
        ('closed', 'Closed'),
        ('archived', 'Archived'),
    ]

    PRIORITY_CHOICES = [
        (1, 'Low'),
        (2, 'Medium-Low'),
        (3, 'Medium'),
        (4, 'Medium-High'),
        (5, 'High'),
    ]

    case_type = models.ForeignKey(CaseType, on_delete=models.PROTECT)
    title = models.CharField(max_length=512, db_index=True)
    description = CKEditor5Field('Description', config_name='extends', blank=True, null=True)
    opened_date = models.DateField(db_index=True, default=timezone.now)
    closed_date = models.DateField(db_index=True, null=True, blank=True)
    estimated_resolution_date = models.DateField(db_index=True, null=True, blank=True)
    parties = models.ManyToManyField('LegalParty', through='CaseParty', related_name='legal_cases')
    risk_description = CKEditor5Field('Risk Description', config_name='extends', blank=True, null=True)
    compliance_description = CKEditor5Field('Compliance Description', config_name='extends', blank=True, null=True)
    status = models.CharField(max_length=30, choices=STATUS_CHOICES, default='intake', db_index=True)
    priority = models.IntegerField(default=3, choices=PRIORITY_CHOICES, db_index=True)
    lead_attorney = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True, related_name='lead_cases')
    attorneys = models.ManyToManyField(CustomUser, related_name='assigned_cases', blank=True)
    internal_notes = CKEditor5Field('Internal Notes', config_name='extends', blank=True, null=True)

    class Meta:
        indexes = [
            models.Index(fields=['organization', 'status']),
            models.Index(fields=['opened_date', 'closed_date']),
        ]

    def __str__(self):
        return f"{self.title} ({self.get_status_display()})"

    def get_absolute_url(self):
        return reverse('legal_case_detail', args=[str(self.id)])

    def is_overdue(self):
        return self.estimated_resolution_date and self.estimated_resolution_date < timezone.now().date() and self.status not in ['closed', 'archived']

    def get_active_tasks(self):
        return self.tasks.filter(status__in=['pending', 'in_progress'])

class CaseParty(models.Model):
    """Junction model for legal cases and parties"""
    case = models.ForeignKey(LegalCase, on_delete=models.CASCADE)
    party = models.ForeignKey(LegalParty, on_delete=models.CASCADE)
    role_in_case = models.CharField(max_length=100)

    class Meta:
        unique_together = ('case', 'party')

    def __str__(self):
        return f"{self.party.name} - {self.role_in_case}"

class LegalTask(OrganizationOwnedModel, AuditableModel):
    """Case-related tasks with deadlines"""
    STATUS_CHOICES = [
        ('pending', 'Pending'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('overdue', 'Overdue'),
    ]

    case = models.ForeignKey(LegalCase, on_delete=models.CASCADE, related_name='tasks')
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    due_date = models.DateField(db_index=True)
    completion_date = models.DateField(null=True, blank=True)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    assigned_to = models.ForeignKey(CustomUser, on_delete=models.SET_NULL, null=True)

    class Meta:
        indexes = [
            models.Index(fields=['case', 'status']),
            models.Index(fields=['due_date']),
        ]

    def __str__(self):
        return f"{self.title} ({self.get_status_display()})"

class LegalDocument(OrganizationOwnedModel, AuditableModel):
    """Case-related document management"""
    case = models.ForeignKey(LegalCase, on_delete=models.CASCADE, related_name='documents')
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    file = models.FileField(
        upload_to='legal_documents/',
        validators=[validate_file_extension, validate_file_size]
    )
    version = models.CharField(max_length=50, default='1.0')
    is_confidential = models.BooleanField(default=False)

    class Meta:
        indexes = [
            models.Index(fields=['case', 'is_confidential']),
        ]

    def __str__(self):
        return f"{self.title} (v{self.version})"

class LegalArchive(OrganizationOwnedModel, AuditableModel):
    """Case archiving with retention policies"""
    case = models.OneToOneField(LegalCase, on_delete=models.CASCADE, related_name='archive')
    archive_date = models.DateField(default=timezone.now)
    retention_period_years = models.IntegerField(default=7)
    archive_reason = CKEditor5Field('Reason for Archiving', config_name='extends', blank=True, null=True)
    destruction_date = models.DateField(null=True, blank=True)

    def __str__(self):
        return f"Archived: {self.case.title}" 