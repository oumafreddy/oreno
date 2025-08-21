from django.urls import path
from . import views

app_name = 'admin_module'

urlpatterns = [
    # Main Dashboard
    path('', views.AdminDashboardView.as_view(), name='dashboard'),
    
    # Data Export URLs
    path('data-export/', views.DataExportListView.as_view(), name='export-list'),
    path('data-export/create/', views.DataExportCreateView.as_view(), name='export-create'),
    path('data-export/<int:pk>/', views.DataExportDetailView.as_view(), name='export-detail'),
    path('data-export/<int:export_id>/download/', views.download_export_file, name='export-download'),
    path('data-export/<int:export_id>/cancel/', views.cancel_export, name='export-cancel'),
    path('data-export/<int:export_id>/delete/', views.delete_export, name='export-delete'),
    path('data-export/statistics/', views.export_statistics, name='export-statistics'),
    path('data-export/admin/', views.DataExportAdminView.as_view(), name='export-admin'),
    path('data-export/cleanup/', views.cleanup_expired_exports, name='export-cleanup'),
]
