"""
Shim de compatibilidad.

- Mantiene funcionando: manage.py runserver (sin exportar DJANGO_SETTINGS_MODULE)
- En Kubernetes/Docker profesional: usa DJANGO_SETTINGS_MODULE=noah_food.settings.dev|prod
"""
from noah_food.settings.dev import *  # noqa
