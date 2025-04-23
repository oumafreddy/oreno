# apps/users/urls.py
from django.urls import path
from .views import (
    # HTML / Web Views
    UserRegisterView,
    UserLoginView,
    UserLogoutView,
    ProfileView,
    UserPasswordChangeView,
    UserPasswordChangeDoneView,
    UserPasswordResetView,
    UserPasswordResetDoneView,
    UserPasswordResetConfirmView,
    UserPasswordResetCompleteView,
    # API Views
    UserRegisterAPIView,
    UserLoginAPIView,
    TokenRefreshAPIView,
    OTPVerifyAPIView,
    OTPResendAPIView,
)

app_name = 'users'
urlpatterns = [
    # HTML / Web Views
    path('register/', UserRegisterView.as_view(), name='register'),
    path('login/',    UserLoginView.as_view(),    name='login'),
    path('logout/',   UserLogoutView.as_view(),   name='logout'),
    path('profile/',  ProfileView.as_view(),      name='profile'),

    # Password Change
    path('password/change/',
         UserPasswordChangeView.as_view(),
         name='password_change'),
    path('password/change/done/',
         UserPasswordChangeDoneView.as_view(),
         name='password_change_done'),

    # Password Reset
    path('password/reset/',
         UserPasswordResetView.as_view(),
         name='password_reset'),
    path('password/reset/done/',
         UserPasswordResetDoneView.as_view(),
         name='password_reset_done'),
    path('password/reset/confirm/<uidb64>/<token>/',
         UserPasswordResetConfirmView.as_view(),
         name='password_reset_confirm'),
    path('password/reset/complete/',
         UserPasswordResetCompleteView.as_view(),
         name='password_reset_complete'),

    # REST API Endpoints
    path('api/register/',      UserRegisterAPIView.as_view(), name='api-register'),
    path('api/login/',         UserLoginAPIView.as_view(),    name='api-login'),
    path('api/token/refresh/', TokenRefreshAPIView.as_view(), name='token_refresh'),
    path('api/verify-otp/',    OTPVerifyAPIView.as_view(),    name='api-verify-otp'),
    path('api/otp/resend/',    OTPResendAPIView.as_view(),    name='api-otp-resend'),
]
