# apps/risk/models.py
from django.db import models
from core.models.abstract_models import OrganizationOwnedModel, AuditableModel
from django.urls import reverse
from django_ckeditor_5.fields import CKEditor5Field
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator
from django.core.exceptions import ValidationError
from django.utils.functional import cached_property
from .risk_register import RiskRegister
from .risk_matrix import RiskMatrixConfig
from common.constants import RISK_CATEGORY_CHOICES
from .choices import (
    RISK_RESPONSE_CHOICES, CONTROL_STATUS_CHOICES, CONTROL_RATING_CHOICES, ACTION_PLAN_STATUS_CHOICES, STATUS_CHOICES
)
from .objective import Objective

class Risk(OrganizationOwnedModel, AuditableModel):
    """Model for managing risks according to ISO 31000 and COSO ERM frameworks."""
    risk_register = models.ForeignKey(
        'RiskRegister',
        on_delete=models.CASCADE,
        related_name='risks',
        verbose_name="Risk Register",
        default=1
    )
    code = models.CharField(max_length=16, db_index=True, verbose_name="Risk Code", default="UNKNOWN")
    risk_name = models.CharField(max_length=512, db_index=True, verbose_name="Risk Name", default="Unnamed Risk")
    external_context = CKEditor5Field('External Context', config_name='extends', blank=True, null=True)
    internal_context = CKEditor5Field('Internal Context', config_name='extends', blank=True, null=True)
    risk_description = CKEditor5Field('Description', config_name='extends', blank=True, null=True)
    date_identified = models.DateField(default=timezone.now, verbose_name="Date Identified")
    identified_by = models.CharField(max_length=100, blank=True, null=True, verbose_name="Identified By")
    risk_owner = models.CharField(max_length=70, db_index=True, verbose_name="Risk Owner", default="Unassigned")
    department = models.CharField(max_length=100, blank=True, null=True, db_index=True, verbose_name="Department")
    category = models.CharField(max_length=20, choices=RISK_CATEGORY_CHOICES, default='other', db_index=True, verbose_name="Risk Category")
    inherent_impact_score = models.IntegerField(default=3, validators=[MinValueValidator(1), MaxValueValidator(5)], verbose_name="Inherent Impact Score")
    inherent_likelihood_score = models.IntegerField(default=3, validators=[MinValueValidator(1), MaxValueValidator(5)], verbose_name="Inherent Likelihood Score")
    inherent_risk_score = models.IntegerField(editable=False, verbose_name="Inherent Risk Score", default=1)
    residual_impact_score = models.IntegerField(default=3, validators=[MinValueValidator(1), MaxValueValidator(5)], verbose_name="Residual Impact Score")
    residual_likelihood_score = models.IntegerField(default=3, validators=[MinValueValidator(1), MaxValueValidator(5)], verbose_name="Residual Likelihood Score")
    residual_risk_score = models.IntegerField(editable=False, verbose_name="Residual Risk Score", default=1)
    risk_response_strategy = models.CharField(max_length=20, choices=RISK_RESPONSE_CHOICES, default='mitigate', verbose_name="Risk Response Strategy")
    risk_appetite = models.IntegerField(default=15, verbose_name="Risk Appetite")
    controls_description = CKEditor5Field('Controls', config_name='extends', blank=True, null=True)
    control_status = models.CharField(max_length=20, choices=CONTROL_STATUS_CHOICES, default='not-implemented', verbose_name="Control Status")
    control_rating = models.CharField(max_length=20, choices=CONTROL_RATING_CHOICES, default='not-assessed', verbose_name="Control Rating")
    control_owner = models.CharField(max_length=70, blank=True, null=True, verbose_name="Control Owner")
    control_last_review_date = models.DateField(null=True, blank=True, verbose_name="Last Control Review Date")
    control_next_review_date = models.DateField(null=True, blank=True, verbose_name="Next Control Review Date")
    action_plan = CKEditor5Field('Action Plan', config_name='extends', blank=True, null=True)
    action_plan_status = models.CharField(max_length=20, choices=ACTION_PLAN_STATUS_CHOICES, default='not-started', verbose_name="Action Plan Status")
    action_owner = models.CharField(max_length=70, blank=True, null=True, verbose_name="Action Owner")
    action_due_date = models.DateField(null=True, blank=True, verbose_name="Action Due Date")
    kri_description = CKEditor5Field('KRI Description', config_name='extends', blank=True, null=True)
    kri_threshold = models.IntegerField(default=70, verbose_name="KRI Threshold")
    next_review_date = models.DateField(null=True, blank=True, verbose_name="Next Review Date")
    last_reviewed_date = models.DateField(null=True, blank=True, verbose_name="Last Reviewed Date")
    last_reviewed_by = models.CharField(max_length=70, blank=True, null=True, verbose_name="Last Reviewed By")
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='open', db_index=True, verbose_name="Risk Status")
    closure_date = models.DateField(null=True, blank=True, verbose_name="Closure Date")
    closure_justification = CKEditor5Field('Closure Justification', config_name='extends', blank=True, null=True)
    additional_notes = CKEditor5Field('Additional Notes', config_name='extends', blank=True, null=True)
    objectives = models.ManyToManyField(Objective, related_name='risks', blank=True)

    class Meta:
        verbose_name = "Risk"
        verbose_name_plural = "Risks"
        ordering = ['-updated_at', 'risk_name']
        indexes = [
            models.Index(fields=['organization']),
            models.Index(fields=['risk_register']),
            models.Index(fields=['code']),
            models.Index(fields=['risk_name']),
            models.Index(fields=['category']),
            models.Index(fields=['status']),
            models.Index(fields=['risk_owner']),
            models.Index(fields=['date_identified']),
        ]

    def save(self, *args, **kwargs):
        self.inherent_risk_score = self.calculate_inherent_risk()
        self.residual_risk_score = self.calculate_residual_risk()
        self.check_action_due()
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.code}: {self.risk_name} ({self.get_category_display()})"

    def get_absolute_url(self):
        return reverse('risk_detail', args=[str(self.id)])

    def clean(self):
        if self.date_identified and self.date_identified > timezone.now().date():
            raise ValidationError('Date identified cannot be in the future.')
        # Dynamic validation based on active matrix configuration
        matrix_config = self.get_matrix_config
        errors = {}
        if matrix_config:
            # Respect model-level 1..5 caps, but further restrict to matrix levels when lower
            max_impact = min(matrix_config.impact_levels, 5)
            max_likelihood = min(matrix_config.likelihood_levels, 5)

            # Validate inherent scores
            if not (1 <= self.inherent_impact_score <= max_impact):
                errors['inherent_impact_score'] = (
                    f"Impact score must be between 1 and {max_impact} for the current matrix"
                )
            if not (1 <= self.inherent_likelihood_score <= max_likelihood):
                errors['inherent_likelihood_score'] = (
                    f"Likelihood score must be between 1 and {max_likelihood} for the current matrix"
                )

            # Validate residual scores
            if not (1 <= self.residual_impact_score <= max_impact):
                errors['residual_impact_score'] = (
                    f"Impact score must be between 1 and {max_impact} for the current matrix"
                )
            if not (1 <= self.residual_likelihood_score <= max_likelihood):
                errors['residual_likelihood_score'] = (
                    f"Likelihood score must be between 1 and {max_likelihood} for the current matrix"
                )

            # Validate risk appetite within matrix threshold ceiling if provided
            if self.risk_appetite is not None:
                if self.risk_appetite < 1 or self.risk_appetite > matrix_config.very_high_threshold:
                    errors['risk_appetite'] = (
                        f"Risk appetite must be between 1 and {matrix_config.very_high_threshold}"
                    )

        if errors:
            raise ValidationError(errors)

    def check_action_due(self):
        if (self.action_due_date and self.action_due_date < timezone.now().date() and self.action_plan_status != 'completed'):
            self.action_plan_status = 'overdue'

    def calculate_inherent_risk(self):
        return self.inherent_impact_score * self.inherent_likelihood_score

    def calculate_residual_risk(self):
        return self.residual_impact_score * self.residual_likelihood_score

    def get_risk_level(self):
        risk_score = self.residual_risk_score
        matrix_config = self.get_matrix_config
        return matrix_config.get_risk_level(risk_score) if matrix_config else None

    @cached_property
    def get_matrix_config(self):
        return RiskMatrixConfig.objects.filter(organization=self.organization, is_active=True).first()

    def is_within_appetite(self):
        return self.residual_risk_score <= self.risk_appetite

    def get_current_kri_value(self):
        latest_kri = self.kris.order_by('-timestamp').first()
        return latest_kri.value if latest_kri else 0

    def is_kri_violated(self):
        current_value = self.get_current_kri_value()
        if current_value > self.kri_threshold:
            self.send_kri_alert()
            return True
        return False

    def send_kri_alert(self):
        pass

    def get_control_effectiveness(self):
        if self.inherent_risk_score == 0:
            return 0
        reduction = self.inherent_risk_score - self.residual_risk_score
        effectiveness = (reduction / self.inherent_risk_score) * 100
        return round(effectiveness, 2)
