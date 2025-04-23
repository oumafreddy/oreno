# apps/risk/models.py
from django.db import models
from django_scopes import ScopesManager, scope

class Risk(models.Model):
    organization = models.ForeignKey('organizations.Organization', on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    # Use ScopesManager instead of default
    objects = ScopesManager()

    class Meta:
        scopes = {
            'organization': ['organization']
        }
