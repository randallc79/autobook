import os
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
import organizer.routing  # Add routing.py later

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'autobook.settings')

application = ProtocolTypeRouter({
    "http": get_asgi_application(),
    "websocket": AuthMiddlewareStack(
        URLRouter(organizer.routing.websocket_urlpatterns)
    ),
})
