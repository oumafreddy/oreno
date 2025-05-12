from django.db import models
from django.utils.translation import gettext_lazy as _
from core.models.abstract_models import OrganizationOwnedModel, AuditableModel, SoftDeletionModel
from .objective import Objective
from django_ckeditor_5.fields import CKEditor5Field
from simple_history.models import HistoricalRecords

class Procedure(OrganizationOwnedModel, AuditableModel, SoftDeletionModel):
    objective = models.ForeignKey(
        Objective,
        on_delete=models.CASCADE,
        related_name='procedures',
        verbose_name=_('Objective'),
    )
    title = models.CharField(max_length=255, verbose_name=_('Procedure Title'))
    description = CKEditor5Field(_('Procedure Description'), config_name='extends', blank=True, null=True)
    related_risks = CKEditor5Field(_('Related Risks'), config_name='extends', blank=True, null=True)
    order = models.PositiveIntegerField(default=0, verbose_name=_('Order'))
    history = HistoricalRecords()

    class Meta:
        app_label = 'audit'
        verbose_name = _('Procedure')
        verbose_name_plural = _('Procedures')
        ordering = ['order', 'id']

    def __str__(self):
        return f"{self.title} (Objective: {self.objective})" 