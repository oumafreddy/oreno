# apps/core/mixins.py
from rest_framework import viewsets
from rest_framework.permissions import IsAuthenticated
from django.views.generic import ListView, DetailView
from django.contrib.auth.mixins import LoginRequiredMixin

class OrganizationQuerysetMixin:
    """
    Restricts the queryset to the current request.organization.
    Must be mixed-in before the viewset class.
    """

    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        # 1. Start with the base queryset
        qs = super().get_queryset()  # :contentReference[oaicite:0]{index=0}
        # 2. Grab the org from the middleware
        org = getattr(self.request, 'organization', None)
        if org is None:
            # No organization in context → deny access
            return qs.none()
        # 3. Filter by FK ‘organization’
        return qs.filter(organization=org)  # :contentReference[oaicite:1]{index=1}

class OrganizationFilterMixin(LoginRequiredMixin):
    """
    Filters object lists and detail lookups by request.organization.
    """

    def get_queryset(self):
        qs = super().get_queryset()
        org = getattr(self.request, 'organization', None)
        return qs.filter(organization=org)  # :contentReference[oaicite:2]{index=2}