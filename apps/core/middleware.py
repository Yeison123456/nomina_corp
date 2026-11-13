from django.conf import settings
from django.shortcuts import redirect
from django.urls import reverse

RUTAS_PUBLICAS = ("/ingresar/", "/static/", "/admin/")


class LoginObligatorioMiddleware:
    """Exige sesión iniciada en todas las páginas excepto el ingreso y los estáticos."""

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        if not request.user.is_authenticated and not request.path.startswith(RUTAS_PUBLICAS):
            return redirect(f"{reverse(settings.LOGIN_URL)}?next={request.path}")
        return self.get_response(request)
