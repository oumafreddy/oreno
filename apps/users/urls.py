# apps/users/urls.py
from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_nested import routers
from django.utils.translation import gettext_lazy as _

from .views import (
    # Web Views
    UserLoginView,
    UserLogoutView,
    ProfileView,
    UserPasswordChangeView,
    UserPasswordChangeDoneView,
    UserPasswordResetView,
    UserPasswordResetDoneView,
    UserPasswordResetConfirmView,
    UserPasswordResetCompleteView,
    UserListView,
    UserDetailView,
    UserUpdateView,
    UserDeleteView,
    OrganizationRoleCreateView,
    OrganizationRoleUpdateView,
    OrganizationRoleDeleteView,
    # API Views
    UserRegisterAPIView,
    UserLoginAPIView,
    TokenRefreshAPIView,
    OTPVerifyAPIView,
    OTPResendAPIView,
    ProfileAPIView,
)

app_name = 'users'

# Web URL patterns
urlpatterns = [
    # Authentication
    path('login/', UserLoginView.as_view(), name='login'),
    path('logout/', UserLogoutView.as_view(), name='logout'),
    path('profile/', ProfileView.as_view(), name='profile'),
    
    # Password Management
    path('password/change/', UserPasswordChangeView.as_view(), name='password_change'),
    path('password/change/done/', UserPasswordChangeDoneView.as_view(), name='password_change_done'),
    path('password/reset/', UserPasswordResetView.as_view(), name='password_reset'),
    path('password/reset/done/', UserPasswordResetDoneView.as_view(), name='password_reset_done'),
    path('password/reset/<uidb64>/<token>/', UserPasswordResetConfirmView.as_view(), name='password_reset_confirm'),
    path('password/reset/complete/', UserPasswordResetCompleteView.as_view(), name='password_reset_complete'),
    
    # User Management
    path('', UserListView.as_view(), name='user-list'),
    path('<int:pk>/', UserDetailView.as_view(), name='user-detail'),
    path('<int:pk>/update/', UserUpdateView.as_view(), name='user-update'),
    path('<int:pk>/delete/', UserDeleteView.as_view(), name='user-delete'),
    
    # Organization Roles
    path('roles/create/', OrganizationRoleCreateView.as_view(), name='role-create'),
    path('roles/<int:pk>/update/', OrganizationRoleUpdateView.as_view(), name='role-update'),
    path('roles/<int:pk>/delete/', OrganizationRoleDeleteView.as_view(), name='role-delete'),
    
    # API endpoints
    path('api/register/', UserRegisterAPIView.as_view(), name='api-register'),
    path('api/login/', UserLoginAPIView.as_view(), name='api-login'),
    path('api/token/refresh/', TokenRefreshAPIView.as_view(), name='token-refresh'),
    path('api/verify-otp/', OTPVerifyAPIView.as_view(), name='verify-otp'),
    path('api/resend-otp/', OTPResendAPIView.as_view(), name='resend-otp'),
    path('api/users/profile/', ProfileAPIView.as_view(), name='api-profile'),
]
