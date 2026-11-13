from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("admin/", admin.site.urls),
    path("", include("apps.core.urls")),
    path("personal/", include("apps.personal.urls")),
    path("nomina/", include("apps.nomina.urls")),
]

admin.site.site_header = "Libra — Administración técnica"
admin.site.site_title = "Libra"
