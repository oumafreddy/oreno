from django.db import models
from django.utils.translation import gettext_lazy as _
from django.conf import settings
from core.models.abstract_models import OrganizationOwnedModel, AuditableModel, SoftDeletionModel
from .issue import Issue
from django_ckeditor_5.fields import CKEditor5Field
from simple_history.models import HistoricalRecords

class Recommendation(OrganizationOwnedModel, AuditableModel, SoftDeletionModel):
    issue = models.ForeignKey(
        Issue,
        on_delete=models.CASCADE,
        related_name='recommendations',
        verbose_name=_('Issue'),
    )
    title = models.CharField(max_length=255, verbose_name=_('Recommendation Title'))
    description = CKEditor5Field(_('Recommendation Description'), config_name='extends', blank=True, null=True)
    order = models.PositiveIntegerField(default=0, verbose_name=_('Order'))
    # Add remediation fields
    REMEDIATION_CHOICES = [
        ('open', _('Open')),
        ('management_remediating', _('Management Remediating')),
        ('remediated_awaiting_verification', _('Remediated Awaiting Verification')),
        ('closed', _('Closed')),
    ]
    remediation_status = models.CharField(max_length=56, choices=REMEDIATION_CHOICES, default='open', db_index=True, verbose_name=_('Remediation Status'))
    remediation_deadline_date = models.DateField(blank=True, null=True, verbose_name=_('Remediation Deadline'))
    actual_remediation_date = models.DateField(blank=True, null=True, verbose_name=_('Actual Remediation Date'))
    management_action_plan = CKEditor5Field(_('Management Action Plan'), config_name='extends', blank=True, null=True)
    # Add history tracking
    history = HistoricalRecords()

    class Meta:
        app_label = 'audit'
        verbose_name = _('Recommendation')
        verbose_name_plural = _('Recommendations')
        ordering = ['order', 'id']

    def __str__(self):
        return f"{self.title} (Issue: {self.issue})" 