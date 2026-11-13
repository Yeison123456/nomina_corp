"""Utilidades compartidas por las vistas de todos los módulos."""
from django.contrib import messages
from django.core.paginator import Paginator
from django.shortcuts import redirect, render

from .auditoria import registrar


def formulario(request, form_class, *, instance=None, titulo, volver, exito=None,
               plantilla="comun/formulario.html", contexto=None, initial=None, form_kwargs=None):
    """
    Muestra y procesa un formulario de modelo. Registra la acción en auditoría
    y redirige a `exito` (o a `volver`) al guardar.
    """
    form_kwargs = form_kwargs or {}
    if request.method == "POST":
        form = form_class(request.POST, instance=instance, **form_kwargs)
        if form.is_valid():
            obj = form.save()
            registrar(request.user, "EDITAR" if instance else "CREAR", obj)
            messages.success(request, "Los cambios se guardaron correctamente.")
            destino = exito(obj) if callable(exito) else (exito or volver)
            return redirect(destino)
        messages.error(request, "Revise los campos marcados.")
    else:
        form = form_class(instance=instance, initial=initial, **form_kwargs)
    ctx = {"form": form, "titulo": titulo, "volver": volver, "objeto": instance}
    ctx.update(contexto or {})
    return render(request, plantilla, ctx)


def paginar(request, queryset, por_pagina=25):
    pagina = Paginator(queryset, por_pagina).get_page(request.GET.get("pagina"))
    params = request.GET.copy()
    params.pop("pagina", None)
    return pagina, params.urlencode()
