from django.contrib import admin
import reversion.admin
from .models import ContractType, Party, Contract, ContractParty, ContractMilestone

@admin.register(ContractType)
class ContractTypeAdmin(reversion.admin.VersionAdmin):
    list_display = ("name", "organization", "is_standard_template")
    list_filter = ("organization", "is_standard_template")
    search_fields = ("name",)

@admin.register(Party)
class PartyAdmin(reversion.admin.VersionAdmin):
    list_display = ("name", "party_type", "legal_entity_name", "contact_person", "contact_email")
    list_filter = ("party_type",)
    search_fields = ("name", "legal_entity_name", "contact_person", "contact_email")

@admin.register(Contract)
class ContractAdmin(reversion.admin.VersionAdmin):
    list_display = ("code", "title", "organization", "contract_type", "status", "start_date", "end_date", "value", "currency")
    list_filter = ("organization", "contract_type", "status")
    search_fields = ("code", "title")
    date_hierarchy = "start_date"

@admin.register(ContractParty)
class ContractPartyAdmin(admin.ModelAdmin):
    list_display = ("contract", "party", "is_primary_party", "role_in_contract")
    list_filter = ("is_primary_party", "role_in_contract")
    search_fields = ("contract__code", "party__name", "role_in_contract")

@admin.register(ContractMilestone)
class ContractMilestoneAdmin(reversion.admin.VersionAdmin):
    list_display = ("contract", "title", "milestone_type", "due_date", "is_completed", "organization")
    list_filter = ("organization", "milestone_type", "is_completed")
    search_fields = ("contract__code", "title")
    date_hierarchy = "due_date"
