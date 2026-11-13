from decimal import Decimal, InvalidOperation

from django import template
from django.utils.html import format_html

register = template.Library()


@register.filter
def pesos(valor):
    """1234567.5 → $ 1.234.568"""
    try:
        valor = Decimal(valor or 0)
    except (InvalidOperation, TypeError):
        return valor
    signo = "−" if valor < 0 else ""
    return f"{signo}$ {abs(valor):,.0f}".replace(",", ".")


@register.filter
def numero(valor, decimales=0):
    try:
        valor = Decimal(valor or 0)
    except (InvalidOperation, TypeError):
        return valor
    decimales = int(decimales)
    if decimales == 0 and valor != valor.to_integral():
        decimales = 2
    texto = f"{valor:,.{decimales}f}"
    return texto.replace(",", "X").replace(".", ",").replace("X", ".")


@register.filter
def porcentaje(valor, decimales=2):
    try:
        valor = Decimal(valor or 0) * 100
    except (InvalidOperation, TypeError):
        return valor
    texto = f"{valor:.{int(decimales)}f}".rstrip("0").rstrip(".")
    return texto.replace(".", ",") + " %"


ESTADOS = {
    # periodos
    "BOR": "abierto", "LIQ": "liquidado", "CER": "cerrado",
    # novedades
    "PEN": "pendiente", "APL": "aplicada", "ANU": "anulada",
    # contratos y préstamos
    "VIG": "vigente", "TER": "terminado", "ACT": "activo", "PAG": "pagado",
    # liquidaciones de contrato
    "APR": "aprobada",
}


@register.simple_tag
def estado(codigo, texto):
    clase = ESTADOS.get(codigo, "neutro")
    return format_html('<span class="estado estado--{}">{}</span>', clase, texto)


@register.inclusion_tag("comun/_campo.html")
def campo(field, ancho=""):
    return {"field": field, "ancho": ancho}


@register.filter
def get(diccionario, clave):
    return diccionario.get(clave) if hasattr(diccionario, "get") else None


@register.simple_tag(takes_context=True)
def activo(context, prefijo):
    """Devuelve 'activo' si la ruta actual corresponde a la entrada del menú."""
    ruta = context["request"].path
    if prefijo == "/":
        return "activo" if ruta == "/" else ""
    return "activo" if ruta.startswith(prefijo) else ""


@register.filter
def iniciales(texto):
    partes = str(texto).split()
    return "".join(p[0] for p in partes[:2]).upper()
