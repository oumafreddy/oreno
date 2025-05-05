from django.db import models
from .choices import CONTROL_RATING_CHOICES

class RiskControl(models.Model):
    """Junction model for the many-to-many relationship between Risk and Control."""
    risk = models.ForeignKey('Risk', on_delete=models.CASCADE, verbose_name="Risk")
    control = models.ForeignKey('Control', on_delete=models.CASCADE, verbose_name="Control")
    notes = models.TextField(blank=True, null=True, verbose_name="Notes")
    effectiveness_rating = models.CharField(max_length=20, choices=CONTROL_RATING_CHOICES, default='not-assessed', verbose_name="Effectiveness Rating")

    class Meta:
        verbose_name = "Risk Control"
        verbose_name_plural = "Risk Controls"
        unique_together = ('risk', 'control')
        indexes = [
            models.Index(fields=['risk']),
            models.Index(fields=['control']),
        ]

    def __str__(self):
        return f"{self.control.code} applied to {self.risk.code}"
