"""
Roles de usuario. Se implementan con grupos de Django:

* Administrador      — todo, incluidos cierre de periodos, parámetros y usuarios.
* Analista de nómina — personal, novedades, préstamos, liquidación (sin cierre).
* Consulta           — solo lectura.
"""
from functools import wraps

from django.contrib import messages
from django.shortcuts import redirect

ADMIN = "Administrador"
ANALISTA = "Analista de nómina"
CONSULTA = "Consulta"
ROLES = [ADMIN, ANALISTA, CONSULTA]

ESCRITURA = (ADMIN, ANALISTA)


def rol_de(usuario) -> str | None:
    if not usuario.is_authenticated:
        return None
    if usuario.is_superuser:
        return ADMIN
    nombres = set(usuario.groups.values_list("name", flat=True))
    for rol in ROLES:
        if rol in nombres:
            return rol
    return CONSULTA


def tiene_rol(usuario, *roles) -> bool:
    return rol_de(usuario) in roles


def requiere_rol(*roles):
    """Decorador de vistas: restringe el acceso a los roles indicados."""

    def decorador(vista):
        @wraps(vista)
        def envoltura(request, *args, **kwargs):
            if not tiene_rol(request.user, *roles):
                messages.error(request, "Su rol no tiene permiso para realizar esta acción.")
                return redirect(request.META.get("HTTP_REFERER") or "core:tablero")
            return vista(request, *args, **kwargs)

        return envoltura

    return decorador
