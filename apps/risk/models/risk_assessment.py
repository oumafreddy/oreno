from django.db import models
from core.models.abstract_models import OrganizationOwnedModel, AuditableModel
from django_ckeditor_5.fields import CKEditor5Field
from django.utils import timezone
from .risk import Risk
from django.core.validators import MinValueValidator, MaxValueValidator

class RiskAssessment(AuditableModel, OrganizationOwnedModel):
    """Model for tracking risk assessments over time."""
    risk = models.ForeignKey(Risk, on_delete=models.CASCADE, related_name='assessments', verbose_name="Risk")
    assessment_date = models.DateField(default=timezone.now, verbose_name="Assessment Date")
    assessor = models.CharField(max_length=100, verbose_name="Assessor")
    impact_score = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)], verbose_name="Impact Score")
    likelihood_score = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)], verbose_name="Likelihood Score")
    risk_score = models.IntegerField(editable=False, verbose_name="Risk Score")
    ASSESSMENT_TYPE_CHOICES = [
        ('inherent', 'Inherent Risk (before controls)'),
        ('residual', 'Residual Risk (after controls)'),
        ('target', 'Target Risk (desired state)'),
    ]
    assessment_type = models.CharField(max_length=20, choices=ASSESSMENT_TYPE_CHOICES, verbose_name="Assessment Type")
    notes = CKEditor5Field('Assessment Notes', config_name='extends', blank=True, null=True)

    class Meta:
        verbose_name = "Risk Assessment"
        verbose_name_plural = "Risk Assessments"
        ordering = ['-assessment_date']
        indexes = [
            models.Index(fields=['risk']),
            models.Index(fields=['assessment_date']),
            models.Index(fields=['assessment_type']),
        ]

    def save(self, *args, **kwargs):
        self.risk_score = self.impact_score * self.likelihood_score
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.get_assessment_type_display()} Assessment for {self.risk.risk_name} on {self.assessment_date}"

    def get_absolute_url(self):
        return reverse('risk_assessment_detail', args=[str(self.id)])
