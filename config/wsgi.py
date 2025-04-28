import os
import sys
import logging
from django.core.wsgi import get_wsgi_application

# Ensure the project root is on PYTHONPATH
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Use tenant-aware settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.tenants')

# Set up Django's WSGI application (loads your MIDDLEWARE from settings)
application = get_wsgi_application()

# Optional: Health-check endpoint as simple WSGI middleware
class HealthCheckMiddleware:
    def __init__(self, app):
        self.app = app

    def __call__(self, environ, start_response):
        if environ.get('PATH_INFO') == '/health/':
            start_response('200 OK', [('Content-Type', 'text/plain')])
            return [b'OK']
        return self.app(environ, start_response)

application = HealthCheckMiddleware(application)

# Optional: Error-handling wrapper for uncaught exceptions
class WSGIErrorHandler:
    def __init__(self, app):
        self.app = app
        self.logger = logging.getLogger(__name__)

    def __call__(self, environ, start_response):
        try:
            return self.app(environ, start_response)
        except Exception as e:
            self.logger.exception("WSGI Error:")
            start_response('500 Internal Server Error', [('Content-Type', 'text/plain')])
            return [b'Internal Server Error']

application = WSGIErrorHandler(application)
