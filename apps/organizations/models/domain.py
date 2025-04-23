# apps/organizations/models/domain.py

from django.db import models
from django_tenants.models import DomainMixin
from .organization import Organization

class Domain(DomainMixin):
    """
    Maps a hostname (domain) to a Tenant (Organization).
    Inherits fields:
      - domain             (the hostname, e.g. 'acme.example.com')
      - tenant             (FK to your TENANT_MODEL)
      - is_primary         (whether this is the main domain)
      - auto_create_schema (whether to auto-create schema on save)
    """
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Created At",
        help_text="When this domain record was first created",
        db_index=True
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name="Updated At",
        help_text="When this domain record was last modified",
        db_index=True
    )

    class Meta:
        verbose_name = "Tenant Domain"
        verbose_name_plural = "Tenant Domains"
        # Each (domain, tenant) must be unique
        unique_together = ("domain", "tenant")
        indexes = [
            models.Index(fields=["domain"]),
            models.Index(fields=["tenant"]),
        ]
        ordering = ["domain"]

    def __str__(self):
        primary = " (primary)" if getattr(self, "is_primary", False) else ""
        return f"{self.domain}{primary} → {self.tenant}"
