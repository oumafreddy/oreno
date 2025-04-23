# apps/users/views.py
from django.utils.decorators import method_decorator
from django.contrib.auth.decorators import login_required
from django.contrib.auth.mixins import LoginRequiredMixin
from django.contrib.auth import login, logout
from django.contrib.auth.views import (
    LoginView, LogoutView,
    PasswordChangeView, PasswordChangeDoneView,
    PasswordResetView, PasswordResetDoneView,
    PasswordResetConfirmView, PasswordResetCompleteView,
)
from django.shortcuts import render, redirect
from django.urls import reverse_lazy
from django.views import View
from django.views.generic import TemplateView, FormView

from apps.core.decorators import skip_org_check

from rest_framework import generics, permissions
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from rest_framework.response import Response

from .forms import CustomUserCreationForm, CustomUserChangeForm, ProfileForm
from .models import Profile
from .serializers import (
    UserRegisterSerializer,
    OTPVerifySerializer,
    OTPResendSerializer,
    CustomTokenObtainPairSerializer,
)

# ─── REST API VIEWS ───────────────────────────────────────────────────────────
@method_decorator(skip_org_check, name='dispatch')
class UserRegisterAPIView(generics.CreateAPIView):
    serializer_class = UserRegisterSerializer
    permission_classes = [permissions.AllowAny]

@method_decorator(skip_org_check, name='dispatch')
class UserLoginAPIView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer
    permission_classes = [permissions.AllowAny]

@method_decorator(skip_org_check, name='dispatch')
class TokenRefreshAPIView(TokenRefreshView):
    permission_classes = [permissions.AllowAny]

@method_decorator(skip_org_check, name='dispatch')
class OTPVerifyAPIView(generics.GenericAPIView):
    """
    POST /api/users/verify-otp/  →  verify one-time password
    """
    serializer_class = OTPVerifySerializer
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response({"detail": "OTP verified successfully."})

@method_decorator(skip_org_check, name='dispatch')
class OTPResendAPIView(generics.GenericAPIView):
    serializer_class = OTPResendSerializer
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(context={'request': request})
        otp = serializer.save()
        return Response({
            "detail": "New OTP sent.",
            "expires_at": otp.expires_at
        })

# ─── HTML / WEB VIEWS ──────────────────────────────────────────────────────────
@method_decorator(skip_org_check, name='dispatch')
class UserRegisterView(FormView):
    """
    GET /users/register/  →  show registration form
    POST /users/register/ →  create a new user
    """
    template_name = 'users/register.html'
    form_class = CustomUserCreationForm
    success_url = reverse_lazy('users:login')

    def form_valid(self, form):
        user = form.save()
        Profile.objects.create(user=user)
        return super().form_valid(form)

@method_decorator(skip_org_check, name='dispatch')
class UserLoginView(LoginView):
    template_name = 'users/login.html'
    # redirect_authenticated_user = True      

class UserLogoutView(LogoutView):
    template_name = 'users/logged_out.html'
    

class ProfileView(LoginRequiredMixin, View):
    template_name = 'users/profile.html'

    def get(self, request, *args, **kwargs):
        profile, _ = Profile.objects.get_or_create(user=request.user)
        u_form = CustomUserChangeForm(instance=request.user)
        p_form = ProfileForm(instance=profile)
        return render(request, self.template_name, {'u_form': u_form, 'p_form': p_form})

    def post(self, request, *args, **kwargs):
        profile, _ = Profile.objects.get_or_create(user=request.user)
        u_form = CustomUserChangeForm(request.POST, instance=request.user)
        p_form = ProfileForm(request.POST, request.FILES, instance=profile)
        if u_form.is_valid() and p_form.is_valid():
            u_form.save()
            p_form.save()
            return redirect('users:profile')
        return render(request, self.template_name, {'u_form': u_form, 'p_form': p_form})

@method_decorator(login_required, name='dispatch')
class UserPasswordChangeView(PasswordChangeView):
    template_name = 'users/password_change.html'
    success_url = reverse_lazy('users:password_change_done')

@method_decorator(login_required, name='dispatch')
class UserPasswordChangeDoneView(PasswordChangeDoneView):
    template_name = 'users/password_change_done.html'

class UserPasswordResetView(PasswordResetView):
    template_name = 'users/password_reset.html'
    email_template_name = 'users/password_reset_email.html'
    subject_template_name = 'users/password_reset_subject.txt'
    success_url = reverse_lazy('users:password_reset_done')

class UserPasswordResetDoneView(PasswordResetDoneView):
    template_name = 'users/password_reset_done.html'

class UserPasswordResetConfirmView(PasswordResetConfirmView):
    template_name = 'users/password_reset_confirm.html'
    success_url = reverse_lazy('users:password_reset_complete')

class UserPasswordResetCompleteView(PasswordResetCompleteView):
    template_name = 'users/password_reset_complete.html'

