from django.urls import path

from . import views

app_name = "nomina"

urlpatterns = [
    path("periodos/", views.periodos_lista, name="periodos"),
    path("periodos/nuevo/", views.periodo_nuevo, name="periodo_nuevo"),
    path("periodos/<int:pk>/", views.periodo_detalle, name="periodo"),
    path("periodos/<int:pk>/liquidar/", views.periodo_liquidar, name="periodo_liquidar"),
    path("periodos/<int:pk>/cerrar/", views.periodo_cerrar, name="periodo_cerrar"),
    path("periodos/<int:pk>/reabrir/", views.periodo_reabrir, name="periodo_reabrir"),
    path("periodos/<int:pk>/eliminar/", views.periodo_eliminar, name="periodo_eliminar"),
    path("periodos/<int:pk>/desprendibles.pdf", views.desprendibles_periodo, name="desprendibles_periodo"),
    path("periodos/<int:pk>/sabana.xlsx", views.sabana, name="sabana"),
    path("liquidaciones/<int:pk>/", views.liquidacion_detalle, name="liquidacion"),
    path("liquidaciones/<int:pk>/desprendible.pdf", views.desprendible, name="desprendible"),
    path("novedades/", views.novedades_lista, name="novedades"),
    path("novedades/nueva/", views.novedad_editar, name="novedad_nueva"),
    path("novedades/<int:pk>/", views.novedad_editar, name="novedad_editar"),
    path("novedades/<int:pk>/anular/", views.novedad_anular, name="novedad_anular"),
    path("prestamos/", views.prestamos_lista, name="prestamos"),
    path("prestamos/nuevo/", views.prestamo_nuevo, name="prestamo_nuevo"),
    path("prestamos/<int:pk>/anular/", views.prestamo_anular, name="prestamo_anular"),
    path("conceptos/", views.conceptos_lista, name="conceptos"),
    path("retiros/", views.liquidaciones_contrato, name="liquidaciones_contrato"),
    path("retiros/nueva/", views.liquidacion_contrato_nueva, name="liquidacion_contrato_nueva"),
    path("retiros/<int:pk>/", views.liquidacion_contrato_detalle, name="liquidacion_contrato"),
    path("retiros/<int:pk>/pdf/", views.liquidacion_contrato_pdf, name="liquidacion_contrato_pdf"),
    path("retiros/<int:pk>/aprobar/", views.liquidacion_contrato_aprobar, name="liquidacion_contrato_aprobar"),
    path("retiros/<int:pk>/eliminar/", views.liquidacion_contrato_eliminar, name="liquidacion_contrato_eliminar"),
    path("reportes/", views.reportes, name="reportes"),
]
