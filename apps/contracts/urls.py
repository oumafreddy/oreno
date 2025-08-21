from django.urls import path
from rest_framework.routers import DefaultRouter
from django.views.generic import TemplateView
from . import views
from .views import ContractsReportsView
from rest_framework import viewsets
from users.permissions import IsOrgAdmin, IsOrgManagerOrReadOnly, IsOrgStaffOrReadOnly
from .models import ContractType, Party, Contract, ContractParty, ContractMilestone
from .serializers import ContractTypeSerializer, PartySerializer, ContractSerializer, ContractPartySerializer, ContractMilestoneSerializer
from core.mixins.organization import OrganizationScopedQuerysetMixin

app_name = 'contracts'

# Basic URL patterns for contracts app
urlpatterns = [
    path('', views.ContractsDashboardView.as_view(), name='dashboard'),
    path('reports/', ContractsReportsView.as_view(), name='reports'),

    # ContractType
    path('contracttypes/', views.ContractTypeListView.as_view(), name='contracttype-list'),
    path('contracttypes/add/', views.ContractTypeCreateView.as_view(), name='contracttype-add'),
    path('contracttypes/<int:pk>/', views.ContractTypeDetailView.as_view(), name='contracttype-detail'),
    path('contracttypes/<int:pk>/edit/', views.ContractTypeUpdateView.as_view(), name='contracttype-edit'),
    path('contracttypes/<int:pk>/delete/', views.ContractTypeDeleteView.as_view(), name='contracttype-delete'),

    # Party
    path('parties/', views.PartyListView.as_view(), name='party-list'),
    path('parties/add/', views.PartyCreateView.as_view(), name='party-add'),
    path('parties/<int:pk>/', views.PartyDetailView.as_view(), name='party-detail'),
    path('parties/<int:pk>/edit/', views.PartyUpdateView.as_view(), name='party-edit'),
    path('parties/<int:pk>/delete/', views.PartyDeleteView.as_view(), name='party-delete'),

    # Contract
    path('contracts/', views.ContractListView.as_view(), name='contract-list'),
    path('contracts/add/', views.ContractCreateView.as_view(), name='contract-add'),
    path('contracts/<int:pk>/', views.ContractDetailView.as_view(), name='contract-detail'),
    path('contracts/<int:pk>/edit/', views.ContractUpdateView.as_view(), name='contract-edit'),
    path('contracts/<int:pk>/delete/', views.ContractDeleteView.as_view(), name='contract-delete'),

    # ContractParty
    path('contractparties/', views.ContractPartyListView.as_view(), name='contractparty-list'),
    path('contractparties/add/', views.ContractPartyCreateView.as_view(), name='contractparty-add'),
    path('contractparties/<int:pk>/', views.ContractPartyDetailView.as_view(), name='contractparty-detail'),
    path('contractparties/<int:pk>/edit/', views.ContractPartyUpdateView.as_view(), name='contractparty-edit'),
    path('contractparties/<int:pk>/delete/', views.ContractPartyDeleteView.as_view(), name='contractparty-delete'),

    # ContractMilestone
    path('milestones/', views.ContractMilestoneListView.as_view(), name='contractmilestone-list'),
    path('milestones/add/', views.ContractMilestoneCreateView.as_view(), name='contractmilestone-add'),
    path('milestones/<int:pk>/', views.ContractMilestoneDetailView.as_view(), name='contractmilestone-detail'),
    path('milestones/<int:pk>/edit/', views.ContractMilestoneUpdateView.as_view(), name='contractmilestone-edit'),
    path('milestones/<int:pk>/delete/', views.ContractMilestoneDeleteView.as_view(), name='contractmilestone-delete'),

    path('api/status-data/', views.api_status_data, name='api_status_data'),
    path('api/type-data/', views.api_type_data, name='api_type_data'),
    path('api/party-data/', views.api_party_data, name='api_party_data'),
    path('api/milestone-type-data/', views.api_milestone_type_data, name='api_milestone_type_data'),
    path('api/milestone-status-data/', views.api_milestone_status_data, name='api_milestone_status_data'),
    path('api/expiry-data/', views.api_expiry_data, name='api_expiry_data'),
]

# API router for contracts endpoints
router = DefaultRouter()

# API ViewSets
class ContractTypeViewSet(OrganizationScopedQuerysetMixin, viewsets.ModelViewSet):
    queryset = ContractType.objects.all()
    serializer_class = ContractTypeSerializer
    permission_classes = [IsOrgAdmin]

class PartyViewSet(viewsets.ModelViewSet):
    queryset = Party.objects.all()
    serializer_class = PartySerializer
    permission_classes = [IsOrgStaffOrReadOnly]
    def get_queryset(self):
        return Party.objects.filter(organization=self.request.organization)

class ContractViewSet(OrganizationScopedQuerysetMixin, viewsets.ModelViewSet):
    queryset = Contract.objects.all()
    serializer_class = ContractSerializer
    permission_classes = [IsOrgManagerOrReadOnly]

class ContractPartyViewSet(OrganizationScopedQuerysetMixin, viewsets.ModelViewSet):
    queryset = ContractParty.objects.all()
    serializer_class = ContractPartySerializer
    permission_classes = [IsOrgManagerOrReadOnly]
    def get_queryset(self):
        return ContractParty.objects.filter(contract__organization=self.request.organization)

class ContractMilestoneViewSet(OrganizationScopedQuerysetMixin, viewsets.ModelViewSet):
    queryset = ContractMilestone.objects.all()
    serializer_class = ContractMilestoneSerializer
    permission_classes = [IsOrgManagerOrReadOnly]
    def get_queryset(self):
        return ContractMilestone.objects.filter(organization=self.request.organization)

# Register your contracts API viewsets here
router.register(r'contracttypes', ContractTypeViewSet, basename='contracttype')
router.register(r'parties', PartyViewSet, basename='party')
router.register(r'contracts', ContractViewSet, basename='contract')
router.register(r'contractparties', ContractPartyViewSet, basename='contractparty')
router.register(r'milestones', ContractMilestoneViewSet, basename='contractmilestone')

# Include API URLs
urlpatterns += router.urls
