# apps/organizations/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_nested import routers

from . import views

app_name = 'organizations'

urlpatterns = [
    # Organization management
    path('', views.OrganizationListView.as_view(), name='list'),
    path('create/', views.OrganizationCreateView.as_view(), name='create'),
    path('<int:pk>/', views.OrganizationDetailView.as_view(), name='detail'),
    path('<int:pk>/update/', views.OrganizationUpdateView.as_view(), name='update'),
    path('<int:pk>/delete/', views.OrganizationDeleteView.as_view(), name='delete'),
    
    # Organization settings
    path('<int:org_pk>/settings/', views.OrganizationSettingsView.as_view(), name='settings'),
    
    # Subscription management
    path('<int:org_pk>/subscription/', views.SubscriptionUpdateView.as_view(), name='subscription'),
    
    # Dashboard
    path('dashboard/', views.OrganizationDashboardView.as_view(), name='dashboard'),
]

# API URLs
router = DefaultRouter()
router.register(r'api/organizations', views.OrganizationViewSet, basename='organization-api')
router.register(r'api/settings', views.OrganizationSettingsViewSet, basename='settings-api')
router.register(r'api/subscriptions', views.SubscriptionViewSet, basename='subscription-api')
router.register(r'api/domains', views.DomainViewSet, basename='domain-api')
router.register(r'api/users', views.OrganizationUserViewSet, basename='user-api')

urlpatterns += router.urls