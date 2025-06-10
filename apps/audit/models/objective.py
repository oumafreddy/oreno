import reversion
from django.db import models
from django.utils.translation import gettext_lazy as _
from django.conf import settings
from django.contrib.contenttypes.fields import GenericRelation
from core.models.abstract_models import OrganizationOwnedModel, AuditableModel, SoftDeletionModel
from .engagement import Engagement
from django_ckeditor_5.fields import CKEditor5Field
from simple_history.models import HistoricalRecords
from django.utils import timezone

@reversion.register()
class Objective(OrganizationOwnedModel, AuditableModel, SoftDeletionModel):
    """
    Audit objective model for GIAS 2024 compliance.
    Links to Engagement and contains Risks.
    """
    engagement = models.ForeignKey(
        Engagement,
        on_delete=models.CASCADE,
        related_name='objectives',
        verbose_name=_('Engagement'),
    )
    title = models.CharField(
        max_length=255, 
        verbose_name=_('Objective Title'),
        help_text=_('Title of the audit objective')
    )
    description = CKEditor5Field(
        _('Objective Description'), 
        config_name='extends', 
        blank=True, 
        null=True,
        help_text=_('Detailed description of the audit objective')
    )
    priority = models.CharField(
        max_length=20,
        choices=[
            ('high', _('High')),
            ('medium', _('Medium')),
            ('low', _('Low')),
        ],
        default='medium',
        verbose_name=_('Priority'),
        help_text=_('Priority level of this objective')
    )
    criteria = CKEditor5Field(
        _('Audit Criteria'), 
        config_name='extends', 
        blank=True, 
        null=True,
        help_text=_('Standards, regulations, or policies that form the basis for evaluation')
    )
    assigned_to = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='objectives_assigned',
        verbose_name=_('Assigned To'),
        help_text=_('Auditor responsible for this objective')
    )
    start_date = models.DateField(
        blank=True,
        null=True,
        verbose_name=_('Start Date'),
        help_text=_('Date when work on this objective started')
    )
    completion_date = models.DateField(
        blank=True,
        null=True,
        verbose_name=_('Completion Date'),
        help_text=_('Date when this objective was completed')
    )
    STATUS_CHOICES = [
        ('not_started', _('Not Started')),
        ('in_progress', _('In Progress')),
        ('completed', _('Completed')),
        ('deferred', _('Deferred')),
    ]
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='not_started',
        verbose_name=_('Status'),
        help_text=_('Current status of this objective')
    )
    estimated_hours = models.PositiveIntegerField(
        default=0,
        verbose_name=_('Estimated Hours'),
        help_text=_('Estimated hours to complete this objective')
    )
    order = models.PositiveIntegerField(
        default=0, 
        verbose_name=_('Order'),
        help_text=_('Display order within the engagement')
    )
    
    # Approvals for this objective
    approvals = GenericRelation(
        'audit.Approval',
        content_type_field='content_type',
        object_id_field='object_id',
        related_query_name='objective',
        related_name='approvals',
    )
    history = HistoricalRecords()

    class Meta:
        app_label = 'audit'
        verbose_name = _('Objective')
        verbose_name_plural = _('Objectives')
        ordering = ['order', 'id']

    def __str__(self):
        return f"{self.title} (Engagement: {self.engagement})"
        
    def save(self, *args, **kwargs):
        # Set start_date if status changes to in_progress
        if self.status == 'in_progress' and not self.start_date:
            self.start_date = timezone.now().date()
            
        # Set completion_date if status changes to completed
        if self.status == 'completed' and not self.completion_date:
            self.completion_date = timezone.now().date()
            
        with reversion.create_revision():
            if hasattr(self, 'last_modified_by') and self.last_modified_by:
                reversion.set_user(self.last_modified_by)
            reversion.set_comment(f"Saved objective '{self.title}'")
            super().save(*args, **kwargs)
            
    @property
    def all_risks(self):
        """Returns all risks linked to this objective."""
        return self.risks.all()
        
    @property
    def all_procedures(self):
        """Returns all procedures linked to this objective via risks."""
        Procedure = self._meta.apps.get_model('audit', 'Procedure')
        return Procedure.objects.filter(risk__objective=self)
        
    @property
    def all_issues(self):
        """Returns all issues linked to this objective via risks > procedures."""
        Issue = self._meta.apps.get_model('audit', 'Issue')
        return Issue.objects.filter(procedure__risk__objective=self)