from django.shortcuts import render, get_object_or_404, redirect
from django.views import View
from django.utils import timezone
from django.contrib import messages
from .models import DocumentRequest, Document
from .forms import DocumentForm, DocumentRequestForm
from django.http import Http404
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
    def get_queryset(self):
        return DocumentRequest.objects.filter(organization=self.request.user.organization)

class DocumentRequestDetailView(OrganizationPermissionMixin, DetailView):
    model = DocumentRequest
    template_name = 'document_management/documentrequest_detail.html'
    context_object_name = 'document_request'
    def get_queryset(self):
        return DocumentRequest.objects.filter(organization=self.request.user.organization)

class DocumentRequestCreateView(OrganizationPermissionMixin, CreateView):
    model = DocumentRequest
    form_class = DocumentRequestForm
    template_name = 'document_management/documentrequest_form.html'
    success_url = reverse_lazy('document_management:documentrequest-list')
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['organization'] = self.request.user.organization
        return kwargs
    def form_valid(self, form):
        form.instance.organization = self.request.user.organization
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
        kwargs['organization'] = self.request.user.organization
        return kwargs
    def get_queryset(self):
        return DocumentRequest.objects.filter(organization=self.request.user.organization)

class DocumentRequestDeleteView(OrganizationPermissionMixin, DeleteView):
    model = DocumentRequest
    template_name = 'document_management/documentrequest_confirm_delete.html'
    success_url = reverse_lazy('document_management:documentrequest-list')
    def get_queryset(self):
        return DocumentRequest.objects.filter(organization=self.request.user.organization)

class DocumentListView(OrganizationPermissionMixin, ListView):
    model = Document
    template_name = 'document_management/document_list.html'
    context_object_name = 'documents'
    def get_queryset(self):
        return Document.objects.filter(organization=self.request.user.organization)

class DocumentDetailView(OrganizationPermissionMixin, DetailView):
    model = Document
    template_name = 'document_management/document_detail.html'
    context_object_name = 'document'
    def get_queryset(self):
        return Document.objects.filter(organization=self.request.user.organization)

class DocumentCreateView(OrganizationPermissionMixin, CreateView):
    model = Document
    form_class = DocumentForm
    template_name = 'document_management/document_form.html'
    success_url = reverse_lazy('document_management:document-list')
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['organization'] = self.request.user.organization
        return kwargs
    def form_valid(self, form):
        form.instance.organization = self.request.user.organization
        form.instance.uploaded_by = self.request.user
        return super().form_valid(form)

class DocumentUpdateView(OrganizationPermissionMixin, UpdateView):
    model = Document
    form_class = DocumentForm
    template_name = 'document_management/document_form.html'
    success_url = reverse_lazy('document_management:document-list')
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['organization'] = self.request.user.organization
        return kwargs
    def get_queryset(self):
        return Document.objects.filter(organization=self.request.user.organization)

class DocumentDeleteView(OrganizationPermissionMixin, DeleteView):
    model = Document
    template_name = 'document_management/document_confirm_delete.html'
    success_url = reverse_lazy('document_management:document-list')
    def get_queryset(self):
        return Document.objects.filter(organization=self.request.user.organization)

class DocumentManagementDashboardView(OrganizationPermissionMixin, ListView):
    template_name = 'document_management/dashboard.html'
    context_object_name = 'dashboard'
    def get_queryset(self):
        return []
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        org = self.request.user.organization
        context['request_count'] = DocumentRequest.objects.filter(organization=org).count()
        context['document_count'] = Document.objects.filter(organization=org).count()
        context['pending_count'] = DocumentRequest.objects.filter(organization=org, status='pending').count()
        context['recent_uploads'] = Document.objects.filter(organization=org).order_by('-uploaded_at')[:5]
        # Analytics: Requests by status
        status_qs = DocumentRequest.objects.filter(organization=org).values('status').annotate(count=Count('id'))
        status_data = {s['status']: s['count'] for s in status_qs}
        context['status_chart'] = json.dumps(status_data)
        # Analytics: Uploads over last 7 days
        today = now().date()
        days = [today - timedelta(days=i) for i in range(6, -1, -1)]
        uploads_qs = Document.objects.filter(organization=org, uploaded_at__date__gte=days[0]).values('uploaded_at__date').annotate(count=Count('id'))
        uploads_map = {str(u['uploaded_at__date']): u['count'] for u in uploads_qs}
        uploads_data = {str(day): uploads_map.get(str(day), 0) for day in days}
        context['uploads_chart'] = json.dumps(uploads_data)
        return context

class DocumentRequestViewSet(OrganizationScopedQuerysetMixin, viewsets.ModelViewSet):
    serializer_class = DocumentRequestSerializer
    permission_classes = [IsOrgManagerOrReadOnly]
    def perform_create(self, serializer):
        serializer.save(organization=self.request.tenant, request_owner=self.request.user)

class DocumentViewSet(OrganizationScopedQuerysetMixin, viewsets.ModelViewSet):
    serializer_class = DocumentSerializer
    permission_classes = [IsOrgManagerOrReadOnly]
    def perform_create(self, serializer):
        serializer.save(organization=self.request.tenant, uploaded_by=self.request.user)
