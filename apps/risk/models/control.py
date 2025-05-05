from django.db import models
from core.models.abstract_models import OrganizationOwnedModel, AuditableModel
from django.urls import reverse
from django_ckeditor_5.fields import CKEditor5Field
from .choices import CONTROL_STATUS_CHOICES, CONTROL_RATING_CHOICES

class Control(AuditableModel, OrganizationOwnedModel):
    """Model for risk controls aligned with COSO's emphasis on control activities."""
    code = models.CharField(max_length=16, db_index=True, verbose_name="Control Code", default="UNKNOWN")
    name = models.CharField(max_length=255, db_index=True, verbose_name="Control Name")
    description = CKEditor5Field('Description', config_name='extends', blank=True, null=True)
    CONTROL_TYPE_CHOICES = [
        ('preventive', 'Preventive'),
        ('detective', 'Detective'),
        ('corrective', 'Corrective'),
        ('directive', 'Directive'),
    ]
    control_type = models.CharField(max_length=20, choices=CONTROL_TYPE_CHOICES, verbose_name="Control Type")
    CONTROL_NATURE_CHOICES = [
        ('manual', 'Manual'),
        ('automated', 'Automated'),
        ('semi-automated', 'Semi-Automated'),
    ]
    control_nature = models.CharField(max_length=20, choices=CONTROL_NATURE_CHOICES, verbose_name="Control Nature")
    CONTROL_FREQUENCY_CHOICES = [
        ('continuous', 'Continuous'),
        ('daily', 'Daily'),
        ('weekly', 'Weekly'),
        ('monthly', 'Monthly'),
        ('quarterly', 'Quarterly'),
        ('annually', 'Annually'),
        ('ad-hoc', 'Ad-hoc'),
    ]
    control_frequency = models.CharField(max_length=20, choices=CONTROL_FREQUENCY_CHOICES, verbose_name="Control Frequency")
    status = models.CharField(max_length=20, choices=CONTROL_STATUS_CHOICES, default='not-implemented', db_index=True, verbose_name="Control Status")
    effectiveness_rating = models.CharField(max_length=20, choices=CONTROL_RATING_CHOICES, default='not-assessed', verbose_name="Effectiveness Rating")
    control_owner = models.CharField(max_length=100, db_index=True, verbose_name="Control Owner")
    owner_department = models.CharField(max_length=100, blank=True, null=True, verbose_name="Owner Department")
    last_review_date = models.DateField(null=True, blank=True, verbose_name="Last Review Date")
    next_review_date = models.DateField(null=True, blank=True, verbose_name="Next Review Date")
    documentation = models.FileField(upload_to='control_docs/', blank=True, null=True, verbose_name="Documentation")
    risks = models.ManyToManyField('Risk', related_name='controls', through='RiskControl')

    class Meta:
        verbose_name = "Control"
        verbose_name_plural = "Controls"
        ordering = ['code']
        indexes = [
            models.Index(fields=['organization']),
            models.Index(fields=['code']),
            models.Index(fields=['control_owner']),
            models.Index(fields=['status']),
        ]

    def __str__(self):
        return f"{self.code}: {self.name}"

    def get_absolute_url(self):
        return reverse('control_detail', args=[str(self.id)])
