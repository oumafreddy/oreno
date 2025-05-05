# apps/organizations/models/subscription.py

from django.db import models
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from core.models.abstract_models import OrganizationOwnedModel, AuditableModel
from django_ckeditor_5.fields import CKEditor5Field
from django.core.validators import MinValueValidator
from django.utils import timezone
from django.contrib.auth import get_user_model

class Subscription(OrganizationOwnedModel, AuditableModel):
    """
    Represents the subscription details for an organization.
    
    This model stores subscription information such as:
        - Subscription plan (e.g., Basic, Premium)
        - Start and (optional) end dates of the subscription
        - Current status (Active, Cancelled, or Paused)
        - Billing cycle (e.g., monthly, yearly)
        - Payment history details for tracking last and upcoming payments
        
    The one-to-one relationship with Organization ensures that each organization has exactly one subscription record.
    """
    
    STATUS_CHOICES = (
        ('active', _('Active')),
        ('cancelled', _('Cancelled')),
        ('paused', _('Paused')),
    )

    BILLING_CYCLE_CHOICES = (
        ('monthly', _('Monthly')),
        ('yearly', _('Yearly')),
    )
    
    # Tie subscription record uniquely to an organization
    organization = models.OneToOneField(
        'organizations.Organization',
        on_delete=models.CASCADE,
        primary_key=True,
        verbose_name=_("Organization"),
        related_name="subscription"
    )
    
    subscription_plan = models.CharField(
        max_length=50,
        verbose_name=_("Subscription Plan"),
        help_text=_("The subscription plan for the organization (e.g., Basic, Premium).")
    )
    start_date = models.DateTimeField(default=timezone.now, verbose_name=_("Subscription Start Date"), help_text=_("The date when the subscription starts."))
    end_date = models.DateTimeField(verbose_name=_("Subscription End Date"), help_text=_("The date when the subscription ends. Leave blank for ongoing subscriptions."))
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='active',
        verbose_name=_("Subscription Status"),
        help_text=_("Current status of the subscription.")
    )
    auto_renew = models.BooleanField(
        default=True,
        verbose_name=_("Auto Renew"),
        help_text=_("Determines if the subscription automatically renews when it expires.")
    )
    billing_cycle = models.CharField(
        max_length=20,
        choices=BILLING_CYCLE_CHOICES,
        default='monthly',
        verbose_name=_("Billing Cycle"),
        help_text=_("Billing cycle period, e.g., monthly or yearly.")
    )
    last_payment_date = models.DateTimeField(
        verbose_name=_("Last Payment Date"),
        null=True,
        blank=True,
        help_text=_("The date of the last successful payment.")
    )
    next_payment_date = models.DateTimeField(
        verbose_name=_("Next Payment Date"),
        null=True,
        blank=True,
        help_text=_("The date for the upcoming scheduled payment.")
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(
        get_user_model(),
        on_delete=models.SET_NULL,
        null=True,
        related_name='subscriptions_created',
        verbose_name=_("Created By")
    )
    updated_by = models.ForeignKey(
        get_user_model(),
        on_delete=models.SET_NULL,
        null=True,
        related_name='subscriptions_updated',
        verbose_name=_("Updated By")
    )
    
    class Meta:
        verbose_name = _("Subscription")
        verbose_name_plural = _("Subscriptions")
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['subscription_plan']),
            models.Index(fields=['status']),
        ]
        constraints = [
            models.CheckConstraint(
                check=models.Q(organization__isnull=False),
                name='organization_required_subscription'
            )
        ]
    
    def __str__(self):
        return f"{self.organization} - {self.subscription_plan}"
    
    def get_absolute_url(self):
        """
        Returns the canonical URL to access subscription details.
        """
        return reverse('organizations:subscription', args=[str(self.organization.id)])
    
    def is_active(self):
        """
        Utility method to determine if the subscription is currently active.
        
        Returns:
            True if the status is active and either the end date is not set or it is in the future;
            otherwise, returns False.
        """
        return self.status == 'active' and self.end_date > timezone.now()
    
    def renew(self):
        """
        Renews the subscription by updating the end date.
        """
        if self.auto_renew and self.is_active():
            if self.billing_cycle == 'monthly':
                self.end_date = self.end_date + timezone.timedelta(days=30)
            else:
                self.end_date = self.end_date + timezone.timedelta(days=365)
            self.last_payment_date = timezone.now()
            self.next_payment_date = self.end_date
            self.save(update_fields=['end_date', 'last_payment_date', 'next_payment_date'])
            return True
        return False
    
    def cancel(self):
        """
        Cancels the subscription.
        """
        self.status = 'cancelled'
        self.auto_renew = False
        self.save(update_fields=['status', 'auto_renew'])
    
    def pause(self):
        """
        Pauses the subscription.
        """
        self.status = 'paused'
        self.save(update_fields=['status'])
    
    def resume(self):
        """
        Resumes the subscription.
        """
        self.status = 'active'
        self.save(update_fields=['status'])
