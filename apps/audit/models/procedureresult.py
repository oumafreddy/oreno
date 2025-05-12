from django.db import models
from django.utils.translation import gettext_lazy as _
from core.models.abstract_models import OrganizationOwnedModel, AuditableModel, SoftDeletionModel
from .procedure import Procedure
from django_ckeditor_5.fields import CKEditor5Field
from simple_history.models import HistoricalRecords

class ProcedureResult(OrganizationOwnedModel, AuditableModel, SoftDeletionModel):
    STATUS_CHOICES = [
        ('operating_effectively', _('Operating Effectively')),
        ('not_effective', _('Not Effective')),
        ('for_the_record', _('For the Record')),
    ]
    procedure = models.ForeignKey(
        Procedure,
        on_delete=models.CASCADE,
        related_name='results',
        verbose_name=_('Procedure'),
    )
    status = models.CharField(max_length=32, choices=STATUS_CHOICES, verbose_name=_('Result Status'))
    notes = CKEditor5Field(_('Notes'), config_name='extends', blank=True, null=True)
    is_for_the_record = models.BooleanField(default=False, verbose_name=_('Just for the Record'))
    order = models.PositiveIntegerField(default=0, verbose_name=_('Order'))
    is_positive = models.BooleanField(default=False, verbose_name=_('Positive Result'))
    history = HistoricalRecords()

    class Meta:
        app_label = 'audit'
        verbose_name = _('Procedure Result')
        verbose_name_plural = _('Procedure Results')
        ordering = ['order', 'id']

    def __str__(self):
        return f"{self.procedure} - {self.get_status_display()}" 