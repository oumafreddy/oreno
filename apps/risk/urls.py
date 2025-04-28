from django.urls import path
from rest_framework.routers import DefaultRouter

app_name = 'risk'

# Basic URL patterns for risk app
urlpatterns = [
    # Add your risk URLs here
]

# API router for risk endpoints
router = DefaultRouter()
# Register your risk API viewsets here

# Include API URLs
urlpatterns += router.urls
