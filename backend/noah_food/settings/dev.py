from .base import *  # noqa

DEBUG = True

# En dev es normal permitir '*' para evitar DisallowedHost en K8s local.
# Aun así, se puede override por env.
if os.getenv("DJANGO_ALLOWED_HOSTS", "").strip() == "":
    ALLOWED_HOSTS = ["*"]
