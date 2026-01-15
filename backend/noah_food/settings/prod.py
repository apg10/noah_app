from .base import *  # noqa

DEBUG = False

# En prod NUNCA uses "*".
# Debes setear DJANGO_ALLOWED_HOSTS con dominios reales.
if ALLOWED_HOSTS == ["*"]:
    raise RuntimeError("DJANGO_ALLOWED_HOSTS='*' está prohibido en producción.")

# Recomendado cuando estés detrás de Ingress con HTTPS:
# (habilitar por env cuando ya tengas TLS)
# DJANGO_USE_PROXY_HEADERS=1
# DJANGO_SECURE_SSL_REDIRECT=1
# DJANGO_SESSION_COOKIE_SECURE=1
# DJANGO_CSRF_COOKIE_SECURE=1
