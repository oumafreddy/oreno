from django.contrib import admin
import reversion.admin
from .models import Risk, RiskRegister, RiskMatrixConfig, Control, RiskControl, KRI, RiskAssessment

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
