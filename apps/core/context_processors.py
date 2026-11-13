from django.conf import settings

from .models import Empresa
from .roles import ADMIN, ESCRITURA, rol_de


def contexto_global(request):
    rol = rol_de(request.user) if hasattr(request, "user") else None
    return {
        "empresa_actual": Empresa.actual(),
        "producto": settings.LIBRA_NOMBRE_PRODUCTO,
        "version": settings.LIBRA_VERSION,
        "rol_usuario": rol,
        "puede_editar": rol in ESCRITURA,
        "es_admin": rol == ADMIN,
    }
