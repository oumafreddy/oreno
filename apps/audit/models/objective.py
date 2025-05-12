from django.db import models
from django.utils.translation import gettext_lazy as _
from core.models.abstract_models import OrganizationOwnedModel, AuditableModel, SoftDeletionModel
from .engagement import Engagement
from django_ckeditor_5.fields import CKEditor5Field
from simple_history.models import HistoricalRecords

class Objective(OrganizationOwnedModel, AuditableModel, SoftDeletionModel):
    engagement = models.ForeignKey(
        Engagement,
        on_delete=models.CASCADE,
        related_name='objectives',
        verbose_name=_('Engagement'),
    )
    title = models.CharField(max_length=255, verbose_name=_('Objective Title'))
    description = CKEditor5Field(_('Objective Description'), config_name='extends', blank=True, null=True)
    order = models.PositiveIntegerField(default=0, verbose_name=_('Order'))
    history = HistoricalRecords()

    class Meta:
        app_label = 'audit'
        verbose_name = _('Objective')
        verbose_name_plural = _('Objectives')
        ordering = ['order', 'id']

    def __str__(self):
        return f"{self.title} (Engagement: {self.engagement})" 