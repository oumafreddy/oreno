# apps/organizations/urls.py
from django.urls import path
from . import views

app_name = 'organizations'

urlpatterns = [
    path('', views.OrganizationListView.as_view(), name='organization-list'),
    path('<int:pk>/', views.OrganizationDetailView.as_view(), name='organization-detail'),
    path('create/', views.OrganizationCreateView.as_view(), name='organization-create'),
    path('<int:org_pk>/users/', views.OrganizationUsersListView.as_view(), name='organization-users-list'),
    path('<int:org_pk>/settings/', views.OrganizationSettingsView.as_view(), name='organization-settings'),
    path('edit/<int:pk>/', views.OrganizationUpdateView.as_view(), name='organization-update'),
    path('delete/<int:pk>/', views.OrganizationDeleteView.as_view(), name='organization-delete'),
]