from django.db import models
from core.models.abstract_models import OrganizationOwnedModel, AuditableModel
from django.urls import reverse
from django_ckeditor_5.fields import CKEditor5Field

# IMPORTANT: Ensure a RiskRegister with ID=1 exists for default assignment in Risk model

class RiskRegister(OrganizationOwnedModel, AuditableModel):
    """Container for risks within an organization."""
    code = models.CharField(max_length=16, db_index=True, verbose_name="Register Code", default="UNKNOWN")
    register_name = models.CharField(max_length=255, db_index=True, verbose_name="Register Name")
    register_creation_date = models.DateField(auto_now_add=True, verbose_name="Creation Date")
    register_period = models.CharField(max_length=4, verbose_name="Period")
    register_description = CKEditor5Field('Description', config_name='extends', blank=True, null=True)

    class Meta:
        verbose_name = "Risk Register"
        verbose_name_plural = "Risk Registers"
        ordering = ['-register_creation_date', 'register_name']
        indexes = [
            models.Index(fields=['organization', 'code']),
            models.Index(fields=['register_name']),
            models.Index(fields=['register_period']),
        ]

    def __str__(self):
        return f"{self.register_name} ({self.register_period})"

    def get_absolute_url(self):
        """Return the URL to access a particular risk register instance."""
        return reverse('risk_register_detail', args=[str(self.id)])

    def get_risk_count(self):
        """Return the count of risks in this register."""
        return self.risks.count()
