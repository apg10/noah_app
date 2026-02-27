from .base import *  # noqa

DEBUG = True

# En dev es normal permitir '*' para evitar DisallowedHost en K8s local.
# Aun así, se puede override por env.
if os.getenv("DJANGO_ALLOWED_HOSTS", "").strip() == "":
    ALLOWED_HOSTS = ["*"]

# En desarrollo permitimos CORS abierto por defecto para probar frontend separado.
if (
    os.getenv("DJANGO_CORS_ALLOWED_ORIGINS", "").strip() == ""
    and os.getenv("DJANGO_CORS_ALLOW_ALL_ORIGINS", "").strip() == ""
):
    CORS_ALLOW_ALL_ORIGINS = True
