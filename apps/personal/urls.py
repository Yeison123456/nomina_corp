from django.urls import path

from . import views

app_name = "personal"

urlpatterns = [
    path("empleados/", views.empleados_lista, name="empleados"),
    path("empleados/nuevo/", views.empleado_editar, name="empleado_nuevo"),
    path("empleados/<int:pk>/", views.empleado_detalle, name="empleado"),
    path("empleados/<int:pk>/editar/", views.empleado_editar, name="empleado_editar"),
    path("empleados/<int:empleado_pk>/contratos/nuevo/", views.contrato_editar, name="contrato_nuevo"),
    path("empleados/<int:empleado_pk>/contratos/<int:pk>/", views.contrato_editar, name="contrato_editar"),
    path("estructura/", views.estructura, name="estructura"),
    path("estructura/centros/nuevo/", views.centro_editar, name="centro_nuevo"),
    path("estructura/centros/<int:pk>/", views.centro_editar, name="centro_editar"),
    path("estructura/areas/nueva/", views.area_editar, name="area_nueva"),
    path("estructura/areas/<int:pk>/", views.area_editar, name="area_editar"),
    path("estructura/cargos/nuevo/", views.cargo_editar, name="cargo_nuevo"),
    path("estructura/cargos/<int:pk>/", views.cargo_editar, name="cargo_editar"),
]
