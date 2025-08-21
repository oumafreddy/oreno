# apps/admin_module/apps.py
from django.apps import AppConfig

class AdminModuleConfig(AppConfig):
    name = 'admin_module'
    verbose_name = "Data Export Management"
    
    def ready(self):
        # Import admin configuration when the app is ready
        import admin_module.admin
