# apps/contracts/apps.py
from django.apps import AppConfig

class ContractsConfig(AppConfig):
    name = 'contracts'        # if using sys.path hack and __init__.py added
    # …or…
    # name = 'apps.core'  # if you prefer fully qualified imports without altering sys.path
