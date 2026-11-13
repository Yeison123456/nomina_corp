from django import forms
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404, render
from django.urls import reverse

from apps.core.roles import ADMIN, ESCRITURA, requiere_rol
from apps.core.vistas_base import formulario, paginar

from .forms import AreaForm, CargoForm, CentroCostoForm, ContratoForm, EmpleadoForm
from .models import Area, Cargo, CentroCosto, Contrato, Empleado


def empleados_lista(request):
    qs = Empleado.objects.select_related("eps").prefetch_related("contratos__cargo")
    q = request.GET.get("q", "").strip()
    estado = request.GET.get("estado", "1")
    centro = request.GET.get("centro", "")
    if q:
        qs = qs.filter(Q(nombres__icontains=q) | Q(apellidos__icontains=q) | Q(numero_documento__icontains=q))
    if estado in ("0", "1"):
        qs = qs.filter(activo=estado == "1")
    if centro:
        qs = qs.filter(contratos__centro_costo_id=centro, contratos__estado=Contrato.Estado.VIGENTE).distinct()
    pagina, params = paginar(request, qs)
    return render(request, "personal/empleados_lista.html", {
        "pagina": pagina, "params": params, "q": q, "estado": estado, "centro": centro,
        "centros": CentroCosto.objects.all(), "total": qs.count(),
    })


def empleado_detalle(request, pk):
    empleado = get_object_or_404(Empleado.objects.select_related("eps", "afp", "fondo_cesantias", "caja", "banco"), pk=pk)
    contratos = empleado.contratos.select_related("cargo", "centro_costo", "arl")
    from apps.nomina.models import LiquidacionNomina, Novedad, Prestamo

    return render(request, "personal/empleado_detalle.html", {
        "empleado": empleado,
        "contratos": contratos,
        "novedades": Novedad.objects.filter(contrato__empleado=empleado).select_related("concepto")[:12],
        "prestamos": Prestamo.objects.filter(contrato__empleado=empleado),
        "liquidaciones": LiquidacionNomina.objects.filter(contrato__empleado=empleado).select_related("periodo").order_by("-periodo__fecha_inicio")[:8],
    })


@requiere_rol(*ESCRITURA)
def empleado_editar(request, pk=None):
    obj = get_object_or_404(Empleado, pk=pk) if pk else None
    return formulario(
        request, EmpleadoForm, instance=obj,
        titulo=f"Editar empleado · {obj}" if obj else "Nuevo empleado",
        volver=reverse("personal:empleado", args=[obj.pk]) if obj else reverse("personal:empleados"),
        exito=lambda e: reverse("personal:empleado", args=[e.pk]),
        plantilla="personal/empleado_form.html",
    )


@requiere_rol(*ESCRITURA)
def contrato_editar(request, empleado_pk, pk=None):
    empleado = get_object_or_404(Empleado, pk=empleado_pk)
    obj = get_object_or_404(Contrato, pk=pk, empleado=empleado) if pk else None

    class Form(ContratoForm):
        def clean(self):
            datos = super().clean()
            vigentes = empleado.contratos.filter(estado=Contrato.Estado.VIGENTE)
            if obj:
                vigentes = vigentes.exclude(pk=obj.pk)
            if vigentes.exists():
                raise forms.ValidationError("El empleado ya tiene un contrato vigente. Termínelo con una liquidación de retiro antes de crear otro.")
            return datos

        def save(self, commit=True):
            contrato = super().save(commit=False)
            contrato.empleado = empleado
            contrato.save()
            return contrato

    inicial = None
    if not obj:
        siguiente = Contrato.objects.count() + 1
        inicial = {"numero": f"CI-{siguiente:05d}"}
    return formulario(
        request, Form, instance=obj, initial=inicial,
        titulo=f"Editar contrato {obj.numero}" if obj else f"Nuevo contrato · {empleado}",
        volver=reverse("personal:empleado", args=[empleado.pk]),
        plantilla="personal/contrato_form.html",
        contexto={"empleado": empleado},
    )


def estructura(request):
    return render(request, "personal/estructura.html", {
        "centros": CentroCosto.objects.annotate(n=Count("contratos", filter=Q(contratos__estado="VIG"))),
        "areas": Area.objects.select_related("centro_costo").annotate(n=Count("cargos")),
        "cargos": Cargo.objects.select_related("area").annotate(n=Count("contratos", filter=Q(contratos__estado="VIG"))),
    })


def _editar_estructura(request, modelo, form, pk, nombre):
    obj = get_object_or_404(modelo, pk=pk) if pk else None
    return formulario(request, form, instance=obj, titulo=f"Editar {nombre}" if obj else f"Nuevo {nombre}",
                      volver=reverse("personal:estructura"))


@requiere_rol(ADMIN)
def centro_editar(request, pk=None):
    return _editar_estructura(request, CentroCosto, CentroCostoForm, pk, "centro de costo")


@requiere_rol(ADMIN)
def area_editar(request, pk=None):
    return _editar_estructura(request, Area, AreaForm, pk, "área")


@requiere_rol(ADMIN)
def cargo_editar(request, pk=None):
    return _editar_estructura(request, Cargo, CargoForm, pk, "cargo")
