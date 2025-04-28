from django.urls import path
from rest_framework.routers import DefaultRouter

app_name = 'contracts'

# Basic URL patterns for contracts app
urlpatterns = [
    # Add your contracts URLs here
]

# API router for contracts endpoints
router = DefaultRouter()
# Register your contracts API viewsets here

# Include API URLs
urlpatterns += router.urls
