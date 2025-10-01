from django.urls import path
from rest_framework.routers import DefaultRouter
from . import views
from .views import RiskDashboardView, RiskReportsView, api_heatmap_data, api_assessment_timeline

app_name = 'risk'

# Basic URL patterns for risk app
urlpatterns = [
    path('', RiskDashboardView.as_view(), name='dashboard'),
    path('reports/', RiskReportsView.as_view(), name='reports'),
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

    # Objectives
    path('objectives/', views.ObjectiveListView.as_view(), name='objective_list'),
    path('objectives/create/', views.ObjectiveCreateView.as_view(), name='objective_create'),
    path('objectives/<int:pk>/', views.ObjectiveDetailView.as_view(), name='objective_detail'),
    path('objectives/<int:pk>/update/', views.ObjectiveUpdateView.as_view(), name='objective_update'),
    path('objectives/<int:pk>/delete/', views.ObjectiveDeleteView.as_view(), name='objective_delete'),

    # COBIT URLs
    path('cobit/domains/', views.COBITDomainListView.as_view(), name='cobitdomain_list'),
    path('cobit/domains/create/', views.COBITDomainCreateView.as_view(), name='cobitdomain_create'),
    path('cobit/domains/<int:pk>/', views.COBITDomainDetailView.as_view(), name='cobitdomain_detail'),
    path('cobit/domains/<int:pk>/update/', views.COBITDomainUpdateView.as_view(), name='cobitdomain_update'),
    path('cobit/domains/<int:pk>/delete/', views.COBITDomainDeleteView.as_view(), name='cobitdomain_delete'),

    path('cobit/processes/', views.COBITProcessListView.as_view(), name='cobitprocess_list'),
    path('cobit/processes/create/', views.COBITProcessCreateView.as_view(), name='cobitprocess_create'),
    path('cobit/processes/<int:pk>/', views.COBITProcessDetailView.as_view(), name='cobitprocess_detail'),
    path('cobit/processes/<int:pk>/update/', views.COBITProcessUpdateView.as_view(), name='cobitprocess_update'),
    path('cobit/processes/<int:pk>/delete/', views.COBITProcessDeleteView.as_view(), name='cobitprocess_delete'),

    path('cobit/capabilities/', views.COBITCapabilityListView.as_view(), name='cobitcapability_list'),
    path('cobit/capabilities/create/', views.COBITCapabilityCreateView.as_view(), name='cobitcapability_create'),
    path('cobit/capabilities/<int:pk>/', views.COBITCapabilityDetailView.as_view(), name='cobitcapability_detail'),
    path('cobit/capabilities/<int:pk>/update/', views.COBITCapabilityUpdateView.as_view(), name='cobitcapability_update'),
    path('cobit/capabilities/<int:pk>/delete/', views.COBITCapabilityDeleteView.as_view(), name='cobitcapability_delete'),

    path('cobit/controls/', views.COBITControlListView.as_view(), name='cobitcontrol_list'),
    path('cobit/controls/create/', views.COBITControlCreateView.as_view(), name='cobitcontrol_create'),
    path('cobit/controls/<int:pk>/', views.COBITControlDetailView.as_view(), name='cobitcontrol_detail'),
    path('cobit/controls/<int:pk>/update/', views.COBITControlUpdateView.as_view(), name='cobitcontrol_update'),
    path('cobit/controls/<int:pk>/delete/', views.COBITControlDeleteView.as_view(), name='cobitcontrol_delete'),

    path('cobit/governance/', views.COBITGovernanceListView.as_view(), name='cobitgovernance_list'),
    path('cobit/governance/create/', views.COBITGovernanceCreateView.as_view(), name='cobitgovernance_create'),
    path('cobit/governance/<int:pk>/', views.COBITGovernanceDetailView.as_view(), name='cobitgovernance_detail'),
    path('cobit/governance/<int:pk>/update/', views.COBITGovernanceUpdateView.as_view(), name='cobitgovernance_update'),
    path('cobit/governance/<int:pk>/delete/', views.COBITGovernanceDeleteView.as_view(), name='cobitgovernance_delete'),

    # NIST URLs
    path('nist/functions/', views.NISTFunctionListView.as_view(), name='nistfunction_list'),
    path('nist/functions/create/', views.NISTFunctionCreateView.as_view(), name='nistfunction_create'),
    path('nist/functions/<int:pk>/', views.NISTFunctionDetailView.as_view(), name='nistfunction_detail'),
    path('nist/functions/<int:pk>/update/', views.NISTFunctionUpdateView.as_view(), name='nistfunction_update'),
    path('nist/functions/<int:pk>/delete/', views.NISTFunctionDeleteView.as_view(), name='nistfunction_delete'),

    path('nist/categories/', views.NISTCategoryListView.as_view(), name='nistcategory_list'),
    path('nist/categories/create/', views.NISTCategoryCreateView.as_view(), name='nistcategory_create'),
    path('nist/categories/<int:pk>/', views.NISTCategoryDetailView.as_view(), name='nistcategory_detail'),
    path('nist/categories/<int:pk>/update/', views.NISTCategoryUpdateView.as_view(), name='nistcategory_update'),
    path('nist/categories/<int:pk>/delete/', views.NISTCategoryDeleteView.as_view(), name='nistcategory_delete'),

    path('nist/subcategories/', views.NISTSubcategoryListView.as_view(), name='nistsubcategory_list'),
    path('nist/subcategories/create/', views.NISTSubcategoryCreateView.as_view(), name='nistsubcategory_create'),
    path('nist/subcategories/<int:pk>/', views.NISTSubcategoryDetailView.as_view(), name='nistsubcategory_detail'),
    path('nist/subcategories/<int:pk>/update/', views.NISTSubcategoryUpdateView.as_view(), name='nistsubcategory_update'),
    path('nist/subcategories/<int:pk>/delete/', views.NISTSubcategoryDeleteView.as_view(), name='nistsubcategory_delete'),

    path('nist/implementations/', views.NISTImplementationListView.as_view(), name='nistimplementation_list'),
    path('nist/implementations/create/', views.NISTImplementationCreateView.as_view(), name='nistimplementation_create'),
    path('nist/implementations/<int:pk>/', views.NISTImplementationDetailView.as_view(), name='nistimplementation_detail'),
    path('nist/implementations/<int:pk>/update/', views.NISTImplementationUpdateView.as_view(), name='nistimplementation_update'),
    path('nist/implementations/<int:pk>/delete/', views.NISTImplementationDeleteView.as_view(), name='nistimplementation_delete'),

    path('nist/threats/', views.NISTThreatListView.as_view(), name='nistthreat_list'),
    path('nist/threats/create/', views.NISTThreatCreateView.as_view(), name='nistthreat_create'),
    path('nist/threats/<int:pk>/', views.NISTThreatDetailView.as_view(), name='nistthreat_detail'),
    path('nist/threats/<int:pk>/update/', views.NISTThreatUpdateView.as_view(), name='nistthreat_update'),
    path('nist/threats/<int:pk>/delete/', views.NISTThreatDeleteView.as_view(), name='nistthreat_delete'),

    path('nist/incidents/', views.NISTIncidentListView.as_view(), name='nistincident_list'),
    path('nist/incidents/create/', views.NISTIncidentCreateView.as_view(), name='nistincident_create'),
    path('nist/incidents/<int:pk>/', views.NISTIncidentDetailView.as_view(), name='nistincident_detail'),
    path('nist/incidents/<int:pk>/update/', views.NISTIncidentUpdateView.as_view(), name='nistincident_update'),
    path('nist/incidents/<int:pk>/delete/', views.NISTIncidentDeleteView.as_view(), name='nistincident_delete'),

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
    
    # API endpoints for audit integration
    path('api/riskregisters/', views.api_riskregister_list, name='riskregister-list'),
    path('api/risks/', views.api_risk_list, name='risk-list'),
    
    # COBIT API Endpoints
    path('api/cobit/domain-distribution/', views.api_cobit_domain_distribution, name='api_cobit_domain_distribution'),
    path('api/cobit/control-status/', views.api_cobit_control_status, name='api_cobit_control_status'),
    path('api/cobit/maturity-trend/', views.api_cobit_maturity_trend, name='api_cobit_maturity_trend'),
    
    # NIST API Endpoints
    path('api/nist/function-distribution/', views.api_nist_function_distribution, name='api_nist_function_distribution'),
    path('api/nist/threat-severity/', views.api_nist_threat_severity, name='api_nist_threat_severity'),
    path('api/nist/incident-timeline/', views.api_nist_incident_timeline, name='api_nist_incident_timeline'),
    path('api/cobit-nist-summary/', views.api_cobit_nist_summary, name='api_cobit_nist_summary'),
    
    path('export/risks/', views.export_risks, name='export_risks'),
    path('export/kris/', views.export_kris, name='export_kris'),
    path('export/assessments/', views.export_assessments, name='export_assessments'),
]

# API router for risk endpoints
router = DefaultRouter()
# Register your risk API viewsets here

# Include API URLs
urlpatterns += router.urls
