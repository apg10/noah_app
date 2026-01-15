# backend/urls.py o noah_food/urls.py
from django.contrib import admin
from django.urls import path, include
from core.views import healthz, readyz

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/", include("core.urls")),
     # Probes para Kubernetes
    path("healthz/", healthz, name="healthz"),
    path("readyz/", readyz, name="readyz"),
]
