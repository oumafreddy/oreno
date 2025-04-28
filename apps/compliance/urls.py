from django.urls import path
from rest_framework.routers import DefaultRouter

app_name = 'compliance'

# Basic URL patterns for compliance app
urlpatterns = [
    # Add your compliance URLs here
]

# API router for compliance endpoints
router = DefaultRouter()
# Register your compliance API viewsets here

# Include API URLs
urlpatterns += router.urls
