from django.http import JsonResponse
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
import logging

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
        
        # For authenticated users, you would normally get notifications from the database
        # This is a placeholder that will be replaced with actual notification fetching logic
        notifications = []  # In a real implementation, this would be fetched from the database
        
        return Response(notifications, status=status.HTTP_200_OK)
