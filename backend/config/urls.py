from django.contrib import admin
from django.urls import include, path

from config.interfaces.http.healthcheck import healthcheck

urlpatterns = [
    path("admin/", admin.site.urls),
    path("api/payouts/", include("payouts.api.urls")),
    path("health/", healthcheck, name="healthcheck"),  
]
