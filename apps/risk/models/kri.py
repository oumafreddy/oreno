from django.db import models
from core.models.abstract_models import TimeStampedModel
from django_ckeditor_5.fields import CKEditor5Field
from django.utils import timezone
from .risk import Risk

class KRI(TimeStampedModel):
    """Key Risk Indicator model for monitoring risks."""
    risk = models.ForeignKey(Risk, on_delete=models.CASCADE, related_name='kris', verbose_name="Risk")
    name = models.CharField(max_length=255, verbose_name="KRI Name")
    description = CKEditor5Field('Description', config_name='extends', blank=True, null=True)
    value = models.FloatField(verbose_name="Value")
    unit = models.CharField(max_length=50, blank=True, null=True, help_text="Unit of measurement (%, $, count, etc.)", verbose_name="Unit")
    timestamp = models.DateTimeField(default=timezone.now, verbose_name="Timestamp")
    threshold_warning = models.FloatField(help_text="Warning level threshold", verbose_name="Warning Threshold")
    threshold_critical = models.FloatField(help_text="Critical level threshold", verbose_name="Critical Threshold")
    DIRECTION_CHOICES = [
        ('increasing', 'Increasing values indicate higher risk'),
        ('decreasing', 'Decreasing values indicate higher risk'),
    ]
    direction = models.CharField(max_length=20, choices=DIRECTION_CHOICES, default='increasing', verbose_name="Direction")
    data_source = models.CharField(max_length=255, blank=True, null=True, help_text="Source of the KRI data", verbose_name="Data Source")
    collection_frequency = models.CharField(max_length=50, blank=True, null=True, help_text="How often this KRI is collected", verbose_name="Collection Frequency")

    @property
    def organization(self):
        return self.risk.organization

    class Meta:
        verbose_name = "Key Risk Indicator"
        verbose_name_plural = "Key Risk Indicators"
        ordering = ['-timestamp']
        indexes = [
            models.Index(fields=['risk']),
            models.Index(fields=['timestamp']),
        ]

    def __str__(self):
        return f"{self.name} for {self.risk.risk_name} - Value: {self.value} {self.unit or ''}"

    def get_status(self):
        if self.direction == 'increasing':
            if self.value >= self.threshold_critical:
                return 'critical'
            elif self.value >= self.threshold_warning:
                return 'warning'
            return 'normal'
        else:
            if self.value <= self.threshold_critical:
                return 'critical'
            elif self.value <= self.threshold_warning:
                return 'warning'
            return 'normal'
