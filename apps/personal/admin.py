from django.contrib import admin

from .models import Area, Cargo, CentroCosto, Contrato, Empleado

admin.site.register(CentroCosto)
admin.site.register(Area)
admin.site.register(Cargo)


class ContratoInline(admin.TabularInline):
    model = Contrato
    extra = 0
    fields = ("numero", "tipo", "salario", "cargo", "periodicidad", "fecha_inicio", "estado")


@admin.register(Empleado)
class EmpleadoAdmin(admin.ModelAdmin):
    list_display = ("numero_documento", "apellidos", "nombres", "activo")
    search_fields = ("numero_documento", "nombres", "apellidos")
    inlines = [ContratoInline]


@admin.register(Contrato)
class ContratoAdmin(admin.ModelAdmin):
    list_display = ("numero", "empleado", "tipo", "salario", "periodicidad", "estado")
    list_filter = ("estado", "periodicidad", "tipo")
