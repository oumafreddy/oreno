from django.urls import path, include
from rest_framework.routers import DefaultRouter
from django.views.generic import TemplateView
from . import views
from .views import ComplianceReportsView
from . import serializers
from rest_framework import viewsets
from users.permissions import IsOrgAdmin, IsOrgManagerOrReadOnly, IsOrgStaffOrReadOnly
from core.mixins.organization import OrganizationScopedQuerysetMixin

app_name = 'compliance'

# --- API ViewSets ---
from .models import (
    ComplianceFramework,
    PolicyDocument,
    DocumentProcessing,
    ComplianceRequirement,
    ComplianceObligation,
    ComplianceEvidence,
)
from .serializers import (
    ComplianceFrameworkSerializer,
    PolicyDocumentSerializer,
    DocumentProcessingSerializer,
    ComplianceRequirementSerializer,
    ComplianceObligationSerializer,
    ComplianceEvidenceSerializer,
)

class ComplianceFrameworkViewSet(OrganizationScopedQuerysetMixin, viewsets.ModelViewSet):
    queryset = ComplianceFramework.objects.all()
    serializer_class = ComplianceFrameworkSerializer
    permission_classes = [IsOrgAdmin]

class PolicyDocumentViewSet(OrganizationScopedQuerysetMixin, viewsets.ModelViewSet):
    queryset = PolicyDocument.objects.all()
    serializer_class = PolicyDocumentSerializer
    permission_classes = [IsOrgManagerOrReadOnly]

class DocumentProcessingViewSet(OrganizationScopedQuerysetMixin, viewsets.ModelViewSet):
    queryset = DocumentProcessing.objects.all()
    serializer_class = DocumentProcessingSerializer
    permission_classes = [IsOrgManagerOrReadOnly]

class ComplianceRequirementViewSet(OrganizationScopedQuerysetMixin, viewsets.ModelViewSet):
    queryset = ComplianceRequirement.objects.all()
    serializer_class = ComplianceRequirementSerializer
    permission_classes = [IsOrgManagerOrReadOnly]

class ComplianceObligationViewSet(OrganizationScopedQuerysetMixin, viewsets.ModelViewSet):
    queryset = ComplianceObligation.objects.all()
    serializer_class = ComplianceObligationSerializer
    permission_classes = [IsOrgManagerOrReadOnly]

class ComplianceEvidenceViewSet(OrganizationScopedQuerysetMixin, viewsets.ModelViewSet):
    queryset = ComplianceEvidence.objects.all()
    serializer_class = ComplianceEvidenceSerializer
    permission_classes = [IsOrgStaffOrReadOnly]

# --- API Router ---
router = DefaultRouter()
router.register(r'frameworks', ComplianceFrameworkViewSet, basename='framework')
router.register(r'policydocuments', PolicyDocumentViewSet, basename='policydocument')
router.register(r'documentprocessings', DocumentProcessingViewSet, basename='documentprocessing')
router.register(r'requirements', ComplianceRequirementViewSet, basename='requirement')
router.register(r'obligations', ComplianceObligationViewSet, basename='obligation')
router.register(r'evidences', ComplianceEvidenceViewSet, basename='evidence')

# --- CRUD URL Patterns ---
urlpatterns = [
    # Dashboard
    path('', views.ComplianceDashboardView.as_view(), name='dashboard'),
    path('reports/', ComplianceReportsView.as_view(), name='reports'),
    # ComplianceFramework
    path('frameworks/', views.ComplianceFrameworkListView.as_view(), name='framework_list'),
    path('frameworks/create/', views.ComplianceFrameworkCreateView.as_view(), name='framework_create'),
    path('frameworks/<int:pk>/', views.ComplianceFrameworkDetailView.as_view(), name='framework_detail'),
    path('frameworks/<int:pk>/update/', views.ComplianceFrameworkUpdateView.as_view(), name='framework_update'),
    path('frameworks/<int:pk>/delete/', views.ComplianceFrameworkDeleteView.as_view(), name='framework_delete'),

    # PolicyDocument
    path('policydocuments/', views.PolicyDocumentListView.as_view(), name='policydocument_list'),
    path('policydocuments/create/', views.PolicyDocumentCreateView.as_view(), name='policydocument_create'),
    path('policydocuments/<int:pk>/', views.PolicyDocumentDetailView.as_view(), name='policydocument_detail'),
    path('policydocuments/<int:pk>/update/', views.PolicyDocumentUpdateView.as_view(), name='policydocument_update'),
    path('policydocuments/<int:pk>/delete/', views.PolicyDocumentDeleteView.as_view(), name='policydocument_delete'),

    # DocumentProcessing
    path('documentprocessings/', views.DocumentProcessingListView.as_view(), name='documentprocessing_list'),
    path('documentprocessings/create/', views.DocumentProcessingCreateView.as_view(), name='documentprocessing_create'),
    path('documentprocessings/<int:pk>/', views.DocumentProcessingDetailView.as_view(), name='documentprocessing_detail'),
    path('documentprocessings/<int:pk>/update/', views.DocumentProcessingUpdateView.as_view(), name='documentprocessing_update'),
    path('documentprocessings/<int:pk>/delete/', views.DocumentProcessingDeleteView.as_view(), name='documentprocessing_delete'),

    # ComplianceRequirement
    path('requirements/', views.ComplianceRequirementListView.as_view(), name='requirement_list'),
    path('requirements/create/', views.ComplianceRequirementCreateView.as_view(), name='requirement_create'),
    path('requirements/<int:pk>/', views.ComplianceRequirementDetailView.as_view(), name='requirement_detail'),
    path('requirements/<int:pk>/update/', views.ComplianceRequirementUpdateView.as_view(), name='requirement_update'),
    path('requirements/<int:pk>/delete/', views.ComplianceRequirementDeleteView.as_view(), name='requirement_delete'),

    # ComplianceObligation
    path('obligations/', views.ComplianceObligationListView.as_view(), name='obligation_list'),
    path('obligations/create/', views.ComplianceObligationCreateView.as_view(), name='obligation_create'),
    path('obligations/<int:pk>/', views.ComplianceObligationDetailView.as_view(), name='obligation_detail'),
    path('obligations/<int:pk>/update/', views.ComplianceObligationUpdateView.as_view(), name='obligation_update'),
    path('obligations/<int:pk>/delete/', views.ComplianceObligationDeleteView.as_view(), name='obligation_delete'),

    # ComplianceEvidence
    path('evidences/', views.ComplianceEvidenceListView.as_view(), name='evidence_list'),
    path('evidences/create/', views.ComplianceEvidenceCreateView.as_view(), name='evidence_create'),
    path('evidences/<int:pk>/', views.ComplianceEvidenceDetailView.as_view(), name='evidence_detail'),
    path('evidences/<int:pk>/update/', views.ComplianceEvidenceUpdateView.as_view(), name='evidence_update'),
    path('evidences/<int:pk>/delete/', views.ComplianceEvidenceDeleteView.as_view(), name='evidence_delete'),

    # API URLs
    path('api/', include(router.urls)),
    path('api/framework-data/', views.api_framework_data, name='api_framework_data'),
    path('api/obligation-data/', views.api_obligation_data, name='api_obligation_data'),
    path('api/policy-expiry-data/', views.api_policy_expiry_data, name='api_policy_expiry_data'),
]
