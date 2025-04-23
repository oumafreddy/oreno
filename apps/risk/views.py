# apps/risk/views.py

from django.views.generic import ListView, DetailView
from rest_framework import viewsets
from django_scopes import scope

from apps.core.middleware import get_current_organization
from apps.core.mixins import OrganizationQuerysetMixin, OrganizationFilterMixin
from .models import Risk
from .serializers import RiskSerializer


@scope(provider=get_current_organization, name="organization")
class RiskScopedViewSet(viewsets.ModelViewSet):
    """
    Option A: Row‑level isolation via django‑scopes.
    All queries automatically limited by the active organization scope.
    """
    queryset = Risk.objects.all()
    serializer_class = RiskSerializer


class RiskViewSet(OrganizationQuerysetMixin, viewsets.ModelViewSet):
    """
    Option B: Classic DRF mixin filtering.
    Filters `.queryset` to request.organization in get_queryset().
    """
    queryset = Risk.objects.all()
    serializer_class = RiskSerializer


class RiskListView(OrganizationFilterMixin, ListView):
    """
    Web listing of Risks, automatically filtered to request.organization.
    """
    model = Risk
    template_name = 'risk/risk_list.html'


class RiskDetailView(OrganizationFilterMixin, DetailView):
    """
    Web detail view of a single Risk, 404s if not in request.organization.
    """
    model = Risk
    template_name = 'risk/risk_detail.html'
