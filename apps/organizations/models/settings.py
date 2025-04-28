# apps/organizations/models/settings.py

from django.db import models
from django.utils.translation import gettext_lazy as _
from core.models.abstract_models import OrganizationOwnedModel, AuditableModel
from django_ckeditor_5.fields import CKEditor5Field

class OrganizationSettings(OrganizationOwnedModel, AuditableModel):
    """
    Stores customizable settings for an organization.
    
    This model contains both predefined configuration options and
    a flexible JSON field (additional_settings) to store further preferences.
    It is implemented with a one-to-one relationship with the Organization model,
    ensuring each organization has a unique set of settings.
    """
    
    # Use OneToOneField to tie settings to the organization uniquely.
    # The primary_key=True ensures that the settings use the Organization's PK.
    organization = models.OneToOneField(
        'organizations.Organization',
        on_delete=models.CASCADE,
        primary_key=True,
        verbose_name=_("Organization"),
        related_name="settings"
    )
    
    subscription_plan = models.CharField(
        max_length=50,
        verbose_name=_("Subscription Plan"),
        help_text=_("Identifier for the subscription plan (e.g., 'basic', 'premium').")
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name=_("Active Status"),
        help_text=_("Indicates if the organization's subscription is active.")
    )
    additional_settings = models.JSONField(
        default=dict,
        blank=True,
        verbose_name=_("Additional Settings"),
        help_text=_("A JSON field to store additional configuration parameters.")
    )
    
    class Meta:
        verbose_name = _("Organization Setting")
        verbose_name_plural = _("Organization Settings")
        ordering = ['organization__name']
        indexes = [
            models.Index(fields=['subscription_plan']),
            models.Index(fields=['is_active']),
        ]
    
    def __str__(self):
        return f"Settings for {self.organization.name}"
    
    def get_setting(self, key, default=None):
        """
        Retrieve a setting value from additional_settings.
        
        Args:
            key (str): The key for the setting.
            default: The value to return if the key is not found.
        
        Returns:
            The value corresponding to the key, or default if not present.
        """
        return self.additional_settings.get(key, default)
    
    def set_setting(self, key, value):
        """
        Update or add a key-value pair in additional_settings.
        
        Args:
            key (str): The setting key.
            value: The setting value.
        
        Returns:
            None. Saves the updated additional_settings dictionary.
        """
        self.additional_settings[key] = value
        self.save(update_fields=["additional_settings"])
