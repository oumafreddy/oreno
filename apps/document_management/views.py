from django.shortcuts import render, get_object_or_404, redirect
from django.views import View
from django.utils import timezone
from django.contrib import messages
from .models import DocumentRequest, Document
from .forms import DocumentForm, DocumentRequestForm, DocumentRequestFilterForm
from django.http import Http404, JsonResponse
from django.views.generic import ListView, DetailView, CreateView, UpdateView, DeleteView
from core.mixins.permissions import OrganizationPermissionMixin
from django.urls import reverse_lazy
from rest_framework import viewsets, permissions
from .serializers import DocumentRequestSerializer, DocumentSerializer
import json
from django.db.models import Count
from django.utils.timezone import now, timedelta
from users.permissions import IsOrgManagerOrReadOnly
from core.mixins.organization import OrganizationScopedQuerysetMixin
from django.db.models import Q
from django.contrib.auth.decorators import login_required

class PublicDocumentUploadView(View):
    template_name = 'document_management/public_upload.html'

    def get(self, request, token):
        doc_request = self.get_valid_request(token)
        if not doc_request:
            return render(request, 'document_management/public_upload_invalid.html')
        form = DocumentForm()
        return render(request, self.template_name, {'form': form, 'doc_request': doc_request})

    def post(self, request, token):
        doc_request = self.get_valid_request(token)
        if not doc_request:
            return render(request, 'document_management/public_upload_invalid.html')
        form = DocumentForm(request.POST, request.FILES)
        if form.is_valid():
            document = form.save(commit=False)
            document.document_request = doc_request
            document.organization = doc_request.organization
            document.uploaded_by = None  # No user, external upload
            document.save()
            doc_request.status = 'submitted'
            doc_request.upload_token = None  # Invalidate token after use
            doc_request.save()
            messages.success(request, 'Document uploaded successfully!')
            return render(request, 'document_management/public_upload_success.html', {'doc_request': doc_request})
        return render(request, self.template_name, {'form': form, 'doc_request': doc_request})

    def get_valid_request(self, token):
        try:
            doc_request = DocumentRequest.objects.get(upload_token=token, status='pending')
            if doc_request.token_expiry and timezone.now() > doc_request.token_expiry:
                return None
            return doc_request
        except DocumentRequest.DoesNotExist:
            return None

class DocumentRequestListView(OrganizationPermissionMixin, ListView):
    model = DocumentRequest
    template_name = 'document_management/documentrequest_list.html'
    context_object_name = 'document_requests'
    paginate_by = 20
    def get_queryset(self):
        qs = super().get_queryset().filter(organization=self.request.organization)
        form = DocumentRequestFilterForm(self.request.GET)
        if form.is_valid():
            q = form.cleaned_data.get('q')
            if q:
                qs = qs.filter(
                    Q(request_name__icontains=q) |
                    Q(requestee__email__icontains=q) |
                    Q(requestee_email__icontains=q) |
                    Q(requestee_identifier__icontains=q)
                )
            status = form.cleaned_data.get('status')
            if status:
                qs = qs.filter(status=status)
        return qs
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['filter_form'] = DocumentRequestFilterForm(self.request.GET)
        return context

class DocumentRequestDetailView(OrganizationPermissionMixin, DetailView):
    model = DocumentRequest
    template_name = 'document_management/documentrequest_detail.html'
    context_object_name = 'document_request'
    def get_queryset(self):
        return super().get_queryset().filter(organization=self.request.organization)

class DocumentRequestCreateView(OrganizationPermissionMixin, CreateView):
    model = DocumentRequest
    form_class = DocumentRequestForm
    template_name = 'document_management/documentrequest_form.html'
    success_url = reverse_lazy('document_management:documentrequest-list')
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['organization'] = self.request.organization
        return kwargs
    def form_valid(self, form):
        form.instance.organization = self.request.organization
        form.instance.request_owner = self.request.user
        response = super().form_valid(form)
        self.object.send_email_to_requestee()
        return response

class DocumentRequestUpdateView(OrganizationPermissionMixin, UpdateView):
    model = DocumentRequest
    form_class = DocumentRequestForm
    template_name = 'document_management/documentrequest_form.html'
    success_url = reverse_lazy('document_management:documentrequest-list')
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['organization'] = self.request.organization
        return kwargs
    def get_queryset(self):
        return super().get_queryset().filter(organization=self.request.organization)

class DocumentRequestDeleteView(OrganizationPermissionMixin, DeleteView):
    model = DocumentRequest
    template_name = 'document_management/documentrequest_confirm_delete.html'
    success_url = reverse_lazy('document_management:documentrequest-list')
    def get_queryset(self):
        return super().get_queryset().filter(organization=self.request.organization)

class DocumentListView(OrganizationPermissionMixin, ListView):
    model = Document
    template_name = 'document_management/document_list.html'
    context_object_name = 'documents'
    def get_queryset(self):
        return super().get_queryset().filter(organization=self.request.organization)

class DocumentDetailView(OrganizationPermissionMixin, DetailView):
    model = Document
    template_name = 'document_management/document_detail.html'
    context_object_name = 'document'
    def get_queryset(self):
        return super().get_queryset().filter(organization=self.request.organization)

class DocumentCreateView(OrganizationPermissionMixin, CreateView):
    model = Document
    form_class = DocumentForm
    template_name = 'document_management/document_form.html'
    success_url = reverse_lazy('document_management:document-list')
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['organization'] = self.request.organization
        return kwargs
    def form_valid(self, form):
        form.instance.organization = self.request.organization
        form.instance.uploaded_by = self.request.user
        return super().form_valid(form)

class DocumentUpdateView(OrganizationPermissionMixin, UpdateView):
    model = Document
    form_class = DocumentForm
    template_name = 'document_management/document_form.html'
    success_url = reverse_lazy('document_management:document-list')
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['organization'] = self.request.organization
        return kwargs
    def get_queryset(self):
        return super().get_queryset().filter(organization=self.request.organization)

class DocumentDeleteView(OrganizationPermissionMixin, DeleteView):
    model = Document
    template_name = 'document_management/document_confirm_delete.html'
    success_url = reverse_lazy('document_management:document-list')
    def get_queryset(self):
        return super().get_queryset().filter(organization=self.request.organization)

class DocumentManagementDashboardView(OrganizationPermissionMixin, ListView):
    template_name = 'document_management/dashboard.html'
    context_object_name = 'dashboard'
    
    def get_queryset(self):
        return []
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        org = self.request.organization
        
        # Basic counts
        context['request_count'] = DocumentRequest.objects.filter(organization=org).count()
        context['document_count'] = Document.objects.filter(organization=org).count()
        context['pending_count'] = DocumentRequest.objects.filter(organization=org, status='pending').count()
        context['recent_uploads'] = Document.objects.filter(organization=org).order_by('-uploaded_at')[:5]
        
        # Analytics: Requests by status
        status_qs = DocumentRequest.objects.filter(organization=org).values('status').annotate(count=Count('id'))
        status_data = {s['status']: s['count'] for s in status_qs}
        # Ensure we have default values for common statuses
        default_statuses = {'pending': 0, 'approved': 0, 'rejected': 0, 'completed': 0}
        for status in default_statuses:
            if status not in status_data:
                status_data[status] = 0
        context['status_chart'] = json.dumps(status_data or default_statuses)
        
        # Analytics: Uploads over last 7 days
        today = now().date()
        days = [today - timedelta(days=i) for i in range(6, -1, -1)]
        uploads_qs = Document.objects.filter(
            organization=org, 
            uploaded_at__date__gte=days[0]
        ).values('uploaded_at__date').annotate(count=Count('id'))
        
        uploads_map = {str(u['uploaded_at__date']): u['count'] for u in uploads_qs}
        uploads_data = {str(day): uploads_map.get(str(day), 0) for day in days}
        context['uploads_chart'] = json.dumps(uploads_data or {str(today): 0})
        
        return context

class DocumentRequestViewSet(OrganizationScopedQuerysetMixin, viewsets.ModelViewSet):
    serializer_class = DocumentRequestSerializer
    permission_classes = [IsOrgManagerOrReadOnly]
    def perform_create(self, serializer):
        serializer.save(organization=self.request.organization, request_owner=self.request.user)

class DocumentViewSet(OrganizationScopedQuerysetMixin, viewsets.ModelViewSet):
    serializer_class = DocumentSerializer
    permission_classes = [IsOrgManagerOrReadOnly]
    def perform_create(self, serializer):
        serializer.save(organization=self.request.organization, uploaded_by=self.request.user)

@login_required
def api_status_data(request):
    org = request.organization
    from .models import DocumentRequest
    from django.db.models import Count
    status_qs = DocumentRequest.objects.filter(organization=org).values('status').annotate(count=Count('id'))
    status_data = {s['status']: s['count'] for s in status_qs}
    return JsonResponse(status_data, safe=False)

@login_required
def api_uploads_data(request):
    org = request.organization
    from .models import Document
    from django.db.models import Count
    from django.utils import timezone
    from datetime import timedelta
    
    # Get uploads for the last 7 days
    today = timezone.now().date()
    days = [today - timedelta(days=i) for i in range(6, -1, -1)]
    uploads_qs = Document.objects.filter(
        organization=org,
        uploaded_at__date__gte=days[0]
    ).values('uploaded_at__date').annotate(count=Count('id'))
    
    # Create a dictionary with all days, defaulting to 0
    uploads_data = {str(day): 0 for day in days}
    # Update with actual counts
    for upload in uploads_qs:
        uploads_data[str(upload['uploaded_at__date'])] = upload['count']
    
    return JsonResponse(uploads_data, safe=False)
