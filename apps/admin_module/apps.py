# apps/admin_module/apps.py
from django.apps import AppConfig

class AdminModuleConfig(AppConfig):
    name = 'admin_module'
    verbose_name = "Admin Module"
    # …or…
    # name = 'apps.core'  # if you prefer fully qualified imports without altering sys.path
