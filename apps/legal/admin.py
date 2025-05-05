from django.contrib import admin
from .models import CaseType, LegalParty, LegalCase, CaseParty, LegalTask, LegalDocument, LegalArchive

@admin.register(CaseType)
class CaseTypeAdmin(admin.ModelAdmin):
    list_display = ('name', 'organization', 'default_priority')
    search_fields = ('name',)
    list_filter = ('organization',)

@admin.register(LegalParty)
class LegalPartyAdmin(admin.ModelAdmin):
    list_display = ('name', 'party_type', 'contact_person', 'contact_email', 'contact_phone')
    search_fields = ('name', 'contact_person', 'contact_email')
    list_filter = ('party_type',)

@admin.register(LegalCase)
class LegalCaseAdmin(admin.ModelAdmin):
    list_display = ('title', 'case_type', 'organization', 'status', 'priority', 'lead_attorney', 'opened_date', 'closed_date')
    search_fields = ('title',)
    list_filter = ('status', 'priority', 'organization', 'case_type')

@admin.register(CaseParty)
class CasePartyAdmin(admin.ModelAdmin):
    list_display = ('case', 'party', 'role_in_case')
    search_fields = ('case__title', 'party__name', 'role_in_case')

@admin.register(LegalTask)
class LegalTaskAdmin(admin.ModelAdmin):
    list_display = ('title', 'case', 'due_date', 'status', 'assigned_to')
    search_fields = ('title', 'case__title', 'assigned_to__email')
    list_filter = ('status', 'due_date')

@admin.register(LegalDocument)
class LegalDocumentAdmin(admin.ModelAdmin):
    list_display = ('title', 'case', 'version', 'is_confidential')
    search_fields = ('title', 'case__title')
    list_filter = ('is_confidential',)

@admin.register(LegalArchive)
class LegalArchiveAdmin(admin.ModelAdmin):
    list_display = ('case', 'archive_date', 'retention_period_years', 'destruction_date')
    search_fields = ('case__title',)
    list_filter = ('archive_date', 'retention_period_years') 