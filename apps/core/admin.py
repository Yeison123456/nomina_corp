from django.contrib import admin

from .models import Auditoria, Empresa, Entidad, ParametroLegal

admin.site.register(Empresa)
admin.site.register(ParametroLegal)


@admin.register(Entidad)
class EntidadAdmin(admin.ModelAdmin):
    list_display = ("nombre", "tipo", "nit", "activa")
    list_filter = ("tipo",)


@admin.register(Auditoria)
class AuditoriaAdmin(admin.ModelAdmin):
    list_display = ("fecha", "usuario", "accion", "objeto")
    list_filter = ("accion",)
    readonly_fields = ("fecha", "usuario", "accion", "objeto", "detalle")
