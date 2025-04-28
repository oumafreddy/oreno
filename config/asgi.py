import os
import logging
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
from channels.security.websocket import AllowedHostsOriginValidator

# Point to tenant settings
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'config.settings.tenants')

# Base Django ASGI application (loads HTTP-middleware from settings)
django_asgi_app = get_asgi_application()

# Define your WebSocket URL patterns here, e.g.:
# from your_app.routing import websocket_urlpatterns
websocket_urlpatterns = [
    # path("ws/notifications/", NotificationConsumer.as_asgi()),
]

# Build the protocol router
application = ProtocolTypeRouter({
    "http": django_asgi_app,
    "websocket": AllowedHostsOriginValidator(
        AuthMiddlewareStack(
            URLRouter(websocket_urlpatterns)
        )
    ),
})

# Optional: Health-check endpoint for ASGI
class ASGIHealthCheck:
    def __init__(self, app):
        self.app = app

    async def __call__(self, scope, receive, send):
        if scope['type'] == 'http' and scope.get('path') == '/health/':
            await send({
                'type': 'http.response.start',
                'status': 200,
                'headers': [(b'content-type', b'text/plain')],
            })
            await send({
                'type': 'http.response.body',
                'body': b'OK',
            })
        else:
            await self.app(scope, receive, send)

application = ASGIHealthCheck(application)

# Optional: ASGI error handler
class ASGIErrorHandler:
    def __init__(self, app):
        self.app = app
        self.logger = logging.getLogger(__name__)

    async def __call__(self, scope, receive, send):
        try:
            await self.app(scope, receive, send)
        except Exception as e:
            self.logger.exception("ASGI Error:")
            if scope['type'] == 'http':
                await send({
                    'type': 'http.response.start',
                    'status': 500,
                    'headers': [(b'content-type', b'text/plain')],
                })
                await send({
                    'type': 'http.response.body',
                    'body': b'Internal Server Error',
                })

application = ASGIErrorHandler(application)
