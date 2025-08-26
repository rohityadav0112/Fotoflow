import os
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
import accounts.routing  # Import your app's routing file


os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'fotoflow.settings')


application = ProtocolTypeRouter({
    "http": get_asgi_application(),
    "websocket": AuthMiddlewareStack(  # Add authentication for WebSockets
        URLRouter(
            accounts.routing.websocket_urlpatterns
        )
    ),
})