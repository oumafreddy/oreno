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
from django.contrib import messages
from django.core.exceptions import PermissionDenied, ValidationError
from django.db import transaction
from django.db.models import Q, Prefetch
from django.utils.translation import gettext_lazy as _
from django.db import IntegrityError

from core.decorators import skip_org_check
from core.mixins.organization import OrganizationScopedQuerysetMixin

from rest_framework import generics, permissions, status
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.token_blacklist.models import OutstandingToken, BlacklistedToken

from .forms import CustomUserCreationForm, CustomUserChangeForm, ProfileForm, OrganizationRoleForm, AdminUserCreationForm, CustomSetPasswordForm
from .models import CustomUser, Profile, OTP, OrganizationRole, PasswordHistory, AccountLockout, SecurityAuditLog
from .serializers import (
    UserRegisterSerializer,
    OTPVerifySerializer,
    OTPResendSerializer,
    CustomTokenObtainPairSerializer,
    ProfileSerializer,
    UserSerializer,
)
from .validators import FirstTimeSetupPasswordValidator, validate_password_strength
from organizations.mixins import OrganizationContextMixin, OrganizationPermissionMixin
from organizations.models import Organization
from .permissions import IsOrgAdmin, IsOrgManagerOrReadOnly, HasOrgAdminAccess

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
    permission_classes = [permissions.AllowAny, HasOrgAdminAccess]

    def perform_create(self, serializer):
        with transaction.atomic():
            user = serializer.save()
            # Profile and OTP are automatically created by signals

@method_decorator(skip_org_check, name='dispatch')
class UserLoginAPIView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer
    permission_classes = [permissions.AllowAny]
    
    def post(self, request, *args, **kwargs):
        """Override to add tenant access validation after successful authentication."""
        client_ip = request.META.get('REMOTE_ADDR')
        user_agent = request.META.get('HTTP_USER_AGENT', '')
        
        response = super().post(request, *args, **kwargs)
        
        # Only check if authentication was successful
        if response.status_code == 200:
            # Get the user from the serializer
            serializer = self.get_serializer(data=request.data)
            if serializer.is_valid():
                user = serializer.user
                # Audit logging
                SecurityAuditLog.log_event(user, 'login_success', client_ip or '0.0.0.0', user_agent)
                
                # Get current tenant from request
                current_tenant = getattr(request, 'tenant', None)
                
                from core.utils import user_has_tenant_access
                if current_tenant and not user_has_tenant_access(user, current_tenant):
                    # User doesn't have access to this tenant
                    SecurityAuditLog.log_event(user, 'suspicious_activity', client_ip or '0.0.0.0', user_agent, {'reason': 'tenant_access_denied'})
                    return Response({
                        'detail': _("Access denied. You can only access your assigned organization.")
                    }, status=403)
        else:
            # Authentication failed
            email = request.data.get('email')
            user = CustomUser.objects.filter(email=email).first()
            if user:
                SecurityAuditLog.log_event(user, 'login_failed', client_ip or '0.0.0.0', user_agent)
                # Record failed attempt and possibly lock out
                AccountLockout.record_failed_attempt(user, client_ip or '0.0.0.0', user_agent)
        
        return response

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

class ProfileAPIView(OrganizationScopedQuerysetMixin, generics.RetrieveUpdateAPIView):
    """
    API view for retrieving and updating user profile information.
    Requires authentication and tenant scoping.
    """
    serializer_class = ProfileSerializer
    permission_classes = [permissions.IsAuthenticated, IsOrgManagerOrReadOnly]
    def get_object(self):
        return self.request.user
    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)
        return Response(serializer.data)

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
            # Profile and OTP are automatically created by signals
            return super().form_valid(form)

@method_decorator(skip_org_check, name='dispatch')
class UserLoginView(LoginView):
    template_name = 'users/login.html'
    redirect_authenticated_user = True

    def form_valid(self, form):
        """Override to add tenant access validation and first-time setup check after successful authentication."""
        response = super().form_valid(form)
        client_ip = self.request.META.get('REMOTE_ADDR')
        user_agent = self.request.META.get('HTTP_USER_AGENT', '')
        
        # Get the authenticated user
        user = form.get_user()
        # Audit
        SecurityAuditLog.log_event(user, 'login_success', client_ip or '0.0.0.0', user_agent)
        
        # Get current tenant from request
        current_tenant = getattr(self.request, 'tenant', None)
        
        from core.utils import user_has_tenant_access
        if current_tenant and not user_has_tenant_access(user, current_tenant):
            # User doesn't have access to this tenant
            from django.contrib.auth import logout
            logout(self.request)
            SecurityAuditLog.log_event(user, 'suspicious_activity', client_ip or '0.0.0.0', user_agent, {'reason': 'tenant_access_denied'})
            
            messages.error(
                self.request,
                _("Access denied. You can only access your assigned organization.")
            )
            
            # Redirect back to login
            return redirect('users:login')
        
        # Check if user requires first-time setup
        if user.requires_first_time_setup():
            # Store user info in session for first-time setup
            self.request.session['first_time_setup_user_id'] = user.id
            self.request.session['first_time_setup_required'] = True
            
            # Redirect to first-time setup page
            return redirect('users:first-time-setup')
        
        return response

    def get_success_url(self):
        # Always redirect to the Professional Home Dashboard
        return reverse_lazy('home')


@method_decorator(skip_org_check, name='dispatch')
class FirstTimeSetupView(LoginRequiredMixin, TemplateView):
    """
    First-time setup view for new users to verify OTP and reset password.
    """
    template_name = 'users/first_time_setup.html'
    
    def dispatch(self, request, *args, **kwargs):
        # Check if user actually needs first-time setup
        if not request.user.requires_first_time_setup():
            return redirect('home')
        
        # Check if this is the correct user for first-time setup
        setup_user_id = request.session.get('first_time_setup_user_id')
        if not setup_user_id or setup_user_id != request.user.id:
            messages.error(request, _("Invalid first-time setup session."))
            return redirect('users:login')
        
        # Handle resend OTP request
        if (request.path.endswith('/resend-otp/') or request.POST.get('resend_otp')) and request.method == 'POST':
            return self.resend_otp(request, *args, **kwargs)
        
        return super().dispatch(request, *args, **kwargs)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.request.user
        
        # Get or create OTP for the user
        otp, created = OTP.objects.get_or_create(
            user=user,
            is_verified=False,
            defaults={'is_expired': False}
        )
        
        if created:
            # Send OTP via email
            try:
                otp.send_via_email()
                messages.success(
                    self.request,
                    _("OTP code has been sent to your email address.")
                )
            except Exception as e:
                messages.error(
                    self.request,
                    _("Failed to send OTP. Please contact support.")
                )
        
        # Get password policy hints
        from .forms import get_password_policy_hints
        policy_hints = get_password_policy_hints(user=user)
        
        context.update({
            'user': user,
            'otp': otp,
            'is_admin_created': user.is_admin_created,
            'policy_hints': policy_hints,
        })
        return context
    
    def post(self, request, *args, **kwargs):
        """Handle OTP verification and password reset."""
        user = request.user
        otp_code = request.POST.get('otp_code')
        new_password = request.POST.get('new_password')
        confirm_password = request.POST.get('confirm_password')
        
        # Verify OTP
        try:
            otp = OTP.objects.get(
                user=user,
                otp=otp_code,
                is_verified=False,
                is_expired=False
            )
            
            if otp.has_expired():
                messages.error(request, _("OTP code has expired. Please request a new one."))
                return self.get(request, *args, **kwargs)
            
            if otp.attempts >= OTP.MAX_ATTEMPTS:
                messages.error(request, _("Too many failed attempts. Please request a new OTP."))
                return self.get(request, *args, **kwargs)
            
            # Verify OTP
            if otp.verify(otp_code):
                # OTP is valid, now handle password reset
                if new_password and confirm_password:
                    if new_password != confirm_password:
                        messages.error(request, _("Passwords do not match."))
                        return self.get(request, *args, **kwargs)
                    
                    # Validate password strength using organization-specific validators
                    try:
                        # Get organization-specific validators if available
                        validators = []
                        if user.organization:
                            try:
                                policy = user.organization.password_policy
                                if policy:
                                    validators = policy.get_validators()
                            except Exception:
                                pass
                        
                        # If no organization policy, use default validators
                        if not validators:
                            from .validators import EnhancedPasswordStrengthValidator, PasswordComplexityValidator, PasswordHistoryValidator, PasswordBreachValidator
                            validators = [
                                EnhancedPasswordStrengthValidator(),
                                PasswordComplexityValidator(),
                                PasswordHistoryValidator(),
                                PasswordBreachValidator(),
                            ]
                        
                        # Validate with all applicable validators
                        for validator in validators:
                            validator.validate(new_password, user)
                            
                    except ValidationError as e:
                        for error in e.messages:
                            messages.error(request, error)
                        return self.get(request, *args, **kwargs)
                    
                    # Check if password is being reused (first-time setup validation)
                    first_time_validator = FirstTimeSetupPasswordValidator()
                    try:
                        first_time_validator.validate(new_password, user)
                    except ValidationError as e:
                        messages.error(request, e.message)
                        return self.get(request, *args, **kwargs)
                    
                    # Store current password in history before changing it
                    PasswordHistory.store_password(user, user.password, reason='change', is_hashed=True)
                    
                    # Set new password and mark setup as complete
                    user.set_password(new_password)
                    user.is_first_time_setup_complete = True
                    user.save()
                    
                    # Store new password in history
                    PasswordHistory.store_password(user, new_password, reason='reset')
                    
                    # Cleanup old password history
                    PasswordHistory.cleanup_old_passwords(user)
                    
                    # Clear session data
                    request.session.pop('first_time_setup_user_id', None)
                    request.session.pop('first_time_setup_required', None)
                    
                    messages.success(
                        request,
                        _("Account setup completed successfully! You can now access the application.")
                    )
                    
                    # Re-authenticate user with new password
                    from django.contrib.auth import login
                    login(request, user)
                    
                    return redirect('home')
                else:
                    messages.error(request, _("Please provide a new password."))
                    return self.get(request, *args, **kwargs)
            else:
                messages.error(request, _("Invalid OTP code. Please try again."))
                return self.get(request, *args, **kwargs)
                
        except OTP.DoesNotExist:
            messages.error(request, _("Invalid OTP code. Please try again."))
            return self.get(request, *args, **kwargs)
    
    def resend_otp(self, request, *args, **kwargs):
        """Handle OTP resend request."""
        user = request.user
        
        # Expire old OTPs
        OTP.objects.filter(
            user=user,
            is_verified=False
        ).update(is_expired=True)
        
        # Create new OTP
        new_otp = OTP.objects.create(user=user)
        
        try:
            new_otp.send_via_email()
            messages.success(
                request,
                _("New OTP code has been sent to your email address.")
            )
        except Exception as e:
            messages.error(
                request,
                _("Failed to send OTP. Please contact support.")
            )
        
        # Redirect back to the setup page
        return redirect('users:first-time-setup')

@method_decorator(skip_org_check, name='dispatch')
class UserLogoutView(LogoutView):
    """Logs out user and blacklists their refresh tokens."""
    def dispatch(self, request, *args, **kwargs):
        response = super().dispatch(request, *args, **kwargs)
        if request.user.is_authenticated:
            try:
                for token in OutstandingToken.objects.filter(user=request.user):
                    BlacklistedToken.objects.get_or_create(token=token)
            except Exception:
                pass  # Don't break logout if blacklist fails
        # Audit logout
        try:
            client_ip = request.META.get('REMOTE_ADDR')
            user_agent = request.META.get('HTTP_USER_AGENT', '')
            if request.user.is_authenticated:
                SecurityAuditLog.log_event(request.user, 'logout', client_ip or '0.0.0.0', user_agent)
        except Exception:
            pass
        return response

def custom_logout(request):
    logout(request)
    return render(request, 'users/logged_out.html')

class ProfileView(LoginRequiredMixin, SuccessMessageMixin, UpdateView):
    model = Profile
    form_class = ProfileForm
    template_name = 'users/profile.html'
    success_url = reverse_lazy('users:profile')
    success_message = _("Profile updated successfully")

    def get_object(self):
        # Robust: create profile if missing
        user = self.request.user
        try:
            return user.profile
        except Profile.DoesNotExist:
            # Option 1: Create the profile automatically
            profile = Profile.objects.create(user=user)
            return profile
            # Option 2: Show a user-friendly error instead:
            # from django.http import Http404
            # raise Http404("Profile not found for this user. Please contact support.")

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

    def get_organization(self):
        return self.request.user.organization

    def get_queryset(self):
        queryset = super().get_queryset()
        organization = self.request.user.organization
        queryset = queryset.filter(
            Q(organization=organization) |
            Q(organization_memberships__organization=organization)
        ).select_related('profile').prefetch_related('organization_memberships').distinct()

        q = self.request.GET.get('q')
        if q:
            queryset = queryset.filter(
                Q(email__icontains=q) |
                Q(first_name__icontains=q) |
                Q(last_name__icontains=q)
            )

        role = self.request.GET.get('role')
        if role:
            queryset = queryset.filter(role=role)

        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['can_create_users'] = self.request.user.role == CustomUser.ROLE_ADMIN
        return context

class UserDetailView(UserPermissionMixin, DetailView):
    model = CustomUser
    template_name = 'users/user_detail.html'
    context_object_name = 'user'

    def get_queryset(self):
        return super().get_queryset().select_related('profile')

    def get_organization(self):
        return self.get_object().organization

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['can_create_users'] = self.request.user.role == CustomUser.ROLE_ADMIN
        return context

class UserUpdateView(UserPermissionMixin, SuccessMessageMixin, UpdateView):
    model = CustomUser
    form_class = CustomUserChangeForm
    template_name = 'users/user_form.html'
    success_message = _("User updated successfully")

    def get_success_url(self):
        return reverse_lazy('users:user-detail', kwargs={'pk': self.object.pk})

    def get_organization(self):
        return self.get_object().organization

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['can_create_users'] = self.request.user.role == CustomUser.ROLE_ADMIN
        return context

class UserDeleteView(UserPermissionMixin, SuccessMessageMixin, DeleteView):
    model = CustomUser
    template_name = 'users/user_confirm_delete.html'
    success_url = reverse_lazy('users:user-list')
    success_message = _("User deleted successfully")

    def get_organization(self):
        # Provide organization context for OrganizationPermissionMixin
        return self.get_object().organization

    def delete(self, request, *args, **kwargs):
        if self.get_object() == request.user:
            raise PermissionDenied(_("You cannot delete your own account"))
        
        # Check if user has permission to delete users
        if not request.user.can_delete_users():
            raise PermissionDenied(_("You do not have permission to delete users. Only superusers can delete users."))
            
        user = self.get_object()
        
        try:
            with transaction.atomic():
                # First, delete any tenant-specific data in the user's organization schema
                if user.organization:
                    from django_tenants.utils import tenant_context
                    with tenant_context(user.organization):
                        # Delete audit-related records first
                        from audit.models import Approval
                        Approval.objects.filter(
                            Q(requester=user) | Q(approver=user)
                        ).delete()
                
                # Now delete the user from the public schema
                return super().delete(request, *args, **kwargs)
        except IntegrityError:
            messages.error(
                request,
                _(
                    "This user cannot be deleted because it is referenced by other records (e.g., audit logs, risk controls). "
                    "Please reassign or clean up related references, or use the supported data cleanup command/view."
                ),
            )
            return redirect('users:user-detail', pk=user.pk)

class AdminUserCreateView(UserPermissionMixin, SuccessMessageMixin, CreateView):
    """
    View for admin users to create new users within their organization.
    Only users with admin role can access this view.
    """
    model = CustomUser
    form_class = AdminUserCreationForm
    template_name = 'users/admin_user_form.html'
    success_url = reverse_lazy('users:user-list')
    success_message = _("User created successfully. They will receive an email to complete their account setup.")

    def dispatch(self, request, *args, **kwargs):
        # Check if user has admin role
        if request.user.role != CustomUser.ROLE_ADMIN:
            raise PermissionDenied(_("Only admin users can create new users."))
        return super().dispatch(request, *args, **kwargs)

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['organization'] = self.request.user.organization
        return kwargs

    def form_valid(self, form):
        # Set the organization to the current user's organization
        form.instance.organization = self.request.user.organization
        form.instance.is_admin_created = True
        form.instance.is_first_time_setup_complete = False
        
        response = super().form_valid(form)
        
        # Store the initial password in history
        PasswordHistory.store_password(form.instance, form.instance.password)
        
        # Profile and OTP are automatically created by signals
        # No need to create them manually here
        
        # Send welcome email
        try:
            from .tasks import send_welcome_email
            send_welcome_email.delay(form.instance.id, form.instance.email, form.instance.username)
        except Exception as e:
            # Log error but don't fail the user creation
            pass
        
        return response

    def get_organization(self):
        return self.request.user.organization

# ─── PASSWORD MANAGEMENT VIEWS ──────────────────────────────────────────────
@method_decorator(login_required, name='dispatch')
class UserPasswordChangeView(PasswordChangeView):
    """Blacklists all tokens on password change."""
    template_name = 'users/password_change.html'
    success_url = reverse_lazy('users:password_change_done')

    def form_valid(self, form):
        user = self.request.user
        new_password = form.cleaned_data['new_password1']
        
        # Store current password in history before changing it
        PasswordHistory.store_password(user, user.password, reason='change', is_hashed=True)
        
        response = super().form_valid(form)
        
        # Store new password in history
        PasswordHistory.store_password(user, new_password, reason='change')
        
        # Cleanup old password history
        PasswordHistory.cleanup_old_passwords(user)
        
        if self.request.user.is_authenticated:
            try:
                for token in OutstandingToken.objects.filter(user=self.request.user):
                    BlacklistedToken.objects.get_or_create(token=token)
            except Exception:
                pass
        return response

@method_decorator(login_required, name='dispatch')
class UserPasswordChangeDoneView(PasswordChangeDoneView):
    template_name = 'users/password_change_done.html'

class UserPasswordResetView(PasswordResetView):
    template_name = 'users/password_reset.html'
    email_template_name = 'users/password_reset_email.html'
    subject_template_name = 'users/password_reset_subject.txt'
    success_url = reverse_lazy('users:password_reset_done')
    
    def get_queryset(self):
        """
        Only allow password resets for users in the current organization
        and only for properly set up accounts (not admin-created accounts)
        """
        # Get the current organization from the request
        current_organization = getattr(self.request, 'organization', None)
        
        if not current_organization:
            # If no organization context, return empty queryset
            return CustomUser.objects.none()
        
        # Only allow resets for users in the current organization
        # AND only for users who have completed first-time setup (not admin-created accounts)
        return CustomUser.objects.filter(
            organization=current_organization,
            is_admin_created=False,  # Only allow resets for properly set up accounts
            is_active=True  # Only allow resets for active accounts
        )
    
    def get_email_context(self, user):
        """
        Override to ensure reset links go to the correct tenant domain
        """
        context = super().get_email_context(user)
        
        # Get the user's organization domain
        user_organization = user.organization
        if user_organization and hasattr(user_organization, 'domain'):
            # Use the user's organization domain for the reset link
            # This ensures the reset link goes to the correct tenant
            context['domain'] = user_organization.domain
            context['site_name'] = user_organization.name
        
        return context
    
    def form_valid(self, form):
        """
        Override to add additional security checks and send marketing emails to non-existent accounts
        """
        email = form.cleaned_data['email']
        
        # Check if the email belongs to a user in the current organization
        current_organization = getattr(self.request, 'organization', None)
        
        if current_organization:
            try:
                user = CustomUser.objects.get(
                    email=email,
                    organization=current_organization,
                    is_admin_created=False,  # Only allow resets for properly set up accounts
                    is_active=True  # Only allow resets for active accounts
                )
                # User exists and is valid for password reset
                return super().form_valid(form)
            except CustomUser.DoesNotExist:
                # User doesn't exist in this organization - send marketing email
                self.send_marketing_email(email)
                # Show generic success message for security
                messages.success(self.request, _("If an account with that email exists, you will receive password reset instructions."))
                return super().form_valid(form)
        else:
            # No organization context - check if email exists anywhere in the system
            try:
                user = CustomUser.objects.get(
                    email=email,
                    is_admin_created=False,  # Only allow resets for properly set up accounts
                    is_active=True  # Only allow resets for active accounts
                )
                # User exists somewhere - send normal password reset
                return super().form_valid(form)
            except CustomUser.DoesNotExist:
                # User doesn't exist anywhere - send marketing email
                self.send_marketing_email(email)
                # Show generic success message for security
                messages.success(self.request, _("If an account with that email exists, you will receive password reset instructions."))
                return super().form_valid(form)
    
    def send_marketing_email(self, email):
        """
        Send a high-quality marketing flyer to non-existent email addresses
        """
        try:
            from django.template.loader import render_to_string
            from django.core.mail import send_mail
            from django.conf import settings
            
            # Render the marketing email templates
            html_message = render_to_string('users/email/marketing_flyer.html')
            text_message = render_to_string('users/email/marketing_flyer.txt')
            
            # Send the marketing email
            send_mail(
                subject='Welcome to Oreno GRC - Enterprise Governance, Risk & Compliance Platform',
                message=text_message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[email],
                html_message=html_message,
                fail_silently=True,  # Don't raise errors for marketing emails
            )
            
            # Log the marketing email for analytics
            import logging
            logger = logging.getLogger(__name__)
            logger.info(f"Marketing email sent to non-existent account: {email}")
            
        except Exception as e:
            # Log any errors but don't break the password reset flow
            import logging
            logger = logging.getLogger(__name__)
            logger.error(f"Failed to send marketing email to {email}: {e}")

class UserPasswordResetDoneView(PasswordResetDoneView):
    template_name = 'users/password_reset_done.html'

class UserPasswordResetConfirmView(PasswordResetConfirmView):
    template_name = 'users/password_reset_confirm.html'
    success_url = reverse_lazy('users:password_reset_complete')
    form_class = CustomSetPasswordForm
    
    def get_user(self, uidb64):
        """
        Override to ensure only users from the correct organization can reset passwords
        """
        try:
            # Get the user from the token
            user = super().get_user(uidb64)
            
            # Get the current organization from the request
            current_organization = getattr(self.request, 'organization', None)
            
            # If we have organization context, verify the user belongs to this organization
            if current_organization and user.organization != current_organization:
                # User doesn't belong to the current organization
                # Return None to indicate invalid user
                return None
            
            # Also verify the user is properly set up and active
            if user.is_admin_created or not user.is_active:
                # User is not properly set up or not active
                return None
            
            return user
            
        except (TypeError, ValueError, OverflowError, CustomUser.DoesNotExist):
            return None
    
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs['user'] = self.user
        return kwargs
    
    def form_valid(self, form):
        # Get the user from the form
        user = form.save()
        
        # Store the new password in history
        new_password = form.cleaned_data['new_password1']
        PasswordHistory.store_password(user, new_password, reason='reset')
        
        # Cleanup old password history
        PasswordHistory.cleanup_old_passwords(user)
        
        return super().form_valid(form)

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

# Example: restrict user list API to org admins only
class UserListAPIView(OrganizationScopedQuerysetMixin, generics.ListAPIView):
    serializer_class = UserSerializer
    permission_classes = [permissions.IsAuthenticated, IsOrgAdmin]
    def get_queryset(self):
        org = self.request.user.organization
        return CustomUser.objects.filter(organization=org)

