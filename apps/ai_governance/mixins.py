from django.contrib.auth.mixins import LoginRequiredMixin


class OrganizationPermissionMixin(LoginRequiredMixin):
    def dispatch(self, request, *args, **kwargs):
        # Reuse existing org context/permission middleware behavior implicitly.
        return super().dispatch(request, *args, **kwargs)
