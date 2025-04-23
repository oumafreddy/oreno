# apps/admin_module/apps.py
from django.apps import AppConfig

class AdminModuleConfig(AppConfig):
    name = 'admin_module'        # if using sys.path hack and __init__.py added
    # …or…
    # name = 'apps.core'  # if you prefer fully qualified imports without altering sys.path
