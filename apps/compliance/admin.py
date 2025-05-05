# Placeholder for compliance admin

from django.contrib import admin
import reversion.admin
from .models import (
    ComplianceFramework,
    PolicyDocument,
    DocumentProcessing,
    ComplianceRequirement,
    ComplianceObligation,
    ComplianceEvidence,
)

@admin.register(ComplianceFramework)
class ComplianceFrameworkAdmin(reversion.admin.VersionAdmin):
    list_display = ("name", "version", "regulatory_body")
    search_fields = ("name", "regulatory_body")
    list_filter = ("regulatory_body",)

@admin.register(PolicyDocument)
class PolicyDocumentAdmin(reversion.admin.VersionAdmin):
    list_display = ("title", "version", "effective_date", "expiration_date", "owner", "owner_email", "is_anonymized")
    search_fields = ("title", "owner__email", "owner_email")
    list_filter = ("is_anonymized", "effective_date")
    date_hierarchy = "effective_date"

@admin.register(DocumentProcessing)
class DocumentProcessingAdmin(reversion.admin.VersionAdmin):
    list_display = ("document", "status", "ai_model_version", "completed_at", "confidence_score")
    search_fields = ("document__title", "ai_model_version")
    list_filter = ("status",)
    date_hierarchy = "completed_at"

@admin.register(ComplianceRequirement)
class ComplianceRequirementAdmin(reversion.admin.VersionAdmin):
    list_display = ("requirement_id", "title", "regulatory_framework", "policy_document", "jurisdiction", "mandatory")
    search_fields = ("requirement_id", "title", "jurisdiction", "tags")
    list_filter = ("mandatory", "regulatory_framework")

@admin.register(ComplianceObligation)
class ComplianceObligationAdmin(reversion.admin.VersionAdmin):
    list_display = ("obligation_id", "requirement", "owner", "owner_email", "priority", "status", "due_date", "completion_date", "is_active")
    search_fields = ("obligation_id", "requirement__title", "owner__email", "owner_email")
    list_filter = ("status", "priority", "is_active")
    date_hierarchy = "due_date"

@admin.register(ComplianceEvidence)
class ComplianceEvidenceAdmin(reversion.admin.VersionAdmin):
    list_display = ("obligation", "document", "validity_start", "validity_end")
    search_fields = ("obligation__obligation_id", "document__title")
    list_filter = ("validity_start", "validity_end")
    date_hierarchy = "validity_start"
