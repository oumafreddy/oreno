from django.urls import reverse_lazy
from django.views.generic import TemplateView, ListView, DetailView, UpdateView, FormView
from django.shortcuts import get_object_or_404, redirect
from users.models import CustomUser, OrganizationRole
from organizations.models import OrganizationSettings
from .forms import UserActivationForm, UserRoleForm, AdminOrganizationSettingsForm
from .mixins import OrgAdminRequiredMixin

class AdminDashboardView(OrgAdminRequiredMixin, TemplateView):
    template_name = 'admin_module/dashboard.html'
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        org = self.request.user.organization
        users = CustomUser.objects.filter(organization=org)
        context['user_count'] = users.count()
        context['active_user_count'] = users.filter(is_active=True).count()
        context['inactive_user_count'] = users.filter(is_active=False).count()
        context['admin_count'] = users.filter(role=CustomUser.ROLE_ADMIN).count()
        context['manager_count'] = users.filter(role=CustomUser.ROLE_MANAGER).count()
        context['staff_count'] = users.filter(role=CustomUser.ROLE_STAFF).count()
        context['recent_users'] = users.order_by('-date_joined')[:5]
        context['org_name'] = org.name
        context['org_code'] = org.code
        context['org_logo'] = org.logo.url if org.logo else None
        context['org_status'] = 'Active' if org.is_active else 'Inactive'
        context['subscription_plan'] = getattr(org.settings, 'subscription_plan', 'N/A')
        # For pie chart
        context['role_distribution'] = [
            {'role': 'Admin', 'count': context['admin_count']},
            {'role': 'Manager', 'count': context['manager_count']},
            {'role': 'Staff', 'count': context['staff_count']},
        ]
        return context

class AdminUserListView(OrgAdminRequiredMixin, ListView):
    model = CustomUser
    template_name = 'admin_module/user_list.html'
    context_object_name = 'users'
    def get_queryset(self):
        return CustomUser.objects.filter(organization=self.request.user.organization)

class AdminUserDetailView(OrgAdminRequiredMixin, DetailView):
    model = CustomUser
    template_name = 'admin_module/user_detail.html'
    context_object_name = 'user'
    def get_queryset(self):
        return CustomUser.objects.filter(organization=self.request.user.organization)

class AdminUserUpdateView(OrgAdminRequiredMixin, UpdateView):
    model = CustomUser
    fields = ['first_name', 'last_name', 'email', 'role']
    template_name = 'admin_module/user_form.html'
    success_url = reverse_lazy('admin_module:user-list')
    def get_queryset(self):
        return CustomUser.objects.filter(organization=self.request.user.organization)

class AdminUserActivationView(OrgAdminRequiredMixin, UpdateView):
    model = CustomUser
    form_class = UserActivationForm
    template_name = 'admin_module/user_activation_form.html'
    success_url = reverse_lazy('admin_module:user-list')
    def get_queryset(self):
        return CustomUser.objects.filter(organization=self.request.user.organization)

class AdminUserRoleUpdateView(OrgAdminRequiredMixin, UpdateView):
    model = OrganizationRole
    form_class = UserRoleForm
    template_name = 'admin_module/user_role_form.html'
    success_url = reverse_lazy('admin_module:user-list')
    def get_queryset(self):
        return OrganizationRole.objects.filter(organization=self.request.user.organization)

class AdminOrgSettingsUpdateView(OrgAdminRequiredMixin, UpdateView):
    model = OrganizationSettings
    form_class = AdminOrganizationSettingsForm
    template_name = 'admin_module/org_settings_form.html'
    success_url = reverse_lazy('admin_module:dashboard')
    def get_object(self):
        return get_object_or_404(OrganizationSettings, organization=self.request.user.organization)
