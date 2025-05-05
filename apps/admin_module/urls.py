from django.urls import path
from . import views

app_name = 'admin_module'

urlpatterns = [
    path('', views.AdminDashboardView.as_view(), name='dashboard'),
    path('users/', views.AdminUserListView.as_view(), name='user-list'),
    path('users/<int:pk>/', views.AdminUserDetailView.as_view(), name='user-detail'),
    path('users/<int:pk>/edit/', views.AdminUserUpdateView.as_view(), name='user-update'),
    path('users/<int:pk>/activate/', views.AdminUserActivationView.as_view(), name='user-activate'),
    path('users/<int:pk>/role/', views.AdminUserRoleUpdateView.as_view(), name='user-role'),
    path('settings/', views.AdminOrgSettingsUpdateView.as_view(), name='org-settings'),
]
