from django.contrib import admin
import reversion.admin
from .models import DocumentRequest, Document

@admin.register(DocumentRequest)
class DocumentRequestAdmin(reversion.admin.VersionAdmin):
    list_display = ("request_name", "organization", "status", "due_date", "request_owner", "requestee", "date_of_request")
    list_filter = ("organization", "status", "due_date")
    search_fields = ("request_name", "request_owner__username", "requestee__username", "requestee_email", "requestee_identifier")
    date_hierarchy = "due_date"

@admin.register(Document)
class DocumentAdmin(reversion.admin.VersionAdmin):
    list_display = ("document_request", "organization", "uploaded_by", "uploaded_at")
    list_filter = ("organization", "uploaded_by", "uploaded_at")
    search_fields = ("document_request__request_name", "uploaded_by__username")
    date_hierarchy = "uploaded_at"
