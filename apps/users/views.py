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
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse_lazy
from django.views import View
from django.views.generic import TemplateView, FormView, ListView, DetailView, CreateView, UpdateView, DeleteView
from django.contrib.messages.views import SuccessMessageMixin
from django.core.exceptions import PermissionDenied
from django.db import transaction
from django.db.models import Q, Prefetch
from django.utils.translation import gettext_lazy as _

from core.decorators import skip_org_check

from rest_framework import generics, permissions, status
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken

from .forms import CustomUserCreationForm, CustomUserChangeForm, ProfileForm, OrganizationRoleForm
from .models import CustomUser, Profile, OTP, OrganizationRole
from .serializers import (
    UserRegisterSerializer,
    OTPVerifySerializer,
    OTPResendSerializer,
    CustomTokenObtainPairSerializer,
    ProfileSerializer
)
from organizations.mixins import OrganizationContextMixin, OrganizationPermissionMixin
from organizations.models import Organization

# ─── MIXINS ──────────────────────────────────────────────────────────────────
class UserPermissionMixin(OrganizationPermissionMixin):
    """Verify that current user has user management permissions"""
    
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return self.handle_no_permission()
            
        # Get organization from the view's object or kwargs
        organization = None
        if hasattr(self, 'object'):
            organization = self.object.organization
        elif 'organization_pk' in kwargs:
            organization = get_object_or_404(Organization, pk=kwargs['organization_pk'])
        
        if organization and not request.user.has_org_admin_access(organization):
            raise PermissionDenied(_("You don't have permission to manage users in this organization"))
        
        return super().dispatch(request, *args, **kwargs)

# ─── REST API VIEWS ──────────────────────────────────────────────────────────
@method_decorator(skip_org_check, name='dispatch')
class UserRegisterAPIView(generics.CreateAPIView):
    serializer_class = UserRegisterSerializer
    permission_classes = [permissions.AllowAny]

    def perform_create(self, serializer):
        with transaction.atomic():
            user = serializer.save()
            # Create profile and initial OTP
            Profile.objects.create(user=user)
            OTP.objects.create(user=user)

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
        otp = serializer.save()
        return Response({
            "detail": _("OTP verified successfully"),
            "user": ProfileSerializer(request.user.profile).data
        })

@method_decorator(skip_org_check, name='dispatch')
class OTPResendAPIView(generics.GenericAPIView):
    serializer_class = OTPResendSerializer
    permission_classes = [permissions.IsAuthenticated]

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(context={'request': request})
        otp = serializer.save()
        return Response({
            "detail": _("New OTP sent"),
            "expires_at": otp.expires_at
        })

# ─── WEB VIEWS ──────────────────────────────────────────────────────────────
@method_decorator(skip_org_check, name='dispatch')
class UserRegisterView(SuccessMessageMixin, CreateView):
    """
    GET /users/register/  →  show registration form
    POST /users/register/ →  create a new user
    """
    template_name = 'users/register.html'
    form_class = CustomUserCreationForm
    success_url = reverse_lazy('users:login')
    success_message = _("Account created successfully. Please check your email for verification.")

    def form_valid(self, form):
        with transaction.atomic():
            user = form.save()
            Profile.objects.create(user=user)
            OTP.objects.create(user=user)
            return super().form_valid(form)

@method_decorator(skip_org_check, name='dispatch')
class UserLoginView(LoginView):
    template_name = 'users/login.html'
    redirect_authenticated_user = True

class UserLogoutView(LogoutView):
    template_name = 'users/logged_out.html'
    

class ProfileView(LoginRequiredMixin, SuccessMessageMixin, UpdateView):
    model = Profile
    form_class = ProfileForm
    template_name = 'users/profile.html'
    success_url = reverse_lazy('users:profile')
    success_message = _("Profile updated successfully")

    def get_object(self):
        return self.request.user.profile

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['user_form'] = CustomUserChangeForm(instance=self.request.user)
        return context

    def post(self, request, *args, **kwargs):
        self.object = self.get_object()
        form = self.get_form()
        user_form = CustomUserChangeForm(request.POST, instance=request.user)
        
        if form.is_valid() and user_form.is_valid():
            with transaction.atomic():
                user_form.save()
                return self.form_valid(form)
        return self.form_invalid(form)

class UserListView(UserPermissionMixin, ListView):
    model = CustomUser
    template_name = 'users/user_list.html'
    context_object_name = 'users'
    paginate_by = 20

    def get_queryset(self):
        queryset = super().get_queryset()
        organization = self.request.user.organization
        return queryset.filter(
            Q(organization=organization) |
            Q(organizationuser__organization=organization)
        ).select_related('profile').prefetch_related('organizationuser_set')

class UserDetailView(UserPermissionMixin, DetailView):
    model = CustomUser
    template_name = 'users/user_detail.html'
    context_object_name = 'user'

    def get_queryset(self):
        return super().get_queryset().select_related('profile')

class UserUpdateView(UserPermissionMixin, SuccessMessageMixin, UpdateView):
    model = CustomUser
    form_class = CustomUserChangeForm
    template_name = 'users/user_form.html'
    success_message = _("User updated successfully")

    def get_success_url(self):
        return reverse_lazy('users:user-detail', kwargs={'pk': self.object.pk})

class UserDeleteView(UserPermissionMixin, SuccessMessageMixin, DeleteView):
    model = CustomUser
    template_name = 'users/user_confirm_delete.html'
    success_url = reverse_lazy('users:user-list')
    success_message = _("User deleted successfully")

    def delete(self, request, *args, **kwargs):
        if self.get_object() == request.user:
            raise PermissionDenied(_("You cannot delete your own account"))
        return super().delete(request, *args, **kwargs)

# ─── PASSWORD MANAGEMENT VIEWS ──────────────────────────────────────────────
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

# ─── ORGANIZATION ROLE VIEWS ────────────────────────────────────────────────
class OrganizationRoleCreateView(UserPermissionMixin, SuccessMessageMixin, CreateView):
    model = OrganizationRole
    form_class = OrganizationRoleForm
    template_name = 'users/organization_role_form.html'
    success_message = _("Organization role created successfully")

    def get_success_url(self):
        return reverse_lazy('users:user-detail', kwargs={'pk': self.object.user.pk})

    def form_valid(self, form):
        form.instance.organization = self.request.user.organization
        return super().form_valid(form)

class OrganizationRoleUpdateView(UserPermissionMixin, SuccessMessageMixin, UpdateView):
    model = OrganizationRole
    form_class = OrganizationRoleForm
    template_name = 'users/organization_role_form.html'
    success_message = _("Organization role updated successfully")

    def get_success_url(self):
        return reverse_lazy('users:user-detail', kwargs={'pk': self.object.user.pk})

class OrganizationRoleDeleteView(UserPermissionMixin, SuccessMessageMixin, DeleteView):
    model = OrganizationRole
    template_name = 'users/organization_role_confirm_delete.html'
    success_message = _("Organization role deleted successfully")

    def get_success_url(self):
        return reverse_lazy('users:user-detail', kwargs={'pk': self.object.user.pk})

