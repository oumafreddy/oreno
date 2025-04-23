# apps/compliance/apps.py
from django.apps import AppConfig

class ComplianceConfig(AppConfig):
    name = 'compliance'        # if using sys.path hack and __init__.py added
    # …or…
    # name = 'apps.core'  # if you prefer fully qualified imports without altering sys.path
