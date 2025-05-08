# apps/compliance/apps.py
from django.apps import AppConfig

class ComplianceConfig(AppConfig):
    name = 'compliance'
    verbose_name = "Compliance"
    # …or…
    # name = 'apps.core'  # if you prefer fully qualified imports without altering sys.path
