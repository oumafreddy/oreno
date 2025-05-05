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
    ApprovalCreateView, ApprovalDetailView, AuditDashboardView
)

# ─── REST API ROUTERS ────────────────────────────────────────────────────────
# Main router for audit app
router = DefaultRouter()
router.register(r'workplans', views.AuditWorkplanViewSet, basename='workplan')
router.register(r'engagements', views.EngagementViewSet, basename='engagement')
router.register(r'issues', views.IssueViewSet, basename='issue')
router.register(r'approvals', views.ApprovalViewSet, basename='approval')

# Nested routers for related objects
workplan_router = routers.NestedDefaultRouter(router, r'workplans', lookup='workplan')
workplan_router.register(r'engagements', views.WorkplanEngagementViewSet, basename='workplan-engagement')
workplan_router.register(r'approvals', views.WorkplanApprovalViewSet, basename='workplan-approval')

engagement_router = routers.NestedDefaultRouter(router, r'engagements', lookup='engagement')
engagement_router.register(r'issues', views.EngagementIssueViewSet, basename='engagement-issue')
engagement_router.register(r'approvals', views.EngagementApprovalViewSet, basename='engagement-approval')

issue_router = routers.NestedDefaultRouter(router, r'issues', lookup='issue')
issue_router.register(r'approvals', views.IssueApprovalViewSet, basename='issue-approval')

# ─── URL PATTERNS ────────────────────────────────────────────────────────────
app_name = 'audit'

urlpatterns = [
    # ─── DASHBOARD ──────────────────────────────────────────────────────────
    path('dashboard/', AuditDashboardView.as_view(), name='dashboard'),
    
    # ─── WORKPLAN URLS ──────────────────────────────────────────────────────
    path('workplans/', WorkplanListView.as_view(), name='workplan-list'),
    path('workplans/create/', WorkplanCreateView.as_view(), name='workplan-create'),
    path('workplans/<int:pk>/', WorkplanDetailView.as_view(), name='workplan-detail'),
    path('workplans/<int:pk>/update/', WorkplanUpdateView.as_view(), name='workplan-update'),
    path('workplans/<int:pk>/submit/', views.submit_workplan, name='workplan-submit'),
    path('workplans/<int:pk>/approve/', views.approve_workplan, name='workplan-approve'),
    path('workplans/<int:pk>/reject/', views.reject_workplan, name='workplan-reject'),
    
    # ─── ENGAGEMENT URLS ────────────────────────────────────────────────────
    path('engagements/', EngagementListView.as_view(), name='engagement-list'),
    path('engagements/create/', EngagementCreateView.as_view(), name='engagement-create'),
    path('engagements/<int:pk>/', EngagementDetailView.as_view(), name='engagement-detail'),
    path('engagements/<int:pk>/update/', EngagementUpdateView.as_view(), name='engagement-update'),
    path('engagements/<int:pk>/submit/', views.submit_engagement, name='engagement-submit'),
    path('engagements/<int:pk>/approve/', views.approve_engagement, name='engagement-approve'),
    path('engagements/<int:pk>/reject/', views.reject_engagement, name='engagement-reject'),
    
    # ─── ISSUE URLS ─────────────────────────────────────────────────────────
    path('issues/', IssueListView.as_view(), name='issue-list'),
    path('issues/create/', IssueCreateView.as_view(), name='issue-create'),
    path('issues/<int:pk>/', IssueDetailView.as_view(), name='issue-detail'),
    path('issues/<int:pk>/update/', IssueUpdateView.as_view(), name='issue-update'),
    path('issues/<int:pk>/close/', views.close_issue, name='issue-close'),
    path('issues/<int:pk>/reopen/', views.reopen_issue, name='issue-reopen'),
    
    # ─── APPROVAL URLS ──────────────────────────────────────────────────────
    path('approvals/create/', ApprovalCreateView.as_view(), name='approval-create'),
    path('approvals/<int:pk>/', ApprovalDetailView.as_view(), name='approval-detail'),
    path('approvals/<int:pk>/approve/', views.approve_approval, name='approval-approve'),
    path('approvals/<int:pk>/reject/', views.reject_approval, name='approval-reject'),

    
    # ─── API URLS ───────────────────────────────────────────────────────────
    #path('api/', include(router.urls)),
    #path('api/', include(workplan_router.urls)),
    #path('api/', include(engagement_router.urls)),
    #path('api/', include(issue_router.urls)),


    # ─── ACTION URLS ────────────────────────────────────────────────────────
    path('actions/bulk-approve/', views.bulk_approve, name='bulk-approve'),
    path('actions/bulk-reject/', views.bulk_reject, name='bulk-reject'),
    path('actions/export/', views.export_data, name='export-data'),
    
    # ─── REPORT URLS ────────────────────────────────────────────────────────
    path('reports/workplans/', views.workplan_report, name='workplan-report'),
    path('reports/engagements/', views.engagement_report, name='engagement-report'),
    path('reports/issues/', views.issue_report, name='issue-report'),
    path('reports/approvals/', views.approval_report, name='approval-report'),
    
    # ─── UTILITY URLS ───────────────────────────────────────────────────────
    path('search/', views.search, name='search'),
    path('autocomplete/', views.autocomplete, name='autocomplete'),
    path('validate/', views.validate, name='validate'),
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
