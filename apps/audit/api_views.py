from django.http import JsonResponse
from django.db.models import Q, Count, Sum, Avg
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
import logging

from .models import Risk, Objective
from .serializers import RiskSerializer, RiskDetailSerializer
from .mixins import OrganizationScopedApiMixin, IsInOrganizationPermission

logger = logging.getLogger(__name__)

class NotificationsAPIView(APIView):
    """
    API view for notifications that gracefully handles unauthenticated requests
    by returning an empty array instead of redirecting to the login page.
    """
    permission_classes = []  # No permissions required - we'll handle authentication manually

    def get(self, request, *args, **kwargs):
        # If user is not authenticated, return an empty array
        if not request.user.is_authenticated:
            logger.debug("NotificationsAPIView: Returning empty array for unauthenticated user")
            return Response([], status=status.HTTP_200_OK)
        
        # For authenticated users, get organization-scoped notifications
        active_organization = getattr(request.user, 'active_organization', None)
        if not active_organization:
            # No active organization, return empty array
            return Response([], status=status.HTTP_200_OK)
            
        # This is a placeholder that will be replaced with actual notification fetching logic
        # In a real implementation, filter notifications by organization
        notifications = []  # In a real implementation, this would be fetched from the database
        
        return Response(notifications, status=status.HTTP_200_OK)


class RiskDashboardAPIView(OrganizationScopedApiMixin, APIView):
    """
    API view that provides risk dashboard metrics and analytics.
    Data includes risk distributions by category, status, and risk levels.
    Uses OrganizationScopedApiMixin for consistent organization filtering.
    """
    permission_classes = [IsAuthenticated, IsInOrganizationPermission]
    
    def get(self, request, *args, **kwargs):
        # Get the user's organization (already validated by IsInOrganizationPermission)
        organization = request.user.active_organization
        
        # Filter risks by organization using standard filtering pattern
        risks = Risk.objects.filter(organization=organization)
        
        # Risk distribution by category
        category_distribution = risks.values('category').annotate(
            count=Count('id')
        ).order_by('category')
        
        # Risk distribution by status
        status_distribution = risks.values('status').annotate(
            count=Count('id')
        ).order_by('status')
        
        # Risk distribution by inherent risk level
        risk_level_counts = {
            'High': risks.filter(inherent_risk_score__gte=7).count(),
            'Medium': risks.filter(inherent_risk_score__gte=3, inherent_risk_score__lte=6).count(),
            'Low': risks.filter(inherent_risk_score__lte=2).count()
        }
        
        # Risk distribution by residual risk level
        residual_level_counts = {
            'High': risks.filter(residual_risk_score__gte=7).count(),
            'Medium': risks.filter(residual_risk_score__gte=3, residual_risk_score__lte=6).count(),
            'Low': risks.filter(residual_risk_score__lte=2).count()
        }
        
        # Overall risk metrics
        avg_inherent_score = risks.aggregate(Avg('inherent_risk_score'))['inherent_risk_score__avg'] or 0
        avg_residual_score = risks.aggregate(Avg('residual_risk_score'))['residual_risk_score__avg'] or 0
        risk_reduction = 0
        if avg_inherent_score > 0:
            risk_reduction = ((avg_inherent_score - avg_residual_score) / avg_inherent_score) * 100
        
        dashboard_data = {
            'category_distribution': category_distribution,
            'status_distribution': status_distribution,
            'risk_level_counts': risk_level_counts,
            'residual_level_counts': residual_level_counts,
            'metrics': {
                'total_risks': risks.count(),
                'avg_inherent_score': round(avg_inherent_score, 2),
                'avg_residual_score': round(avg_residual_score, 2),
                'risk_reduction_percentage': round(risk_reduction, 2)
            }
        }
        
        return Response(dashboard_data)


@api_view(['GET'])
@permission_classes([IsAuthenticated, IsInOrganizationPermission])
def objective_risks_api(request, objective_id):
    """
    API endpoint that returns all risks for a specific objective.
    Useful for populating dashboards or objective-specific risk reports.
    Enforces organization scoping via IsInOrganizationPermission.
    """
    try:
        # Get objective with organization filter applied
        objective = Objective.objects.filter(
            organization=request.user.active_organization
        ).get(pk=objective_id)
        
        # Get risks for this objective with organization filter
        risks = Risk.objects.filter(
            objective=objective,
            organization=request.user.active_organization
        )
        serializer = RiskSerializer(risks, many=True)
        
        return Response(serializer.data)
    except Objective.DoesNotExist:
        return Response({"error": "Objective not found"}, status=status.HTTP_404_NOT_FOUND)
