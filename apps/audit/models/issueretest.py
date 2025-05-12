from django.db import models
from django.utils.translation import gettext_lazy as _
from django.conf import settings
from core.models.abstract_models import OrganizationOwnedModel, AuditableModel, SoftDeletionModel
from .recommendation import Recommendation
from django_ckeditor_5.fields import CKEditor5Field
from simple_history.models import HistoricalRecords
from .issue import Issue

class IssueRetest(OrganizationOwnedModel, AuditableModel, SoftDeletionModel):
    RESULT_CHOICES = [
        ('pass', _('Pass')),
        ('fail', _('Fail')),
        ('not_tested', _('Not Tested')),
    ]
    issue = models.ForeignKey(
        Issue,
        on_delete=models.CASCADE,
        related_name='retests',
        verbose_name=_('Issue'),
        null=True,
        blank=True,
    )
    retest_date = models.DateField(verbose_name=_('Retest Date'), null=True, blank=True)
    retested_by = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='issue_retests',
        verbose_name=_('Retested By'),
    )
    result = models.CharField(max_length=12, choices=RESULT_CHOICES, verbose_name=_('Retest Result'), null=True, blank=True)
    notes = CKEditor5Field(_('Retest Notes'), config_name='extends', blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    history = HistoricalRecords()

    class Meta:
        app_label = 'audit'
        verbose_name = _('Issue Retest')
        verbose_name_plural = _('Issue Retests')
        ordering = ['-retest_date', '-created_at']

    def __str__(self):
        return f"{self.recommendation} - {self.get_result_display()} on {self.retest_date}" 