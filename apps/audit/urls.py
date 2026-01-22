# apps/audit/urls.py

from django.urls import path, include
from django.views.generic import RedirectView
from rest_framework.routers import DefaultRouter
from rest_framework_nested import routers
from django.utils.translation import gettext_lazy as _
from django.conf import settings

from . import views
from .views import (
    WorkplanListView, WorkplanDetailView, WorkplanCreateView, WorkplanUpdateView,
    EngagementListView, EngagementDetailView, EngagementCreateView, EngagementUpdateView,
    IssueListView, IssueDetailView, IssueCreateView, IssueUpdateView,
    ApprovalCreateView, ApprovalDetailView, AuditDashboardView, AuditReportsView,
    ObjectiveListView, ObjectiveDetailView, ObjectiveCreateView, ObjectiveUpdateView,
    ObjectiveModalCreateView, RiskListView, RiskDetailView, RiskCreateView, RiskUpdateView, RiskDeleteView,
    ProcedureListView, ProcedureDetailView, ProcedureCreateView,
    ProcedureUpdateView, ProcedureModalCreateView,
    FollowUpActionListView, FollowUpActionDetailView, FollowUpActionCreateView, FollowUpActionUpdateView,
    FollowUpActionModalCreateView, IssueRetestListView, IssueRetestDetailView, IssueRetestCreateView,
    IssueRetestUpdateView, IssueRetestModalCreateView, NoteCreateView,
    NotificationListView, NoteListView,
    RecommendationListView, RecommendationCreateView, RecommendationUpdateView, RecommendationDetailView,
    IssueWorkingPaperListView, IssueWorkingPaperCreateView, IssueWorkingPaperUpdateView, IssueWorkingPaperDeleteView, IssueWorkingPaperDetailView,
    IssueWorkingPaperViewSet,
    EngagementDocumentListView, EngagementDocumentCreateView, EngagementDocumentDeleteView,
)

# ─── REST API ROUTERS ────────────────────────────────────────────────────────
# Main router for audit app
router = DefaultRouter()
router.register(r'workplans', views.AuditWorkplanViewSet, basename='workplan')
router.register(r'engagements', views.EngagementViewSet, basename='engagement')
router.register(r'issues', views.IssueViewSet, basename='issue')
router.register(r'approvals', views.ApprovalViewSet, basename='approval')
router.register(r'risks', views.RiskViewSet, basename='risk')
router.register(r'objectives', views.ObjectiveViewSet, basename='objective')

# Nested routers for related objects
workplan_router = routers.NestedDefaultRouter(router, r'workplans', lookup='workplan')
workplan_router.register(r'engagements', views.WorkplanEngagementViewSet, basename='workplan-engagement')
workplan_router.register(r'approvals', views.WorkplanApprovalViewSet, basename='workplan-approval')

engagement_router = routers.NestedDefaultRouter(router, r'engagements', lookup='engagement')
engagement_router.register(r'issues', views.EngagementIssueViewSet, basename='engagement-issue')
engagement_router.register(r'approvals', views.EngagementApprovalViewSet, basename='engagement-approval')
engagement_router.register(r'risks', views.EngagementRiskViewSet, basename='engagement-risk')

issue_router = routers.NestedDefaultRouter(router, r'issues', lookup='issue')
issue_router.register(r'approvals', views.IssueApprovalViewSet, basename='issue-approval')
issue_router.register(r'working-papers', IssueWorkingPaperViewSet, basename='issue-working-paper')

# Create a router for objectives and their risks
objective_router = routers.NestedDefaultRouter(router, r'objectives', lookup='objective')
objective_router.register(r'risks', views.ObjectiveRiskViewSet, basename='objective-risk')

# Include all routers in API patterns
api_patterns = [
    path('', include(router.urls)),
    path('', include(workplan_router.urls)),
    path('', include(engagement_router.urls)),
    path('', include(issue_router.urls)),
    path('', include(objective_router.urls)),
]

# ─── URL PATTERNS ────────────────────────────────────────────────────────────
app_name = 'audit'

urlpatterns = [
    # ─── DASHBOARD ──────────────────────────────────────────────────────────
    path('dashboard/', AuditDashboardView.as_view(), name='dashboard'),
    path('reports/', AuditReportsView.as_view(), name='reports'),
    
    # ─── WORKPLAN URLS ──────────────────────────────────────────────────────
    path('workplans/', WorkplanListView.as_view(), name='workplan-list'),
    path('workplans/create/', WorkplanCreateView.as_view(), name='workplan-create'),
    path('workplans/<int:pk>/', WorkplanDetailView.as_view(), name='workplan-detail'),
    path('workplans/<int:pk>/update/', WorkplanUpdateView.as_view(), name='workplan-update'),
    path('workplans/<int:pk>/submit/', views.submit_workplan, name='workplan-submit'),
    path('workplans/<int:pk>/approve/', views.approve_workplan, name='workplan-approve'),
    path('workplans/<int:pk>/reject/', views.reject_workplan, name='workplan-reject'),
    path('workplans/<int:workplan_pk>/engagements/add/', EngagementCreateView.as_view(), name='workplan-engagement-add'),
    
    # ─── ENGAGEMENT URLS ────────────────────────────────────────────────────
    path('engagements/', EngagementListView.as_view(), name='engagement-list'),
    path('engagements/create/', EngagementCreateView.as_view(), name='engagement-create'),
    path('engagements/<int:pk>/', EngagementDetailView.as_view(), name='engagement-detail'),
    path('engagements/<int:pk>/update/', EngagementUpdateView.as_view(), name='engagement-update'),
    path('engagements/<int:pk>/submit/', views.submit_engagement, name='engagement-submit'),
    path('engagements/<int:pk>/approve/', views.approve_engagement, name='engagement-approve'),
    path('engagements/<int:pk>/reject/', views.reject_engagement, name='engagement-reject'),
    path('engagements/<int:engagement_pk>/documents/', EngagementDocumentListView.as_view(), name='engagement-document-list'),
    path('engagements/<int:engagement_pk>/documents/add/', EngagementDocumentCreateView.as_view(), name='engagement-document-add'),
    path('engagements/<int:engagement_pk>/documents/<int:pk>/delete/', EngagementDocumentDeleteView.as_view(), name='engagement-document-delete'),
    
    # ─── ISSUE URLS ─────────────────────────────────────────────────────────
    path('issues/', IssueListView.as_view(), name='issue-list'),
    path('issues/create/', IssueCreateView.as_view(), name='issue-create'),
    path('issues/<int:pk>/', IssueDetailView.as_view(), name='issue-detail'),
    path('issues/<int:pk>/update/', IssueUpdateView.as_view(), name='issue-update'),
    path('issues/<int:pk>/close/', views.close_issue, name='issue-close'),
    path('issues/<int:pk>/reopen/', views.reopen_issue, name='issue-reopen'),
    path('issues/<int:pk>/risks/', views.IssueRiskManageView.as_view(), name='issue-risks'),
    path('issues/<int:pk>/link-risk/', views.link_risk_to_issue, name='issue-link-risk'),
    path('issues/<int:pk>/unlink-risk/', views.unlink_risk_from_issue, name='issue-unlink-risk'),
    
    # ─── APPROVAL URLS ──────────────────────────────────────────────────────
    path('approvals/create/', ApprovalCreateView.as_view(), name='approval-create'),
    path('approvals/<int:pk>/', ApprovalDetailView.as_view(), name='approval-detail'),
    path('approvals/<int:pk>/approve/', views.approve_approval, name='approval-approve'),
    path('approvals/<int:pk>/reject/', views.reject_approval, name='approval-reject'),
    path('approvals/pending/', views.PendingApprovalListView.as_view(), name='approval-pending'),
    path('approvals/history/', views.ApprovalHistoryListView.as_view(), name='approval-history'),
    path('approvals/requested/', views.RequestedApprovalsListView.as_view(), name='approval-requested'),
    path('approvals/<int:pk>/status-update/', views.ApprovalStatusUpdateView.as_view(), name='approval-status-update'),

    
    # ─── API URLS ───────────────────────────────────────────────────────────
    #path('api/', include(router.urls)),
    #path('api/', include(workplan_router.urls)),
    #path('api/', include(engagement_router.urls)),
    path('api/', include(issue_router.urls)),


    # ─── ACTION URLS ────────────────────────────────────────────────────────
    path('actions/bulk-approve/', views.bulk_approve, name='bulk-approve'),
    path('actions/bulk-reject/', views.bulk_reject, name='bulk-reject'),
    path('actions/export/', views.export_data, name='export-data'),
    path('actions/export/workplans/', views.export_workplans, name='export-workplans'),
    path('actions/export/engagements/', views.export_engagements, name='export-engagements'),
    path('actions/export/issues/', views.export_issues, name='export-issues'),
    
    # ─── REPORT URLS ────────────────────────────────────────────────────────
    path('reports/workplans/', views.workplan_report, name='workplan-report'),
    path('reports/engagements/', views.engagement_report, name='engagement-report'),
    path('reports/issues/', views.issue_report, name='issue-report'),
    path('reports/approvals/', views.approval_report, name='approval-report'),
    
    # ─── UTILITY URLS ───────────────────────────────────────────────────────
    path('search/', views.search, name='search'),
    path('autocomplete/', views.autocomplete, name='autocomplete'),
    path('validate/', views.validate, name='validate'),

    # Objective URLs
    path('engagements/<int:engagement_pk>/objectives/', views.ObjectiveListView.as_view(), name='objective-list'),
    path('objectives/<int:pk>/', views.ObjectiveDetailView.as_view(), name='objective-detail'),
    path('engagements/<int:engagement_pk>/objectives/add/', views.ObjectiveCreateView.as_view(), name='objective-add'),
    path('objectives/<int:pk>/edit/', views.ObjectiveUpdateView.as_view(), name='objective-edit'),
    path('objectives/<int:pk>/update/', views.ObjectiveUpdateView.as_view(), name='objective-update'),
    path('engagements/<int:engagement_pk>/objectives/modal/add/', views.ObjectiveModalCreateView.as_view(), name='objective-modal-add'),
    path('objectives/create/', views.ObjectiveModalCreateView.as_view(), name='objective-create'),

    # Risk URLs
    path('objectives/<int:objective_id>/risks/', RiskListView.as_view(), name='risk-list'),
    path('risks/<int:pk>/', RiskDetailView.as_view(), name='risk-detail'),
    path('objectives/<int:objective_id>/risks/add/', RiskCreateView.as_view(), name='risk-add'),
    path('risks/<int:pk>/edit/', RiskUpdateView.as_view(), name='risk-edit'),
    path('risks/<int:pk>/delete/', RiskDeleteView.as_view(), name='risk-delete'),
    path('engagements/<int:engagement_pk>/risks/modal/add/', RiskCreateView.as_view(), name='risk-modal-add'),

    # Procedure URLs (Updated to follow Risk → Procedure hierarchy)
    path('risks/<int:risk_id>/procedures/', views.ProcedureListView.as_view(), name='procedure-list'),
    path('procedures/<int:pk>/', views.ProcedureDetailView.as_view(), name='procedure-detail'),
    path('risks/<int:risk_id>/procedures/add/', views.ProcedureCreateView.as_view(), name='procedure-add'),
    path('procedures/<int:pk>/edit/', views.ProcedureUpdateView.as_view(), name='procedure-edit'),
    path('risks/<int:risk_id>/procedures/modal/add/', views.ProcedureModalCreateView.as_view(), name='procedure-modal-add'),
    # FollowUpAction URLs
    path('issues/<int:issue_pk>/followups/', views.FollowUpActionListView.as_view(), name='followupaction-list'),
    path('followupactions/', views.FollowUpActionListView.as_view(), name='followupaction-list-all'),
    path('issues/<int:issue_pk>/followups/add/', views.FollowUpActionCreateView.as_view(), name='followupaction-add'),
    path('followupactions/<int:pk>/edit/', views.FollowUpActionUpdateView.as_view(), name='followupaction-edit'),
    path('followupactions/<int:pk>/', views.FollowUpActionDetailView.as_view(), name='followupaction-detail'),
    path('issues/<int:issue_pk>/followups/modal/add/', views.FollowUpActionModalCreateView.as_view(), name='followupaction-modal-add'),
    path('issues/<int:issue_pk>/followups/modal/<int:pk>/edit/', views.FollowUpActionModalUpdateView.as_view(), name='followupaction-modal-edit'),
    path('followupactions/<int:pk>/delete/', views.FollowUpActionDeleteView.as_view(), name='followupaction-delete'),
    path('followupactions/<int:pk>/update/', views.FollowUpActionUpdateView.as_view(), name='followupaction-update'),
    # IssueRetest URLs
    path('issues/<int:issue_pk>/retests/', views.IssueRetestListView.as_view(), name='issueretest-list'),
    path('issues/<int:issue_pk>/retests/add/', views.IssueRetestCreateView.as_view(), name='issueretest-add'),
    path('issueretests/<int:pk>/', views.IssueRetestDetailView.as_view(), name='issueretest-detail'),
    path('issueretests/<int:pk>/edit/', views.IssueRetestUpdateView.as_view(), name='issueretest-edit'),
    path('issueretests/<int:pk>/update/', views.IssueRetestUpdateView.as_view(), name='issueretest-update'),
    path('issues/<int:issue_pk>/retests/modal/add/', views.IssueRetestModalCreateView.as_view(), name='issueretest-modal-add'),
    path('issues/<int:issue_pk>/retests/<int:pk>/modal/edit/', views.IssueRetestModalUpdateView.as_view(), name='issueretest-modal-edit'),
    path('issues/<int:issue_pk>/retests/<int:pk>/modal/delete/', views.IssueRetestDeleteView.as_view(), name='issueretest-modal-delete'),
    # Note (generic modal)
    path('notes/modal/add/<int:content_type_id>/<int:object_id>/', views.NoteCreateView.as_view(), name='note-modal-add'),
    path('notes/modal/<int:pk>/edit/', views.NoteModalUpdateView.as_view(), name='note-modal-edit'),
    path('notes/<int:pk>/delete/', views.NoteDeleteView.as_view(), name='note-delete'),
    path('notes/<int:pk>/edit/', views.NoteModalUpdateView.as_view(), name='note-edit'),
    # API endpoint for notifications (JSON data)
    path('api/notifications/', NotificationListView.as_view(), name='notification-api'),
    # Template view for notifications (HTML interface)
    path('notifications/', views.NotificationTemplateView.as_view(), name='notification-list'),
    path('notes/', views.NoteListView.as_view(), name='note-list'),
    path('notes/<int:pk>/', views.NoteDetailView.as_view(), name='note-detail'),
    # Recommendation URLs
    path('recommendations/', RecommendationListView.as_view(), name='recommendation-list'),
    path('issues/<int:issue_pk>/recommendations/', RecommendationListView.as_view(), name='issue-recommendation-list'),
    path('issues/<int:issue_pk>/recommendations/add/', RecommendationCreateView.as_view(), name='recommendation-add'),
    path('recommendations/<int:pk>/edit/', RecommendationUpdateView.as_view(), name='recommendation-edit'),
    # Add the recommendation-update URL pattern to match template references (points to same view as edit)
    path('recommendations/<int:pk>/update/', RecommendationUpdateView.as_view(), name='recommendation-update'),
    path('recommendations/<int:pk>/', RecommendationDetailView.as_view(), name='recommendation-detail'),
    path('recommendations/<int:pk>/delete/', views.RecommendationDeleteView.as_view(), name='recommendation-delete'),
    path('issues/<int:issue_pk>/recommendations/modal/<int:pk>/edit/', views.RecommendationModalUpdateView.as_view(), name='recommendation-modal-edit'),
    path('htmx/objectives/', views.htmx_objective_list, name='htmx-objective-list'),
    path('htmx/procedures/', views.htmx_procedure_list, name='htmx-procedure-list'),
    path('htmx/recommendations/', views.htmx_recommendation_list, name='htmx-recommendation-list'),
    path('htmx/followupactions/', views.htmx_followupaction_list, name='htmx-followupaction-list'),
    path('htmx/issueretests/', views.htmx_issueretest_list, name='htmx-issueretest-list'),
    path('htmx/notes/', views.htmx_note_list, name='htmx-note-list'),
    # Working Paper URLs
    path('issues/<int:issue_pk>/working-papers/', views.IssueWorkingPaperListView.as_view(), name='issueworkingpaper-list'),
    path('issues/<int:issue_pk>/working-papers/modal/add/', IssueWorkingPaperCreateView.as_view(), name='issueworkingpaper-modal-add'),
    path('issues/<int:issue_pk>/working-papers/<int:pk>/edit/', views.IssueWorkingPaperUpdateView.as_view(), name='issueworkingpaper-modal-edit'),
    path('issues/<int:issue_pk>/working-papers/<int:pk>/delete/', views.IssueWorkingPaperDeleteView.as_view(), name='issueworkingpaper-modal-delete'),
    path('working-papers/<int:pk>/', IssueWorkingPaperDetailView.as_view(), name='issueworkingpaper-detail'),
    path('issues/<int:issue_pk>/working-papers/add/', views.IssueWorkingPaperCreateView.as_view(), name='issueworkingpaper-add'),
    path('working-papers/<int:pk>/edit/', views.IssueWorkingPaperUpdateView.as_view(), name='issueworkingpaper-update'),
    path('working-papers/<int:pk>/delete/', views.IssueWorkingPaperDeleteView.as_view(), name='issueworkingpaper-delete'),
    path('api/engagement-status-data/', views.api_engagement_status_data, name='api_engagement_status_data'),
    path('api/issue-risk-data/', views.api_issue_risk_data, name='api_issue_risk_data'),
    path('api/approval-status-data/', views.api_approval_status_data, name='api_approval_status_data'),
    path('api/engagement-data/', views.api_engagement_data, name='api_engagement_data'),
    path('api/issue-data/', views.api_issue_data, name='api_issue_data'),
    path('issues/<int:issue_pk>/retests/modal/add/', IssueRetestModalCreateView.as_view(), name='issueretest-modal-add'),
    path('notes/add/', NoteCreateView.as_view(), name='note-add'),
    

]

# ─── API DOCUMENTATION ───────────────────────────────────────────────────────
try:
    from drf_yasg.views import get_schema_view
    from drf_yasg import openapi
    from rest_framework import permissions
    
    schema_view = get_schema_view(
        openapi.Info(
            title=_("Audit API"),
            default_version='v1',
            description=_("API documentation for the Audit module"),
            terms_of_service="https://www.example.com/terms/",
            contact=openapi.Contact(email="contact@example.com"),
            license=openapi.License(name="BSD License"),
        ),
        public=True,
        permission_classes=(permissions.AllowAny,),
    )
    
    urlpatterns += [
        path('api/docs/', schema_view.with_ui('swagger', cache_timeout=0), name='schema-swagger-ui'),
        path('api/redoc/', schema_view.with_ui('redoc', cache_timeout=0), name='schema-redoc'),
    ]
except ImportError:
    pass

# ─── DEBUG TOOLBAR ──────────────────────────────────────────────────────────
if settings.DEBUG:
    try:
        import debug_toolbar
        urlpatterns += [
            path('__debug__/', include(debug_toolbar.urls)),
        ]
    except ImportError:
        pass
