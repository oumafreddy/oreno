import os
import sys 
import django
from django.db import models

# Setup Django environment
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.append(BASE_DIR)
# Ensure local apps/ is importable so "organizations" resolves without the "apps." prefix
APPS_DIR = os.path.join(BASE_DIR, 'apps')
if APPS_DIR not in sys.path:
    sys.path.insert(0, APPS_DIR)
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.base')
django.setup()

from organizations.models import Organization  # type: ignore[import]


def set_org_active_status(org_identifier, is_active=True):
    """
    Activate or deactivate an organization by code or name.
    Args:
        org_identifier (str): Organization code or name.
        is_active (bool): True to activate, False to deactivate.
    """
    org = Organization.objects.filter(
        models.Q(code=org_identifier) | models.Q(name=org_identifier)
    ).first()
    if not org:
        print(f"Organization '{org_identifier}' not found.")
        return
    org.is_active = is_active
    org.save()
    status = 'activated' if is_active else 'deactivated'
    print(f"Organization '{org.name}' ({org.code}) has been {status}.")


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Activate or deactivate an organization.")
    parser.add_argument('org', help="Organization code or name")
    parser.add_argument('--deactivate', action='store_true', help="Deactivate the organization (default is activate)")
    args = parser.parse_args()
    set_org_active_status(args.org, is_active=not args.deactivate)

if __name__ == '__main__':
    main() 