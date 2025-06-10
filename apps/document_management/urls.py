from django.urls import path, include
from django.views.generic import TemplateView
from . import views
from rest_framework.routers import DefaultRouter

app_name = 'document_management'

urlpatterns = [
    path('', TemplateView.as_view(template_name='document_management/list.html'), name='list'),
    path('upload/<str:token>/', views.PublicDocumentUploadView.as_view(), name='public-upload'),
    path('requests/', views.DocumentRequestListView.as_view(), name='documentrequest-list'),
    path('requests/add/', views.DocumentRequestCreateView.as_view(), name='documentrequest-add'),
    path('requests/<int:pk>/', views.DocumentRequestDetailView.as_view(), name='documentrequest-detail'),
    path('requests/<int:pk>/edit/', views.DocumentRequestUpdateView.as_view(), name='documentrequest-edit'),
    path('requests/<int:pk>/delete/', views.DocumentRequestDeleteView.as_view(), name='documentrequest-delete'),
    path('documents/', views.DocumentListView.as_view(), name='document-list'),
    path('documents/add/', views.DocumentCreateView.as_view(), name='document-add'),
    path('documents/<int:pk>/', views.DocumentDetailView.as_view(), name='document-detail'),
    path('documents/<int:pk>/edit/', views.DocumentUpdateView.as_view(), name='document-edit'),
    path('documents/<int:pk>/delete/', views.DocumentDeleteView.as_view(), name='document-delete'),
    path('dashboard/', views.DocumentManagementDashboardView.as_view(), name='dashboard'),
]

router = DefaultRouter()
router.register(r'document-requests', views.DocumentRequestViewSet, basename='documentrequest-api')
router.register(r'documents', views.DocumentViewSet, basename='document-api')

urlpatterns += [
    path('api/', include(router.urls)),
    path('api/status-data/', views.api_status_data, name='api_status_data'),
    path('api/uploads-data/', views.api_uploads_data, name='api_uploads_data'),
]
