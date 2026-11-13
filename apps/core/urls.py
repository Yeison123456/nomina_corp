from django.contrib.auth import views as auth_views
from django.urls import path

from . import views

app_name = "core"

urlpatterns = [
    path("ingresar/", views.Ingresar.as_view(), name="login"),
    path("salir/", auth_views.LogoutView.as_view(), name="logout"),
    path("", views.tablero, name="tablero"),
    path("configuracion/empresa/", views.empresa_ver, name="empresa"),
    path("configuracion/empresa/editar/", views.empresa_editar, name="empresa_editar"),
    path("configuracion/parametros/", views.parametros_lista, name="parametros"),
    path("configuracion/parametros/nuevo/", views.parametro_editar, name="parametro_nuevo"),
    path("configuracion/parametros/<int:pk>/", views.parametro_editar, name="parametro_editar"),
    path("configuracion/entidades/", views.entidades_lista, name="entidades"),
    path("configuracion/entidades/nueva/", views.entidad_editar, name="entidad_nueva"),
    path("configuracion/entidades/<int:pk>/", views.entidad_editar, name="entidad_editar"),
    path("configuracion/usuarios/", views.usuarios_lista, name="usuarios"),
    path("configuracion/usuarios/nuevo/", views.usuario_editar, name="usuario_nuevo"),
    path("configuracion/usuarios/<int:pk>/", views.usuario_editar, name="usuario_editar"),
    path("configuracion/auditoria/", views.auditoria_lista, name="auditoria"),
]
