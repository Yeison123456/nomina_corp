from django.contrib import admin

from .models import Concepto, DetalleLiquidacion, LiquidacionContrato, LiquidacionNomina, Novedad, PeriodoNomina, Prestamo


@admin.register(Concepto)
class ConceptoAdmin(admin.ModelAdmin):
    list_display = ("codigo", "nombre", "tipo", "captura", "salarial", "base_seguridad_social", "base_prestaciones", "activo")
    list_filter = ("tipo", "captura")


@admin.register(PeriodoNomina)
class PeriodoAdmin(admin.ModelAdmin):
    list_display = ("__str__", "periodicidad", "fecha_inicio", "fecha_fin", "estado")
    list_filter = ("estado", "periodicidad", "anio")


class DetalleInline(admin.TabularInline):
    model = DetalleLiquidacion
    extra = 0


@admin.register(LiquidacionNomina)
class LiquidacionAdmin(admin.ModelAdmin):
    list_display = ("periodo", "contrato", "total_devengado", "total_deducciones", "neto_pagar")
    list_filter = ("periodo",)
    inlines = [DetalleInline]


admin.site.register(Novedad)
admin.site.register(Prestamo)
admin.site.register(LiquidacionContrato)
