from django.urls import path, include
from . import views

app_name = 'legal'

urlpatterns = [
    # CaseType URLs
    path('casetypes/', views.CaseTypeListView.as_view(), name='casetype_list'),
    path('casetypes/create/', views.CaseTypeCreateView.as_view(), name='casetype_create'),
    path('casetypes/<int:pk>/', views.CaseTypeDetailView.as_view(), name='casetype_detail'),
    path('casetypes/<int:pk>/edit/', views.CaseTypeUpdateView.as_view(), name='casetype_update'),
    path('casetypes/<int:pk>/delete/', views.CaseTypeDeleteView.as_view(), name='casetype_delete'),

    # LegalParty URLs
    path('parties/', views.LegalPartyListView.as_view(), name='legalparty_list'),
    path('parties/create/', views.LegalPartyCreateView.as_view(), name='legalparty_create'),
    path('parties/<int:pk>/', views.LegalPartyDetailView.as_view(), name='legalparty_detail'),
    path('parties/<int:pk>/edit/', views.LegalPartyUpdateView.as_view(), name='legalparty_update'),
    path('parties/<int:pk>/delete/', views.LegalPartyDeleteView.as_view(), name='legalparty_delete'),

    # LegalCase URLs
    path('cases/', views.LegalCaseListView.as_view(), name='legalcase_list'),
    path('cases/create/', views.LegalCaseCreateView.as_view(), name='legalcase_create'),
    path('cases/<int:pk>/', views.LegalCaseDetailView.as_view(), name='legalcase_detail'),
    path('cases/<int:pk>/edit/', views.LegalCaseUpdateView.as_view(), name='legalcase_update'),
    path('cases/<int:pk>/delete/', views.LegalCaseDeleteView.as_view(), name='legalcase_delete'),

    # CaseParty URLs
    path('caseparties/', views.CasePartyListView.as_view(), name='caseparty_list'),
    path('caseparties/create/', views.CasePartyCreateView.as_view(), name='caseparty_create'),
    path('caseparties/<int:pk>/', views.CasePartyDetailView.as_view(), name='caseparty_detail'),
    path('caseparties/<int:pk>/edit/', views.CasePartyUpdateView.as_view(), name='caseparty_update'),
    path('caseparties/<int:pk>/delete/', views.CasePartyDeleteView.as_view(), name='caseparty_delete'),

    # LegalTask URLs
    path('tasks/', views.LegalTaskListView.as_view(), name='legaltask_list'),
    path('tasks/create/', views.LegalTaskCreateView.as_view(), name='legaltask_create'),
    path('tasks/<int:pk>/', views.LegalTaskDetailView.as_view(), name='legaltask_detail'),
    path('tasks/<int:pk>/edit/', views.LegalTaskUpdateView.as_view(), name='legaltask_update'),
    path('tasks/<int:pk>/delete/', views.LegalTaskDeleteView.as_view(), name='legaltask_delete'),

    # LegalDocument URLs
    path('documents/', views.LegalDocumentListView.as_view(), name='legaldocument_list'),
    path('documents/create/', views.LegalDocumentCreateView.as_view(), name='legaldocument_create'),
    path('documents/<int:pk>/', views.LegalDocumentDetailView.as_view(), name='legaldocument_detail'),
    path('documents/<int:pk>/edit/', views.LegalDocumentUpdateView.as_view(), name='legaldocument_update'),
    path('documents/<int:pk>/delete/', views.LegalDocumentDeleteView.as_view(), name='legaldocument_delete'),

    # LegalArchive URLs
    path('archives/', views.LegalArchiveListView.as_view(), name='legalarchive_list'),
    path('archives/create/', views.LegalArchiveCreateView.as_view(), name='legalarchive_create'),
    path('archives/<int:pk>/', views.LegalArchiveDetailView.as_view(), name='legalarchive_detail'),
    path('archives/<int:pk>/edit/', views.LegalArchiveUpdateView.as_view(), name='legalarchive_update'),
    path('archives/<int:pk>/delete/', views.LegalArchiveDeleteView.as_view(), name='legalarchive_delete'),

    path('', views.LegalDashboardView.as_view(), name='dashboard'),

    # path('api/', include(router.urls)),
    path('api/case-status-data/', views.api_case_status_data, name='api_case_status_data'),
    path('api/task-status-data/', views.api_task_status_data, name='api_task_status_data'),
] 