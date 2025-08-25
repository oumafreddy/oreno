from django.contrib import admin
import reversion.admin
from .models import (
    Risk, RiskRegister, RiskMatrixConfig, Control, RiskControl, KRI, RiskAssessment,
    # COBIT models
    COBITDomain, COBITProcess, COBITCapability, COBITControl, COBITGovernance,
    # NIST models
    NISTFunction, NISTCategory, NISTSubcategory, NISTImplementation, NISTThreat, NISTIncident
)

@admin.register(Risk)
class RiskAdmin(reversion.admin.VersionAdmin):
    list_display = ("code", "risk_name", "organization", "risk_owner", "category", "status", "date_identified")
    list_filter = ("organization", "category", "status")
    search_fields = ("code", "risk_name", "risk_owner")
    date_hierarchy = "date_identified"

@admin.register(RiskRegister)
class RiskRegisterAdmin(reversion.admin.VersionAdmin):
    list_display = ("code", "register_name", "organization", "register_period", "register_creation_date")
    list_filter = ("organization", "register_period")
    search_fields = ("code", "register_name")
    date_hierarchy = "register_creation_date"

@admin.register(RiskMatrixConfig)
class RiskMatrixConfigAdmin(reversion.admin.VersionAdmin):
    list_display = ("name", "organization", "is_active")
    list_filter = ("organization", "is_active")
    search_fields = ("name",)

@admin.register(Control)
class ControlAdmin(reversion.admin.VersionAdmin):
    list_display = ("code", "name", "organization", "control_owner", "status")
    list_filter = ("organization", "status")
    search_fields = ("code", "name", "control_owner")

@admin.register(RiskControl)
class RiskControlAdmin(admin.ModelAdmin):
    list_display = ("risk", "control", "effectiveness_rating")
    list_filter = ("effectiveness_rating",)
    search_fields = ("risk__code", "control__code")

@admin.register(KRI)
class KRIAdmin(reversion.admin.VersionAdmin):
    list_display = ("name", "risk", "value", "timestamp", "direction")
    list_filter = ("direction",)
    search_fields = ("name", "risk__code")
    date_hierarchy = "timestamp"

@admin.register(RiskAssessment)
class RiskAssessmentAdmin(reversion.admin.VersionAdmin):
    list_display = ("risk", "assessment_date", "assessor", "assessment_type", "impact_score", "likelihood_score", "risk_score")
    list_filter = ("assessment_type",)
    search_fields = ("risk__code", "assessor")
    date_hierarchy = "assessment_date"

# COBIT Admin Classes
@admin.register(COBITDomain)
class COBITDomainAdmin(reversion.admin.VersionAdmin):
    list_display = ("domain_code", "domain_name", "organization")
    list_filter = ("organization", "domain_code")
    search_fields = ("domain_code", "domain_name")
    ordering = ("domain_code",)

@admin.register(COBITProcess)
class COBITProcessAdmin(reversion.admin.VersionAdmin):
    list_display = ("process_code", "process_name", "domain", "organization")
    list_filter = ("organization", "domain")
    search_fields = ("process_code", "process_name")
    ordering = ("process_code",)

@admin.register(COBITCapability)
class COBITCapabilityAdmin(reversion.admin.VersionAdmin):
    list_display = ("process", "current_maturity", "target_maturity", "assessment_date", "assessed_by", "organization")
    list_filter = ("organization", "current_maturity", "target_maturity")
    search_fields = ("process__process_code", "process__process_name")
    date_hierarchy = "assessment_date"

@admin.register(COBITControl)
class COBITControlAdmin(reversion.admin.VersionAdmin):
    list_display = ("control_code", "control_name", "process", "control_type", "implementation_status", "effectiveness_rating", "organization")
    list_filter = ("organization", "control_type", "implementation_status", "effectiveness_rating")
    search_fields = ("control_code", "control_name", "process__process_code")
    ordering = ("control_code",)

@admin.register(COBITGovernance)
class COBITGovernanceAdmin(reversion.admin.VersionAdmin):
    list_display = ("objective_code", "objective_name", "objective_type", "organization")
    list_filter = ("organization", "objective_type")
    search_fields = ("objective_code", "objective_name")
    ordering = ("objective_code",)

# NIST Admin Classes
@admin.register(NISTFunction)
class NISTFunctionAdmin(reversion.admin.VersionAdmin):
    list_display = ("function_code", "function_name", "organization")
    list_filter = ("organization", "function_code")
    search_fields = ("function_code", "function_name")
    ordering = ("function_code",)

@admin.register(NISTCategory)
class NISTCategoryAdmin(reversion.admin.VersionAdmin):
    list_display = ("category_code", "category_name", "function", "organization")
    list_filter = ("organization", "function")
    search_fields = ("category_code", "category_name")
    ordering = ("category_code",)

@admin.register(NISTSubcategory)
class NISTSubcategoryAdmin(reversion.admin.VersionAdmin):
    list_display = ("subcategory_code", "subcategory_name", "category", "organization")
    list_filter = ("organization", "category")
    search_fields = ("subcategory_code", "subcategory_name")
    ordering = ("subcategory_code",)

@admin.register(NISTImplementation)
class NISTImplementationAdmin(reversion.admin.VersionAdmin):
    list_display = ("subcategory", "current_maturity", "target_maturity", "implementation_status", "assessment_date", "assessed_by", "organization")
    list_filter = ("organization", "current_maturity", "target_maturity", "implementation_status")
    search_fields = ("subcategory__subcategory_code", "subcategory__subcategory_name")
    date_hierarchy = "assessment_date"

@admin.register(NISTThreat)
class NISTThreatAdmin(reversion.admin.VersionAdmin):
    list_display = ("threat_name", "threat_type", "severity", "likelihood", "organization")
    list_filter = ("organization", "threat_type", "severity", "likelihood")
    search_fields = ("threat_name",)
    date_hierarchy = "last_updated"

@admin.register(NISTIncident)
class NISTIncidentAdmin(reversion.admin.VersionAdmin):
    list_display = ("incident_id", "title", "incident_type", "severity", "status", "detected_date", "reported_by", "organization")
    list_filter = ("organization", "incident_type", "severity", "status")
    search_fields = ("incident_id", "title", "reported_by__username")
    date_hierarchy = "detected_date"
