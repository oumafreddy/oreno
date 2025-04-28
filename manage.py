#!/usr/bin/env python
# manage.py

import os
import sys
from pathlib import Path

def main():
    # Build paths inside the project
    BASE_DIR = Path(__file__).resolve().parent

    # Add the project directory to the sys.path
    sys.path.append(str(BASE_DIR))

    # Ensure Django runs with tenant-aware settings by default
    os.environ.setdefault(
        'DJANGO_SETTINGS_MODULE',
        os.environ.get('DJANGO_SETTINGS_MODULE', 'config.settings.development')
    )
    try:
        from django.core.management import execute_from_command_line
    except ImportError as exc:
        raise ImportError(
            "Couldn't import Django. Are you sure it's installed and "
            "available on your PYTHONPATH environment variable? Did you "
            "forget to activate a virtual environment?"
        ) from exc
    execute_from_command_line(sys.argv)

if __name__ == '__main__':
    main()
