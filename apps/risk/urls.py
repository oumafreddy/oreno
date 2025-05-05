from django.urls import path
from rest_framework.routers import DefaultRouter
from django.views.generic import TemplateView
from . import views
from .views import RiskDashboardView, api_heatmap_data, api_assessment_timeline

app_name = 'risk'

# Basic URL patterns for risk app
urlpatterns = [
    path('', RiskDashboardView.as_view(), name='dashboard'),
    path('', TemplateView.as_view(template_name='risk/list.html'), name='list'),
    # RiskRegister
    path('registers/', views.RiskRegisterListView.as_view(), name='riskregister_list'),
    path('registers/create/', views.RiskRegisterCreateView.as_view(), name='riskregister_create'),
    path('registers/<int:pk>/', views.RiskRegisterDetailView.as_view(), name='riskregister_detail'),
    path('registers/<int:pk>/update/', views.RiskRegisterUpdateView.as_view(), name='riskregister_update'),
    path('registers/<int:pk>/delete/', views.RiskRegisterDeleteView.as_view(), name='riskregister_delete'),

    # RiskMatrixConfig
    path('matrix/', views.RiskMatrixConfigListView.as_view(), name='riskmatrixconfig_list'),
    path('matrix/create/', views.RiskMatrixConfigCreateView.as_view(), name='riskmatrixconfig_create'),
    path('matrix/<int:pk>/', views.RiskMatrixConfigDetailView.as_view(), name='riskmatrixconfig_detail'),
    path('matrix/<int:pk>/update/', views.RiskMatrixConfigUpdateView.as_view(), name='riskmatrixconfig_update'),
    path('matrix/<int:pk>/delete/', views.RiskMatrixConfigDeleteView.as_view(), name='riskmatrixconfig_delete'),

    # Risk
    path('risks/', views.RiskListView.as_view(), name='risk_list'),
    path('risks/create/', views.RiskCreateView.as_view(), name='risk_create'),
    path('risks/<int:pk>/', views.RiskDetailView.as_view(), name='risk_detail'),
    path('risks/<int:pk>/update/', views.RiskUpdateView.as_view(), name='risk_update'),
    path('risks/<int:pk>/delete/', views.RiskDeleteView.as_view(), name='risk_delete'),

    # Control
    path('controls/', views.ControlListView.as_view(), name='control_list'),
    path('controls/create/', views.ControlCreateView.as_view(), name='control_create'),
    path('controls/<int:pk>/', views.ControlDetailView.as_view(), name='control_detail'),
    path('controls/<int:pk>/update/', views.ControlUpdateView.as_view(), name='control_update'),
    path('controls/<int:pk>/delete/', views.ControlDeleteView.as_view(), name='control_delete'),

    # KRI
    path('kri/', views.KRIListView.as_view(), name='kri_list'),
    path('kri/create/', views.KRICreateView.as_view(), name='kri_create'),
    path('kri/<int:pk>/', views.KRIDetailView.as_view(), name='kri_detail'),
    path('kri/<int:pk>/update/', views.KRIUpdateView.as_view(), name='kri_update'),
    path('kri/<int:pk>/delete/', views.KRIDeleteView.as_view(), name='kri_delete'),

    # RiskAssessment
    path('assessments/', views.RiskAssessmentListView.as_view(), name='riskassessment_list'),
    path('assessments/create/', views.RiskAssessmentCreateView.as_view(), name='riskassessment_create'),
    path('assessments/<int:pk>/', views.RiskAssessmentDetailView.as_view(), name='riskassessment_detail'),
    path('assessments/<int:pk>/update/', views.RiskAssessmentUpdateView.as_view(), name='riskassessment_update'),
    path('assessments/<int:pk>/delete/', views.RiskAssessmentDeleteView.as_view(), name='riskassessment_delete'),

    path('api/heatmap/', api_heatmap_data, name='api_heatmap_data'),
    path('api/assessment-timeline/', api_assessment_timeline, name='api_assessment_timeline'),
    path('api/summary-cards/', views.api_summary_cards, name='api_summary_cards'),
    path('api/top-risks/', views.api_top_risks, name='api_top_risks'),
    path('api/kri-status/', views.api_kri_status, name='api_kri_status'),
    path('api/recent-activity/', views.api_recent_activity, name='api_recent_activity'),
    path('api/assessment-timeline-details/', views.api_assessment_timeline_details, name='api_assessment_timeline_details'),
    path('api/risk-category-distribution/', views.api_risk_category_distribution, name='api_risk_category_distribution'),
    path('api/risk-status-distribution/', views.api_risk_status_distribution, name='api_risk_status_distribution'),
    path('api/control-effectiveness/', views.api_control_effectiveness, name='api_control_effectiveness'),
    path('api/kri-status-counts/', views.api_kri_status_counts, name='api_kri_status_counts'),
    path('api/assessment-type-counts/', views.api_assessment_type_counts, name='api_assessment_type_counts'),
    path('api/risk-advanced-filter/', views.api_risk_advanced_filter, name='api_risk_advanced_filter'),
    path('api/kri-advanced-filter/', views.api_kri_advanced_filter, name='api_kri_advanced_filter'),
    path('api/assessment-advanced-filter/', views.api_assessment_advanced_filter, name='api_assessment_advanced_filter'),
    path('export/risks/', views.export_risks, name='export_risks'),
    path('export/kris/', views.export_kris, name='export_kris'),
    path('export/assessments/', views.export_assessments, name='export_assessments'),
]

# API router for risk endpoints
router = DefaultRouter()
# Register your risk API viewsets here

# Include API URLs
urlpatterns += router.urls
