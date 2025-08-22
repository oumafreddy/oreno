import os
import logging
import tempfile
import zipfile
from datetime import datetime, timedelta
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth.decorators import login_required
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView, TemplateView
from django.contrib.messages.views import SuccessMessageMixin
from django.contrib import messages
from django.core.exceptions import PermissionDenied
from django.http import HttpResponse, Http404, JsonResponse
from django.urls import reverse_lazy
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.db import transaction
from django.db.models import Q, Count, Sum, Avg
from django.core.paginator import Paginator
from django.conf import settings
from django_tenants.utils import tenant_context
from django.core.files.storage import default_storage
from django.core.files.base import ContentFile
from django.db import models

from core.mixins.organization import OrganizationScopedQuerysetMixin
from core.decorators import skip_org_check

from .models import DataExportLog
from .forms import DataExportForm, DataExportFilterForm
from .tasks import process_data_export

logger = logging.getLogger(__name__)

class AdminRequiredMixin:
    """Mixin to ensure only admin users can access the view."""
    
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            from django.contrib.auth.views import redirect_to_login
            return redirect_to_login(request.get_full_path())
        
        if request.user.role != 'admin':
            raise PermissionDenied(_("Only administrators can access this feature."))
        
        return super().dispatch(request, *args, **kwargs)

class AdminDashboardView(AdminRequiredMixin, TemplateView):
    """
    Main dashboard for Application Administration module.
    """
    template_name = 'admin_module/dashboard.html'
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        organization = user.organization
        
        # Organization information
        context.update({
            'org_name': organization.name,
            'org_code': organization.code,
            'org_status': 'Active' if organization.is_active else 'Inactive',
            'subscription_plan': getattr(organization, 'subscription_plan', 'Standard'),
            'org_logo': getattr(organization, 'logo', None),
        })
        
        # User statistics
        from users.models import CustomUser
        users = CustomUser.objects.filter(organization=organization)
        context.update({
            'user_count': users.count(),
            'active_user_count': users.filter(is_active=True).count(),
            'inactive_user_count': users.filter(is_active=False).count(),
            'admin_count': users.filter(role='admin').count(),
            'recent_users': users.order_by('-date_joined')[:5],
        })
        
        # Role distribution for chart
        role_distribution = users.values('role').annotate(count=Count('id'))
        context['role_distribution'] = {item['role']: item['count'] for item in role_distribution}
        
        # Data export statistics
        exports = DataExportLog.objects.filter(organization=organization)
        context.update({
            'total_exports': exports.count(),
            'recent_exports': exports.order_by('-created_at')[:5],
            'export_stats': {
                'completed': exports.filter(status='completed').count(),
                'pending': exports.filter(status='pending').count(),
                'failed': exports.filter(status='failed').count(),
                'total_size_mb': exports.filter(status='completed').aggregate(
                    total_size=Sum('file_size_mb')
                )['total_size'] or 0,
            }
        })
        
        # Security statistics
        from users.models import SecurityAuditLog, AccountLockout
        security_logs = SecurityAuditLog.objects.filter(organization=organization)
        context.update({
            'security_events_today': security_logs.filter(
                timestamp__date=timezone.now().date()
            ).count(),
            'failed_logins_today': security_logs.filter(
                event_type='login_failed',
                timestamp__date=timezone.now().date()
            ).count(),
            'active_lockouts': AccountLockout.objects.filter(
                user__organization=organization,
                is_active=True
            ).count(),
        })
        
        return context

class DataExportListView(AdminRequiredMixin, ListView):
    """
    List view for data export logs with filtering and pagination.
    """
    model = DataExportLog
    template_name = 'admin_module/data_export_list.html'
    context_object_name = 'exports'
    paginate_by = 20
    
    def get_queryset(self):
        queryset = DataExportLog.objects.filter(
            organization=self.request.user.organization
        ).select_related('requested_by').order_by('-created_at')
        
        # Apply filters
        form = DataExportFilterForm(self.request.GET, organization=self.request.user.organization)
        if form.is_valid():
            status = form.cleaned_data.get('status')
            export_type = form.cleaned_data.get('export_type')
            date_from = form.cleaned_data.get('date_from')
            date_to = form.cleaned_data.get('date_to')
            requested_by = form.cleaned_data.get('requested_by')
            
            if status:
                queryset = queryset.filter(status=status)
            if export_type:
                queryset = queryset.filter(export_type=export_type)
            if date_from:
                queryset = queryset.filter(created_at__date__gte=date_from)
            if date_to:
                queryset = queryset.filter(created_at__date__lte=date_to)
            if requested_by:
                queryset = queryset.filter(requested_by=requested_by)
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['filter_form'] = DataExportFilterForm(
            self.request.GET, 
            organization=self.request.user.organization
        )
        
        # Add statistics
        context['total_exports'] = self.get_queryset().count()
        context['completed_exports'] = self.get_queryset().filter(status='completed').count()
        context['pending_exports'] = self.get_queryset().filter(status='pending').count()
        context['failed_exports'] = self.get_queryset().filter(status='failed').count()
        
        return context

class DataExportCreateView(AdminRequiredMixin, SuccessMessageMixin, CreateView):
    """
    Create view for requesting new data exports.
    """
    model = DataExportLog
    form_class = DataExportForm
    template_name = 'admin_module/data_export_form.html'
    success_url = reverse_lazy('admin_module:export-list')
    success_message = _("Data export request submitted successfully. You will be notified when it's ready.")
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.request.user
        kwargs['organization'] = self.request.user.organization
        return kwargs
    
    def form_valid(self, form):
        # Set additional fields
        form.instance.ip_address = self.get_client_ip()
        form.instance.user_agent = self.request.META.get('HTTP_USER_AGENT', '')
        form.instance.session_id = self.request.session.session_key or ''
        
        response = super().form_valid(form)
        
        # Start the export process asynchronously
        try:
            process_data_export.delay(form.instance.id)
            messages.info(
                self.request,
                _("Your export is being processed. You will receive a notification when it's ready.")
            )
        except Exception as e:
            logger.error(f"Failed to start export process: {e}")
            form.instance.mark_as_failed(str(e))
            messages.error(
                self.request,
                _("Failed to start export process. Please try again.")
            )
        
        return response
    
    def get_client_ip(self):
        x_forwarded_for = self.request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip = x_forwarded_for.split(',')[0]
        else:
            ip = self.request.META.get('REMOTE_ADDR')
        return ip

class DataExportDetailView(AdminRequiredMixin, DetailView):
    """
    Detail view for data export logs.
    """
    model = DataExportLog
    template_name = 'admin_module/data_export_detail.html'
    context_object_name = 'export'
    
    def get_queryset(self):
        return DataExportLog.objects.filter(
            organization=self.request.user.organization
        ).select_related('requested_by')
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        export = self.object
        
        # Add file information
        if export.file_path and not export.is_deleted:
            try:
                if default_storage.exists(export.file_path):
                    context['file_exists'] = True
                    context['download_url'] = export.download_url
                else:
                    context['file_exists'] = False
            except Exception:
                context['file_exists'] = False
        else:
            context['file_exists'] = False
        
        return context

@login_required
def download_export_file(request, export_id):
    """
    Download view for exported files with security checks.
    """
    export = get_object_or_404(
        DataExportLog,
        id=export_id,
        organization=request.user.organization
    )
    
    # Check permissions
    if request.user.role != 'admin' and request.user != export.requested_by:
        raise PermissionDenied(_("You don't have permission to download this file."))
    
    # Check if file exists and is not expired
    if not export.file_path or export.is_deleted or export.is_expired:
        raise Http404(_("File not found or has expired."))
    
    try:
        # Get file from storage
        if default_storage.exists(export.file_path):
            file_obj = default_storage.open(export.file_path, 'rb')
            
            # Create response
            response = HttpResponse(file_obj.read(), content_type='application/octet-stream')
            
            # Set filename
            filename = os.path.basename(export.file_path)
            response['Content-Disposition'] = f'attachment; filename="{filename}"'
            
            # Log download
            logger.info(
                f"Export file downloaded: {export.id} by {request.user.email} "
                f"from IP {request.META.get('REMOTE_ADDR')}"
            )
            
            return response
        else:
            raise Http404(_("File not found."))
            
    except Exception as e:
        logger.error(f"Error downloading export file {export.id}: {e}")
        raise Http404(_("Error accessing file."))

@login_required
def cancel_export(request, export_id):
    """
    Cancel a pending export.
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'Invalid method'}, status=405)
    
    export = get_object_or_404(
        DataExportLog,
        id=export_id,
        organization=request.user.organization,
        status='pending'
    )
    
    # Check permissions
    if request.user.role != 'admin' and request.user != export.requested_by:
        return JsonResponse({'error': 'Permission denied'}, status=403)
    
    try:
        export.status = 'cancelled'
        export.save(update_fields=['status'])
        
        messages.success(request, _("Export cancelled successfully."))
        return JsonResponse({'success': True})
        
    except Exception as e:
        logger.error(f"Error cancelling export {export.id}: {e}")
        return JsonResponse({'error': 'Failed to cancel export'}, status=500)

@login_required
def delete_export(request, export_id):
    """
    Delete an export record and its associated file.
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'Invalid method'}, status=405)
    
    export = get_object_or_404(
        DataExportLog,
        id=export_id,
        organization=request.user.organization
    )
    
    # Check permissions
    if request.user.role != 'admin' and request.user != export.requested_by:
        return JsonResponse({'error': 'Permission denied'}, status=403)
    
    try:
        # Delete file if it exists
        if export.file_path and default_storage.exists(export.file_path):
            default_storage.delete(export.file_path)
        
        # Mark as deleted
        export.is_deleted = True
        export.save(update_fields=['is_deleted'])
        
        messages.success(request, _("Export deleted successfully."))
        return JsonResponse({'success': True})
        
    except Exception as e:
        logger.error(f"Error deleting export {export.id}: {e}")
        return JsonResponse({'error': 'Failed to delete export'}, status=500)

@login_required
def export_statistics(request):
    """
    AJAX view for export statistics.
    """
    if request.method != 'GET':
        return JsonResponse({'error': 'Invalid method'}, status=405)
    
    # Get date range
    days = int(request.GET.get('days', 30))
    end_date = timezone.now()
    start_date = end_date - timedelta(days=days)
    
    # Get statistics
    exports = DataExportLog.objects.filter(
        organization=request.user.organization,
        created_at__range=(start_date, end_date)
    )
    
    stats = {
        'total': exports.count(),
        'completed': exports.filter(status='completed').count(),
        'pending': exports.filter(status='pending').count(),
        'failed': exports.filter(status='failed').count(),
        'cancelled': exports.filter(status='cancelled').count(),
        'total_size_mb': exports.filter(status='completed').aggregate(
            total_size=Sum('file_size_mb')
        )['total_size'] or 0,
        'avg_processing_time': exports.filter(
            status='completed',
            processing_time_seconds__isnull=False
        ).aggregate(
            avg_time=Avg('processing_time_seconds')
        )['avg_time'] or 0,
    }
    
    return JsonResponse(stats)

class DataExportAdminView(AdminRequiredMixin, ListView):
    """
    Admin view for managing data exports with additional controls.
    """
    model = DataExportLog
    template_name = 'admin_module/data_export_list.html'
    context_object_name = 'exports'
    paginate_by = 50
    
    def get_queryset(self):
        queryset = DataExportLog.objects.filter(
            organization=self.request.user.organization
        ).select_related('requested_by').order_by('-created_at')
        
        # Apply filters (same as DataExportListView)
        form = DataExportFilterForm(self.request.GET, organization=self.request.user.organization)
        if form.is_valid():
            status = form.cleaned_data.get('status')
            export_type = form.cleaned_data.get('export_type')
            date_from = form.cleaned_data.get('date_from')
            date_to = form.cleaned_data.get('date_to')
            requested_by = form.cleaned_data.get('requested_by')
            
            if status:
                queryset = queryset.filter(status=status)
            if export_type:
                queryset = queryset.filter(export_type=export_type)
            if date_from:
                queryset = queryset.filter(created_at__date__gte=date_from)
            if date_to:
                queryset = queryset.filter(created_at__date__lte=date_to)
            if requested_by:
                queryset = queryset.filter(requested_by=requested_by)
        
        return queryset
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        
        # Add filter form (required by template)
        context['filter_form'] = DataExportFilterForm(
            self.request.GET, 
            organization=self.request.user.organization
        )
        
        # Add comprehensive statistics
        queryset = self.get_queryset()
        context.update({
            'total_exports': queryset.count(),
            'completed_exports': queryset.filter(status='completed').count(),
            'pending_exports': queryset.filter(status='pending').count(),
            'failed_exports': queryset.filter(status='failed').count(),
            'total_size_mb': queryset.filter(status='completed').aggregate(
                total_size=Sum('file_size_mb')
            )['total_size'] or 0,
            'avg_processing_time': queryset.filter(
                status='completed',
                processing_time_seconds__isnull=False
            ).aggregate(
                avg_time=Avg('processing_time_seconds')
            )['avg_time'] or 0,
            'recent_exports': queryset[:10],
            'export_types': queryset.values('export_type').annotate(
                count=Count('id')
            ).order_by('-count'),
        })
        
        return context

@login_required
def cleanup_expired_exports(request):
    """
    Clean up expired export files.
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'Invalid method'}, status=405)
    
    if request.user.role != 'admin':
        return JsonResponse({'error': 'Permission denied'}, status=403)
    
    try:
        # Find expired exports
        expired_exports = DataExportLog.objects.filter(
            organization=request.user.organization,
            file_expires_at__lt=timezone.now(),
            is_deleted=False
        )
        
        deleted_count = 0
        for export in expired_exports:
            try:
                # Delete file if it exists
                if export.file_path and default_storage.exists(export.file_path):
                    default_storage.delete(export.file_path)
                
                # Mark as deleted
                export.is_deleted = True
                export.save(update_fields=['is_deleted'])
                deleted_count += 1
                
            except Exception as e:
                logger.error(f"Error cleaning up export {export.id}: {e}")
        
        messages.success(
            request, 
            _("Cleanup completed. {count} expired files deleted.").format(count=deleted_count)
        )
        return JsonResponse({'success': True, 'deleted_count': deleted_count})
        
    except Exception as e:
        logger.error(f"Error during cleanup: {e}")
        return JsonResponse({'error': 'Cleanup failed'}, status=500)
