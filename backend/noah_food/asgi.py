import os
from channels.routing import ProtocolTypeRouter, URLRouter
from django.core.asgi import get_asgi_application
from django.urls import path

os.environ.setdefault(
    "DJANGO_SETTINGS_MODULE",
    os.getenv("DJANGO_SETTINGS_MODULE", "noah_food.settings"),
)

django_asgi_app = get_asgi_application()

# Placeholder: cuando implementes websockets, aquí conectas tus rutas reales.
websocket_urlpatterns = [
    # path("ws/...", Consumer.as_asgi()),
]

application = ProtocolTypeRouter({
    "http": django_asgi_app,
    "websocket": URLRouter(websocket_urlpatterns),
})
