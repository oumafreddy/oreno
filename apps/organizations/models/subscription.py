# apps/organizations/models/subscription.py

from django.db import models
from django.urls import reverse
from django.utils.translation import gettext_lazy as _
from apps.core.models.abstract_models import OrganizationOwnedModel, AuditableModel
from django_ckeditor_5.fields import CKEditor5Field

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
    
    # Subscription status choices
    STATUS_ACTIVE = 'active'
    STATUS_CANCELLED = 'cancelled'
    STATUS_PAUSED = 'paused'
    STATUS_CHOICES = [
        (STATUS_ACTIVE, _('Active')),
        (STATUS_CANCELLED, _('Cancelled')),
        (STATUS_PAUSED, _('Paused')),
    ]
    
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
    start_date = models.DateField(
        verbose_name=_("Subscription Start Date"),
        help_text=_("The date when the subscription starts.")
    )
    end_date = models.DateField(
        verbose_name=_("Subscription End Date"),
        help_text=_("The date when the subscription ends. Leave blank for ongoing subscriptions."),
        null=True,
        blank=True
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default=STATUS_ACTIVE,
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
        verbose_name=_("Billing Cycle"),
        help_text=_("Billing cycle period, e.g., monthly or yearly.")
    )
    last_payment_date = models.DateField(
        verbose_name=_("Last Payment Date"),
        null=True,
        blank=True,
        help_text=_("The date of the last successful payment.")
    )
    next_payment_date = models.DateField(
        verbose_name=_("Next Payment Date"),
        null=True,
        blank=True,
        help_text=_("The date for the upcoming scheduled payment.")
    )
    
    class Meta:
        verbose_name = _("Subscription")
        verbose_name_plural = _("Subscriptions")
        ordering = ['-start_date']
        indexes = [
            models.Index(fields=['subscription_plan']),
            models.Index(fields=['status']),
        ]
    
    def __str__(self):
        return f"{self.organization} - {self.subscription_plan} ({self.status})"
    
    def get_absolute_url(self):
        """
        Returns the canonical URL to access subscription details.
        """
        return reverse('organizations:subscription_detail', args=[str(self.organization.id)])
    
    def is_active(self):
        """
        Utility method to determine if the subscription is currently active.
        
        Returns:
            True if the status is active and either the end date is not set or it is in the future;
            otherwise, returns False.
        """
        from datetime import date
        today = date.today()
        if self.status != self.STATUS_ACTIVE:
            return False
        if self.end_date and self.end_date < today:
            return False
        return True
    
    def renew_subscription(self, new_end_date):
        """
        Renews the subscription by updating the end date.
        
        Args:
            new_end_date (date): The new end date for the subscription.
        """
        self.end_date = new_end_date
        self.save(update_fields=['end_date'])
