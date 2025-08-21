# apps/admin_module/admin.py
from django.contrib import admin
from django.utils.translation import gettext_lazy as _
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from django.contrib.admin import SimpleListFilter
from reversion.admin import VersionAdmin

from .models import DataExportLog

class ExportStatusFilter(SimpleListFilter):
    """Custom filter for export status."""
    title = _('Export Status')
    parameter_name = 'export_status'

    def lookups(self, request, model_admin):
        return (
            ('completed', _('Completed')),
            ('pending', _('Pending')),
            ('processing', _('Processing')),
            ('failed', _('Failed')),
            ('cancelled', _('Cancelled')),
        )

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(status=self.value())

class ExportTypeFilter(SimpleListFilter):
    """Custom filter for export type."""
    title = _('Export Type')
    parameter_name = 'export_type'

    def lookups(self, request, model_admin):
        return (
            ('full_organization', _('Full Organization')),
            ('audit_data', _('Audit Data')),
            ('risk_data', _('Risk Data')),
            ('compliance_data', _('Compliance Data')),
            ('contracts_data', _('Contracts Data')),
            ('legal_data', _('Legal Data')),
            ('document_data', _('Document Data')),
            ('user_data', _('User Data')),
            ('custom', _('Custom Selection')),
        )

    def queryset(self, request, queryset):
        if self.value():
            return queryset.filter(export_type=self.value())

@admin.register(DataExportLog)
class DataExportLogAdmin(VersionAdmin):
    """
    Admin interface for data export logs with comprehensive audit information.
    """
    list_display = (
        'id', 'requested_by', 'organization', 'export_type', 'export_format',
        'status', 'records_exported', 'file_size_display', 'processing_time_display',
        'created_at', 'completed_at'
    )
    list_filter = (
        ExportStatusFilter,
        ExportTypeFilter,
        'export_format', 'organization',
        'created_at', 'completed_at'
    )
    search_fields = (
        'requested_by__email', 'requested_by__first_name', 'requested_by__last_name',
        'organization__name', 'organization__code',
        'notes', 'error_message'
    )
    readonly_fields = (
        'requested_by', 'organization', 'export_type', 'export_format',
        'file_path', 'file_size_bytes', 'file_size_mb', 'records_exported',
        'tables_exported', 'status', 'started_at', 'completed_at',
        'processing_time_seconds', 'ip_address', 'user_agent', 'session_id',
        'custom_selection', 'error_message', 'file_expires_at', 'is_deleted',
        'created_at', 'updated_at', 'download_link', 'file_info'
    )
    ordering = ('-created_at',)
    date_hierarchy = 'created_at'
    list_per_page = 25
    
    fieldsets = (
        (_('Basic Information'), {
            'fields': ('requested_by', 'organization', 'export_type', 'export_format', 'notes')
        }),
        (_('Export Details'), {
            'fields': ('status', 'started_at', 'completed_at', 'processing_time_seconds')
        }),
        (_('File Information'), {
            'fields': ('file_path', 'file_size_bytes', 'file_size_mb', 'download_link', 'file_info')
        }),
        (_('Data Statistics'), {
            'fields': ('records_exported', 'tables_exported')
        }),
        (_('Security & Audit'), {
            'fields': ('ip_address', 'user_agent', 'session_id'),
            'classes': ('collapse',)
        }),
        (_('Custom Selection'), {
            'fields': ('custom_selection',),
            'classes': ('collapse',)
        }),
        (_('Error Information'), {
            'fields': ('error_message',),
            'classes': ('collapse',)
        }),
        (_('File Management'), {
            'fields': ('file_expires_at', 'is_deleted'),
            'classes': ('collapse',)
        }),
        (_('Timestamps'), {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if not request.user.is_superuser:
            # Filter by organization for non-superusers
            return qs.filter(organization=request.user.organization)
        return qs
    
    def has_add_permission(self, request):
        """Prevent manual creation of export logs."""
        return False
    
    def has_change_permission(self, request, obj=None):
        """Prevent editing of export logs."""
        return False
    
    def has_delete_permission(self, request, obj=None):
        """Only superusers can delete export logs."""
        return request.user.is_superuser
    
    def download_link(self, obj):
        """Display download link if file is available."""
        if obj.download_url and not obj.is_deleted and not obj.is_expired:
            return format_html(
                '<a href="{}" class="button" target="_blank">Download File</a>',
                obj.download_url
            )
        elif obj.is_expired:
            return format_html('<span style="color: red;">File Expired</span>')
        elif obj.is_deleted:
            return format_html('<span style="color: red;">File Deleted</span>')
        else:
            return format_html('<span style="color: orange;">File Not Available</span>')
    download_link.short_description = _('Download')
    
    def file_info(self, obj):
        """Display comprehensive file information."""
        if not obj.file_path:
            return "No file generated"
        
        info_parts = []
        
        if obj.file_size_bytes:
            info_parts.append(f"Size: {obj.get_file_size_display()}")
        
        if obj.records_exported:
            info_parts.append(f"Records: {obj.records_exported:,}")
        
        if obj.tables_exported:
            info_parts.append(f"Tables: {obj.tables_exported}")
        
        if obj.processing_time_seconds:
            info_parts.append(f"Processing: {obj.get_processing_time_display()}")
        
        if obj.file_expires_at:
            if obj.is_expired:
                info_parts.append("Status: Expired")
            else:
                info_parts.append(f"Expires: {obj.file_expires_at.strftime('%Y-%m-%d %H:%M')}")
        
        return mark_safe('<br>'.join(info_parts))
    file_info.short_description = _('File Information')
    
    def file_size_display(self, obj):
        """Display file size in human-readable format."""
        return obj.get_file_size_display()
    file_size_display.short_description = _('File Size')
    file_size_display.admin_order_field = 'file_size_bytes'
    
    def processing_time_display(self, obj):
        """Display processing time in human-readable format."""
        return obj.get_processing_time_display()
    processing_time_display.short_description = _('Processing Time')
    processing_time_display.admin_order_field = 'processing_time_seconds'
    
    def get_actions(self, request):
        """Custom admin actions."""
        actions = super().get_actions(request)
        
        if request.user.is_superuser:
            actions['cleanup_expired'] = (self.cleanup_expired_action, 'cleanup_expired', self.cleanup_expired_action.short_description)
            actions['delete_selected'] = (self.delete_selected_action, 'delete_selected', self.delete_selected_action.short_description)
        
        return actions
    
    def cleanup_expired_action(self, request, queryset):
        """Admin action to cleanup expired exports."""
        from .tasks import cleanup_expired_exports
        cleanup_expired_exports.delay()
        
        self.message_user(
            request,
            _("Cleanup task has been queued. Expired files will be removed shortly.")
        )
    cleanup_expired_action.short_description = _("Cleanup expired export files")
    
    def delete_selected_action(self, request, queryset):
        """Override delete action to handle file cleanup."""
        from django.core.files.storage import default_storage
        
        deleted_count = 0
        for export in queryset:
            try:
                # Delete file if it exists
                if export.file_path and default_storage.exists(export.file_path):
                    default_storage.delete(export.file_path)
                
                # Mark as deleted
                export.is_deleted = True
                export.save(update_fields=['is_deleted'])
                deleted_count += 1
                
            except Exception as e:
                self.message_user(
                    request,
                    f"Error deleting export {export.id}: {e}",
                    level='ERROR'
                )
        
        self.message_user(
            request,
            _("Successfully deleted {count} export records and their associated files.").format(
                count=deleted_count
            )
        )
    delete_selected_action.short_description = _("Delete selected exports and files")
    
    class Media:
        css = {
            'all': ('admin/css/data_export_admin.css',)
        }
        js = ('admin/js/data_export_admin.js',)

# Create a custom admin site for Data Export Management
class DataExportAdminSite(admin.AdminSite):
    """Custom admin site for Data Export Management."""
    site_header = _('Data Export Management')
    site_title = _('Data Export Management')
    index_title = _('Data Export Management Dashboard')
    
    def get_app_list(self, request):
        """Customize the app list to show Data Export Management prominently."""
        app_list = super().get_app_list(request)
        
        # Find the admin_module app and customize it
        for app in app_list:
            if app['app_label'] == 'admin_module':
                app['name'] = _('Data Export Management')
                app['has_module_perms'] = True
                
                # Customize the models
                for model in app['models']:
                    if model['object_name'] == 'DataExportLog':
                        model['name'] = _('Export Logs')
                        model['verbose_name'] = _('Export Logs')
                        model['verbose_name_plural'] = _('Export Logs')
                        model['admin_url'] = '/admin/admin_module/dataexportlog/'
                        model['add_url'] = None  # Disable add
                        model['view_only'] = True
                
                # Add additional management links
                app['models'].extend([
                    {
                        'name': _('Export Dashboard'),
                        'object_name': 'export_dashboard',
                        'verbose_name': _('Export Dashboard'),
                        'verbose_name_plural': _('Export Dashboard'),
                        'admin_url': '/admin-module/',
                        'add_url': None,
                        'view_only': True,
                        'perms': {'view': True, 'add': False, 'change': False, 'delete': False}
                    },
                    {
                        'name': _('Create Export'),
                        'object_name': 'create_export',
                        'verbose_name': _('Create Export'),
                        'verbose_name_plural': _('Create Export'),
                        'admin_url': '/admin-module/data-export/create/',
                        'add_url': None,
                        'view_only': True,
                        'perms': {'view': True, 'add': False, 'change': False, 'delete': False}
                    },
                    {
                        'name': _('Export Statistics'),
                        'object_name': 'export_statistics',
                        'verbose_name': _('Export Statistics'),
                        'verbose_name_plural': _('Export Statistics'),
                        'admin_url': '/admin-module/data-export/statistics/',
                        'add_url': None,
                        'view_only': True,
                        'perms': {'view': True, 'add': False, 'change': False, 'delete': False}
                    }
                ])
                break
        
        return app_list

# Register the custom admin site
data_export_admin_site = DataExportAdminSite(name='data_export_admin')

# Register models with the custom admin site
data_export_admin_site.register(DataExportLog, DataExportLogAdmin)

# Add custom admin actions
@admin.action(description=_("Export to Excel"))
def export_to_excel(modeladmin, request, queryset):
    """Export selected records to Excel."""
    import io
    import xlsxwriter
    from django.http import HttpResponse
    
    # Create the HttpResponse object with Excel header
    response = HttpResponse(
        content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    )
    response['Content-Disposition'] = 'attachment; filename="data_exports.xlsx"'
    
    # Create Excel file
    output = io.BytesIO()
    workbook = xlsxwriter.Workbook(output)
    worksheet = workbook.add_worksheet()
    
    # Write headers
    headers = ['ID', 'Requested By', 'Organization', 'Export Type', 'Format', 'Status', 'Records', 'File Size', 'Created']
    for col, header in enumerate(headers):
        worksheet.write(0, col, header)
    
    # Write data
    for row, export in enumerate(queryset, 1):
        worksheet.write(row, 0, export.id)
        worksheet.write(row, 1, str(export.requested_by))
        worksheet.write(row, 2, str(export.organization))
        worksheet.write(row, 3, export.get_export_type_display())
        worksheet.write(row, 4, export.get_export_format_display())
        worksheet.write(row, 5, export.get_status_display())
        worksheet.write(row, 6, export.records_exported or 0)
        worksheet.write(row, 7, export.get_file_size_display())
        worksheet.write(row, 8, export.created_at.strftime('%Y-%m-%d %H:%M'))
    
    workbook.close()
    output.seek(0)
    response.write(output.getvalue())
    return response

# Add the custom action to the admin
DataExportLogAdmin.actions = [export_to_excel] + list(DataExportLogAdmin.actions)
