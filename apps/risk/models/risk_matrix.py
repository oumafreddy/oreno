from django.db import models
from core.models.abstract_models import OrganizationOwnedModel, AuditableModel
from django.core.validators import MinValueValidator, MaxValueValidator

class RiskMatrixConfig(OrganizationOwnedModel, AuditableModel):
    """Configuration for risk scoring matrix."""
    name = models.CharField(max_length=100, default="Default Risk Matrix", verbose_name="Matrix Name")
    description = models.TextField(blank=True, null=True, verbose_name="Description")
    impact_levels = models.IntegerField(default=5, validators=[MinValueValidator(1), MaxValueValidator(10)], help_text="Number of impact levels (e.g., 5)", verbose_name="Impact Levels")
    likelihood_levels = models.IntegerField(default=5, validators=[MinValueValidator(1), MaxValueValidator(10)], help_text="Number of likelihood levels (e.g., 5)", verbose_name="Likelihood Levels")
    low_threshold = models.IntegerField(default=5, help_text="Maximum score for low risk", verbose_name="Low Risk Threshold")
    medium_threshold = models.IntegerField(default=10, help_text="Maximum score for medium risk", verbose_name="Medium Risk Threshold")
    high_threshold = models.IntegerField(default=15, help_text="Maximum score for high risk", verbose_name="High Risk Threshold")
    very_high_threshold = models.IntegerField(default=20, help_text="Maximum score for very high risk", verbose_name="Very High Risk Threshold")
    low_color = models.CharField(max_length=7, default="#00FF00", help_text="Color code for low risk (e.g., #00FF00)", verbose_name="Low Risk Color")
    medium_color = models.CharField(max_length=7, default="#FFFF00", help_text="Color code for medium risk (e.g., #FFFF00)", verbose_name="Medium Risk Color")
    high_color = models.CharField(max_length=7, default="#FFA500", help_text="Color code for high risk (e.g., #FFA500)", verbose_name="High Risk Color")
    very_high_color = models.CharField(max_length=7, default="#FF0000", help_text="Color code for very high risk (e.g., #FF0000)", verbose_name="Very High Risk Color")
    critical_color = models.CharField(max_length=7, default="#800000", help_text="Color code for critical risk (e.g., #800000)", verbose_name="Critical Risk Color")
    is_active = models.BooleanField(default=True, verbose_name="Active Matrix")

    class Meta:
        verbose_name = "Risk Matrix Configuration"
        verbose_name_plural = "Risk Matrix Configurations"
        indexes = [
            models.Index(fields=['organization', 'is_active']),
        ]

    def __str__(self):
        return f"{self.name} for {self.organization.name}"

    def get_risk_level(self, risk_score):
        """Determine risk level based on score thresholds."""
        if risk_score <= self.low_threshold:
            return 'low'
        elif risk_score <= self.medium_threshold:
            return 'medium'
        elif risk_score <= self.high_threshold:
            return 'high'
        elif risk_score <= self.very_high_threshold:
            return 'very_high'
        else:
            return 'critical'

    def get_risk_level_color(self, risk_score):
        """Get the color code for a risk score."""
        risk_level = self.get_risk_level(risk_score)
        if risk_level == 'low':
            return self.low_color
        elif risk_level == 'medium':
            return self.medium_color
        elif risk_level == 'high':
            return self.high_color
        elif risk_level == 'very_high':
            return self.very_high_color
        else:
            return self.critical_color

    def save(self, *args, **kwargs):
        # Ensure only one active matrix per organization
        if self.is_active:
            RiskMatrixConfig.objects.filter(
                organization=self.organization, 
                is_active=True
            ).exclude(pk=self.pk).update(is_active=False)
        super().save(*args, **kwargs)
