from django.db import models
from core.models.abstract_models import OrganizationOwnedModel, AuditableModel
from django_ckeditor_5.fields import CKEditor5Field
from django.contrib.auth import get_user_model
from organizations.models import Organization


class Objective(OrganizationOwnedModel, AuditableModel):
    """Organizational goal/objective that risks may impact.

    Independent of risk matrix; can be created any time. Only active objectives
    should be available for linking from risk forms.
    """

    STATUS_CHOICES = [
        ("active", "Active"),
        ("inactive", "Inactive"),
        ("retired", "Retired"),
        ("achieved", "Achieved"),
    ]

    code = models.CharField(max_length=32, db_index=True, verbose_name="Objective Code")
    name = models.CharField(max_length=255, db_index=True, verbose_name="Objective Name")
    description = CKEditor5Field('Description', config_name='extends', blank=True, null=True)
    origin_source = models.CharField(
        max_length=255,
        blank=True,
        null=True,
        help_text="Source of the objective (e.g., Strategic Plan, SDGs, internal policy)",
        verbose_name="Origin/Source",
    )
    status = models.CharField(max_length=16, choices=STATUS_CHOICES, default="active", db_index=True)
    is_perpetual = models.BooleanField(default=False, help_text="If true, start/end dates are optional and informational only.")
    start_date = models.DateField(blank=True, null=True)
    end_date = models.DateField(blank=True, null=True)

    # Override inherited relations to avoid reverse name clashes with audit.Objective
    created_by = models.ForeignKey(
        get_user_model(),
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='risk_objective_created',
        verbose_name='created by',
    )
    updated_by = models.ForeignKey(
        get_user_model(),
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='risk_objective_updated',
        verbose_name='updated by',
    )
    organization = models.ForeignKey(
        Organization,
        on_delete=models.CASCADE,
        related_name='risk_objectives',
        verbose_name='organization',
    )

    class Meta:
        verbose_name = "Objective"
        verbose_name_plural = "Objectives"
        ordering = ["name"]
        indexes = [
            models.Index(fields=["organization", "status"]),
            models.Index(fields=["code"]),
            models.Index(fields=["name"]),
        ]

    def __str__(self):
        return f"{self.code}: {self.name}"


