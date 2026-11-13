from datetime import timedelta
from decimal import Decimal

from django.contrib.auth import views as auth_views
from django.contrib.auth.models import User
from django.db.models import Count, Q, Sum
from django.shortcuts import get_object_or_404, render
from django.urls import reverse
from django.utils import timezone

from apps.nomina.models import LiquidacionNomina, Novedad, PeriodoNomina
from apps.personal.models import Contrato, Empleado

from .forms import EmpresaForm, EntidadForm, ParametroLegalForm, UsuarioForm
from .models import Auditoria, Empresa, Entidad, ParametroLegal
from .roles import ADMIN, requiere_rol
from .vistas_base import formulario, paginar


class Ingresar(auth_views.LoginView):
    template_name = "registration/ingresar.html"
    redirect_authenticated_user = True


def tablero(request):
    hoy = timezone.localdate()
    contratos = Contrato.objects.filter(estado=Contrato.Estado.VIGENTE)

    # Costo de nómina por mes (últimos 6 meses con periodos cerrados o liquidados)
    por_mes = (
        LiquidacionNomina.objects.filter(periodo__estado=PeriodoNomina.Estado.CERRADO)
        .values("periodo__anio", "periodo__mes")
        .annotate(dev=Sum("total_devengado"), apo=Sum("total_aportes"), pro=Sum("total_provisiones"), neto=Sum("neto_pagar"))
        .order_by("-periodo__anio", "-periodo__mes")[:6]
    )
    meses = []
    for m in reversed(list(por_mes)):
        costo = (m["dev"] or 0) + (m["apo"] or 0) + (m["pro"] or 0)
        meses.append({
            "etiqueta": f"{PeriodoNomina.MESES[m['periodo__mes']][:3]} {m['periodo__anio']}",
            "devengado": m["dev"] or 0, "aportes": m["apo"] or 0, "provisiones": m["pro"] or 0,
            "costo": costo, "neto": m["neto"] or 0,
        })
    maximo = max([m["costo"] for m in meses] + [Decimal(1)])
    for m in meses:
        m["alto_dev"] = round(float(m["devengado"] / maximo) * 100, 1)
        m["alto_apo"] = round(float(m["aportes"] / maximo) * 100, 1)
        m["alto_pro"] = round(float(m["provisiones"] / maximo) * 100, 1)
    ultimo = meses[-1] if meses else None

    # Distribución por centro de costo del último mes
    centros = []
    if por_mes:
        ref = por_mes[0]
        centros = list(
            LiquidacionNomina.objects.filter(periodo__anio=ref["periodo__anio"], periodo__mes=ref["periodo__mes"])
            .filter(periodo__estado=PeriodoNomina.Estado.CERRADO)
            .values("contrato__centro_costo__nombre")
            .annotate(costo=Sum("total_devengado") + Sum("total_aportes") + Sum("total_provisiones"), personas=Count("contrato", distinct=True))
            .order_by("-costo")
        )
        total_c = sum((c["costo"] for c in centros), Decimal(0)) or Decimal(1)
        for c in centros:
            c["pct"] = round(float(c["costo"] / total_c) * 100, 1)

    contexto = {
        "empleados_activos": Empleado.objects.filter(activo=True).count(),
        "contratos_q": contratos.filter(periodicidad="Q").count(),
        "contratos_m": contratos.filter(periodicidad="M").count(),
        "novedades_pendientes": Novedad.objects.filter(estado=Novedad.Estado.PENDIENTE).count(),
        "periodos_abiertos": PeriodoNomina.objects.exclude(estado=PeriodoNomina.Estado.CERRADO).order_by("fecha_inicio"),
        "vencimientos": contratos.filter(tipo=Contrato.Tipo.FIJO, fecha_fin__gte=hoy, fecha_fin__lte=hoy + timedelta(days=60))
        .select_related("empleado", "cargo").order_by("fecha_fin"),
        "meses": meses,
        "ultimo": ultimo,
        "centros": centros,
        "hoy": hoy,
    }
    return render(request, "core/tablero.html", contexto)


# --------------------------------------------------------------------------- configuración

@requiere_rol(ADMIN)
def empresa_editar(request):
    empresa = Empresa.actual()
    return formulario(request, EmpresaForm, instance=empresa, titulo="Datos de la empresa",
                      volver=reverse("core:empresa"), contexto={"seccion": "config"})


def parametros_lista(request):
    return render(request, "core/parametros_lista.html", {"parametros": ParametroLegal.objects.all()})


@requiere_rol(ADMIN)
def parametro_editar(request, pk=None):
    obj = get_object_or_404(ParametroLegal, pk=pk) if pk else None
    inicial = None
    if not obj:
        ultimo = ParametroLegal.objects.first()
        if ultimo:
            inicial = {f.name: getattr(ultimo, f.name) for f in ParametroLegal._meta.fields if f.name not in ("id", "vigente_desde", "descripcion")}
    return formulario(request, ParametroLegalForm, instance=obj, initial=inicial,
                      titulo="Editar parámetros legales" if obj else "Nuevos parámetros legales",
                      volver=reverse("core:parametros"))


def entidades_lista(request):
    tipo = request.GET.get("tipo", "")
    qs = Entidad.objects.all()
    if tipo:
        qs = qs.filter(tipo=tipo)
    return render(request, "core/entidades_lista.html", {"entidades": qs, "tipos": Entidad.Tipo.choices, "tipo": tipo})


@requiere_rol(ADMIN)
def entidad_editar(request, pk=None):
    obj = get_object_or_404(Entidad, pk=pk) if pk else None
    return formulario(request, EntidadForm, instance=obj, titulo="Editar entidad" if obj else "Nueva entidad",
                      volver=reverse("core:entidades"))


@requiere_rol(ADMIN)
def usuarios_lista(request):
    usuarios = User.objects.prefetch_related("groups").order_by("username")
    return render(request, "core/usuarios_lista.html", {"usuarios": usuarios})


@requiere_rol(ADMIN)
def usuario_editar(request, pk=None):
    obj = get_object_or_404(User, pk=pk) if pk else None
    return formulario(request, UsuarioForm, instance=obj, titulo="Editar usuario" if obj else "Nuevo usuario",
                      volver=reverse("core:usuarios"))


@requiere_rol(ADMIN)
def auditoria_lista(request):
    q = request.GET.get("q", "").strip()
    qs = Auditoria.objects.select_related("usuario")
    if q:
        qs = qs.filter(Q(accion__icontains=q) | Q(objeto__icontains=q) | Q(usuario__username__icontains=q))
    pagina, params = paginar(request, qs, 40)
    return render(request, "core/auditoria_lista.html", {"pagina": pagina, "params": params, "q": q})


def empresa_ver(request):
    return render(request, "core/empresa.html", {"empresa": Empresa.actual()})
