from collections import OrderedDict
from decimal import Decimal

from django.contrib import messages
from django.db.models import Count, Q, Sum
from django.http import HttpResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.utils import timezone
from django.views.decorators.http import require_POST

from apps.core.auditoria import registrar
from apps.core.models import Entidad
from apps.core.roles import ADMIN, ESCRITURA, requiere_rol
from apps.core.vistas_base import formulario, paginar
from apps.personal.models import CentroCosto, Contrato

from .forms import LiquidacionContratoForm, NovedadForm, PeriodoForm, PrestamoForm
from .models import Concepto, DetalleLiquidacion, LiquidacionContrato, LiquidacionNomina, Novedad, PeriodoNomina, Prestamo
from .servicios import documentos, liquidacion_contrato, liquidador
from .servicios.liquidador import ErrorNomina


def _archivo(contenido: bytes, nombre: str, tipo: str, adjunto=True) -> HttpResponse:
    resp = HttpResponse(contenido, content_type=tipo)
    resp["Content-Disposition"] = f'{"attachment" if adjunto else "inline"}; filename="{nombre}"'
    return resp


# --------------------------------------------------------------------------- periodos

def periodos_lista(request):
    anio = request.GET.get("anio", "")
    qs = PeriodoNomina.objects.annotate(
        empleados=Count("liquidaciones"),
        neto=Sum("liquidaciones__neto_pagar"),
        devengado=Sum("liquidaciones__total_devengado"),
    ).order_by("-anio", "-mes", "-numero", "periodicidad")
    if anio:
        qs = qs.filter(anio=anio)
    anios = PeriodoNomina.objects.values_list("anio", flat=True).distinct().order_by("-anio")
    pagina, params = paginar(request, qs, 30)
    return render(request, "nomina/periodos_lista.html", {"pagina": pagina, "params": params, "anios": anios, "anio": anio})


@requiere_rol(*ESCRITURA)
def periodo_nuevo(request):
    hoy = timezone.localdate()
    inicial = {"anio": hoy.year, "mes": hoy.month, "numero": 1 if hoy.day <= 15 else 2, "periodicidad": "Q"}
    return formulario(request, PeriodoForm, titulo="Nuevo periodo de nómina", volver=reverse("nomina:periodos"),
                      exito=lambda p: reverse("nomina:periodo", args=[p.pk]), initial=inicial,
                      plantilla="nomina/periodo_form.html")


def periodo_detalle(request, pk):
    periodo = get_object_or_404(PeriodoNomina, pk=pk)
    liqs = periodo.liquidaciones.select_related("contrato__empleado", "contrato__cargo", "contrato__centro_costo")
    totales = liqs.aggregate(
        devengado=Sum("total_devengado"), deducciones=Sum("total_deducciones"), neto=Sum("neto_pagar"),
        aportes=Sum("total_aportes"), provisiones=Sum("total_provisiones"),
    )
    totales = {k: v or Decimal(0) for k, v in totales.items()}
    totales["costo"] = totales["devengado"] + totales["aportes"] + totales["provisiones"]
    resumen = (
        DetalleLiquidacion.objects.filter(liquidacion__periodo=periodo)
        .values("concepto__codigo", "concepto__nombre", "concepto__tipo", "concepto__orden")
        .annotate(total=Sum("valor"), personas=Count("liquidacion", distinct=True))
        .order_by("concepto__tipo", "concepto__orden")
    )
    grupos = OrderedDict((t, []) for t in ["DEV", "DED", "APO", "PRO"])
    for r in resumen:
        grupos.setdefault(r["concepto__tipo"], []).append(r)
    nombres_grupo = dict(Concepto.Tipo.choices)
    pendientes = 0
    if periodo.editable:
        pendientes = Novedad.objects.filter(
            estado=Novedad.Estado.PENDIENTE, fecha_inicio__lte=periodo.fecha_fin, contrato__periodicidad=periodo.periodicidad
        ).exclude(detalles__liquidacion__periodo=periodo).count()
    return render(request, "nomina/periodo_detalle.html", {
        "periodo": periodo, "liquidaciones": liqs, "totales": totales,
        "grupos": [(nombres_grupo[t], filas) for t, filas in grupos.items() if filas],
        "con_advertencias": [l for l in liqs if l.advertencias],
        "contratos_esperados": liquidador.contratos_del_periodo(periodo).count(),
        "novedades_pendientes": pendientes,
    })


@require_POST
@requiere_rol(*ESCRITURA)
def periodo_liquidar(request, pk):
    periodo = get_object_or_404(PeriodoNomina, pk=pk)
    try:
        n = liquidador.liquidar_periodo(periodo, request.user)
        messages.success(request, f"Periodo liquidado: {n} contratos procesados.")
    except ErrorNomina as e:
        messages.error(request, str(e))
    return redirect("nomina:periodo", pk=pk)


@require_POST
@requiere_rol(ADMIN)
def periodo_cerrar(request, pk):
    periodo = get_object_or_404(PeriodoNomina, pk=pk)
    try:
        liquidador.cerrar_periodo(periodo, request.user)
        messages.success(request, "Periodo cerrado. Las novedades quedaron aplicadas y los saldos de préstamos actualizados.")
    except ErrorNomina as e:
        messages.error(request, str(e))
    return redirect("nomina:periodo", pk=pk)


@require_POST
@requiere_rol(ADMIN)
def periodo_reabrir(request, pk):
    periodo = get_object_or_404(PeriodoNomina, pk=pk)
    try:
        liquidador.reabrir_periodo(periodo, request.user)
        messages.success(request, "Periodo reabierto. Puede reliquidarlo.")
    except ErrorNomina as e:
        messages.error(request, str(e))
    return redirect("nomina:periodo", pk=pk)


@require_POST
@requiere_rol(*ESCRITURA)
def periodo_eliminar(request, pk):
    periodo = get_object_or_404(PeriodoNomina, pk=pk)
    if periodo.estado == PeriodoNomina.Estado.CERRADO:
        messages.error(request, "No se puede eliminar un periodo cerrado.")
        return redirect("nomina:periodo", pk=pk)
    registrar(request.user, "ELIMINAR", periodo)
    periodo.delete()
    messages.success(request, "Periodo eliminado.")
    return redirect("nomina:periodos")


def liquidacion_detalle(request, pk):
    liq = get_object_or_404(LiquidacionNomina.objects.select_related("periodo", "contrato__empleado", "contrato__cargo"), pk=pk)
    detalles = liq.detalles.select_related("concepto", "novedad").order_by("concepto__orden")
    por_tipo = OrderedDict((t, []) for t in ["DEV", "DED", "APO", "PRO"])
    for d in detalles:
        por_tipo.setdefault(d.concepto.tipo, []).append(d)
    nombres = {"DEV": "Devengados", "DED": "Deducciones", "APO": "Aportes del empleador", "PRO": "Provisiones de prestaciones"}
    return render(request, "nomina/liquidacion_detalle.html", {
        "liq": liq,
        "secciones": [(t, nombres[t], filas, sum((f.valor for f in filas), Decimal(0))) for t, filas in por_tipo.items() if filas],
        "advertencias": [a for a in liq.advertencias.splitlines() if a],
    })


def desprendible(request, pk):
    liq = get_object_or_404(LiquidacionNomina, pk=pk)
    pdf = documentos.desprendible_pdf([liq])
    return _archivo(pdf, f"desprendible_{liq.periodo.codigo}_{liq.contrato.empleado.numero_documento}.pdf", "application/pdf", adjunto=False)


def desprendibles_periodo(request, pk):
    periodo = get_object_or_404(PeriodoNomina, pk=pk)
    liqs = periodo.liquidaciones.select_related("contrato__empleado__eps", "contrato__empleado__afp", "contrato__empleado__banco", "contrato__cargo", "contrato__centro_costo")
    if not liqs:
        messages.error(request, "El periodo no tiene liquidaciones.")
        return redirect("nomina:periodo", pk=pk)
    return _archivo(documentos.desprendible_pdf(liqs), f"desprendibles_{periodo.codigo}.pdf", "application/pdf", adjunto=False)


def sabana(request, pk):
    periodo = get_object_or_404(PeriodoNomina, pk=pk)
    return _archivo(documentos.sabana_excel(periodo), f"sabana_{periodo.codigo}.xlsx",
                    "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")


# --------------------------------------------------------------------------- novedades

def novedades_lista(request):
    qs = Novedad.objects.select_related("contrato__empleado", "concepto", "periodo_aplicacion")
    estado = request.GET.get("estado", "PEN")
    concepto = request.GET.get("concepto", "")
    q = request.GET.get("q", "").strip()
    if estado:
        qs = qs.filter(estado=estado)
    if concepto:
        qs = qs.filter(concepto__codigo=concepto)
    if q:
        qs = qs.filter(Q(contrato__empleado__nombres__icontains=q) | Q(contrato__empleado__apellidos__icontains=q) | Q(contrato__empleado__numero_documento__icontains=q))
    pagina, params = paginar(request, qs, 30)
    return render(request, "nomina/novedades_lista.html", {
        "pagina": pagina, "params": params, "estado": estado, "concepto": concepto, "q": q,
        "estados": Novedad.Estado.choices,
        "conceptos": Concepto.objects.filter(captura__in=["HOR", "DIA", "VAL"]).order_by("captura", "orden"),
    })


@requiere_rol(*ESCRITURA)
def novedad_editar(request, pk=None):
    obj = get_object_or_404(Novedad, pk=pk) if pk else None
    if obj and obj.estado != Novedad.Estado.PENDIENTE:
        messages.error(request, "Solo se pueden editar novedades pendientes.")
        return redirect("nomina:novedades")

    class Form(NovedadForm):
        def save(self, commit=True):
            nov = super().save(commit=False)
            if not nov.pk:
                nov.registrado_por = request.user
            nov.save()
            return nov

    inicial = {"fecha_inicio": timezone.localdate()}
    if request.GET.get("contrato"):
        inicial["contrato"] = request.GET["contrato"]
    return formulario(request, Form, instance=obj, initial=None if obj else inicial,
                      titulo="Editar novedad" if obj else "Registrar novedad",
                      volver=reverse("nomina:novedades"), plantilla="nomina/novedad_form.html")


@require_POST
@requiere_rol(*ESCRITURA)
def novedad_anular(request, pk):
    nov = get_object_or_404(Novedad, pk=pk)
    if nov.estado != Novedad.Estado.PENDIENTE:
        messages.error(request, "Solo se pueden anular novedades pendientes.")
    else:
        nov.estado = Novedad.Estado.ANULADA
        nov.save(update_fields=["estado"])
        registrar(request.user, "ANULAR", nov)
        messages.success(request, "Novedad anulada.")
    return redirect(request.POST.get("volver") or "nomina:novedades")


# --------------------------------------------------------------------------- préstamos

def prestamos_lista(request):
    estado = request.GET.get("estado", "ACT")
    qs = Prestamo.objects.select_related("contrato__empleado", "concepto")
    if estado:
        qs = qs.filter(estado=estado)
    pagina, params = paginar(request, qs, 30)
    return render(request, "nomina/prestamos_lista.html", {"pagina": pagina, "params": params, "estado": estado,
                                                           "estados": Prestamo.Estado.choices})


@requiere_rol(*ESCRITURA)
def prestamo_nuevo(request):
    return formulario(request, PrestamoForm, titulo="Registrar préstamo o libranza", volver=reverse("nomina:prestamos"),
                      initial={"fecha": timezone.localdate()})


@require_POST
@requiere_rol(ADMIN)
def prestamo_anular(request, pk):
    pre = get_object_or_404(Prestamo, pk=pk)
    if pre.estado == Prestamo.Estado.ACTIVO:
        pre.estado = Prestamo.Estado.ANULADO
        pre.save(update_fields=["estado"])
        registrar(request.user, "ANULAR", pre, f"Saldo al anular: {pre.saldo}")
        messages.success(request, "Préstamo anulado; no se descontarán más cuotas.")
    return redirect("nomina:prestamos")


# --------------------------------------------------------------------------- conceptos

def conceptos_lista(request):
    grupos = OrderedDict()
    for c in Concepto.objects.all():
        grupos.setdefault(c.get_tipo_display(), []).append(c)
    return render(request, "nomina/conceptos_lista.html", {"grupos": grupos})


# --------------------------------------------------------------------------- liquidación de contratos

def liquidaciones_contrato(request):
    qs = LiquidacionContrato.objects.select_related("contrato__empleado", "contrato__cargo")
    return render(request, "nomina/liquidaciones_contrato.html", {"liquidaciones": qs})


@requiere_rol(*ESCRITURA)
def liquidacion_contrato_nueva(request):
    calculo = None
    form = LiquidacionContratoForm(request.POST or None, initial={"contrato": request.GET.get("contrato")})
    if request.method == "POST" and form.is_valid():
        d = form.cleaned_data
        try:
            if "guardar" in request.POST:
                liq = liquidacion_contrato.guardar(d["contrato"], d["fecha_retiro"], d["causa"], d["observaciones"], request.user)
                messages.success(request, "Liquidación guardada como borrador.")
                return redirect("nomina:liquidacion_contrato", pk=liq.pk)
            calculo = liquidacion_contrato.calcular(d["contrato"], d["fecha_retiro"], d["causa"])
        except ErrorNomina as e:
            messages.error(request, str(e))
    return render(request, "nomina/liquidacion_contrato_form.html", {"form": form, "calculo": calculo})


def liquidacion_contrato_detalle(request, pk):
    liq = get_object_or_404(LiquidacionContrato.objects.select_related("contrato__empleado", "contrato__cargo"), pk=pk)
    calculo = liquidacion_contrato.calcular(liq.contrato, liq.fecha_retiro, liq.causa) if liq.estado == "BOR" else None
    return render(request, "nomina/liquidacion_contrato_detalle.html", {"liq": liq, "calculo": calculo})


def liquidacion_contrato_pdf(request, pk):
    liq = get_object_or_404(LiquidacionContrato, pk=pk)
    calculo = liquidacion_contrato.calcular(liq.contrato, liq.fecha_retiro, liq.causa)
    return _archivo(documentos.liquidacion_contrato_pdf(liq, calculo), f"liquidacion_{liq.contrato.numero}.pdf", "application/pdf", adjunto=False)


@require_POST
@requiere_rol(ADMIN)
def liquidacion_contrato_aprobar(request, pk):
    liq = get_object_or_404(LiquidacionContrato, pk=pk)
    try:
        liquidacion_contrato.aprobar(liq, request.user)
        messages.success(request, "Liquidación aprobada. El contrato quedó terminado.")
    except ErrorNomina as e:
        messages.error(request, str(e))
    return redirect("nomina:liquidacion_contrato", pk=pk)


@require_POST
@requiere_rol(*ESCRITURA)
def liquidacion_contrato_eliminar(request, pk):
    liq = get_object_or_404(LiquidacionContrato, pk=pk)
    if liq.estado != LiquidacionContrato.Estado.BORRADOR:
        messages.error(request, "Solo se pueden eliminar liquidaciones en borrador.")
        return redirect("nomina:liquidacion_contrato", pk=pk)
    registrar(request.user, "ELIMINAR", liq)
    liq.delete()
    messages.success(request, "Borrador eliminado.")
    return redirect("nomina:liquidaciones_contrato")


# --------------------------------------------------------------------------- reportes

def _filtro_mes(request):
    ultimo = PeriodoNomina.objects.exclude(estado="BOR").order_by("-anio", "-mes").first()
    hoy = timezone.localdate()
    anio = int(request.GET.get("anio") or (ultimo.anio if ultimo else hoy.year))
    mes = int(request.GET.get("mes") or (ultimo.mes if ultimo else hoy.month))
    return anio, mes


def reportes(request):
    anio, mes = _filtro_mes(request)
    liqs = LiquidacionNomina.objects.filter(periodo__anio=anio, periodo__mes=mes).exclude(periodo__estado="BOR")

    costos = list(
        liqs.values("contrato__centro_costo__codigo", "contrato__centro_costo__nombre")
        .annotate(empleados=Count("contrato", distinct=True), devengado=Sum("total_devengado"),
                  aportes=Sum("total_aportes"), provisiones=Sum("total_provisiones"))
        .order_by("contrato__centro_costo__codigo")
    )
    for c in costos:
        c["centro"] = f'{c["contrato__centro_costo__codigo"]} · {c["contrato__centro_costo__nombre"]}'
        c["costo"] = c["devengado"] + c["aportes"] + c["provisiones"]
    tot_costos = {k: sum((c[k] for c in costos), Decimal(0)) for k in ("devengado", "aportes", "provisiones", "costo")}

    if request.GET.get("exportar") == "costos":
        return _archivo(documentos.costos_excel(costos, f"Costo de nómina por centro de costo — {PeriodoNomina.MESES[mes]} {anio}"),
                        f"costos_{anio}-{mes:02d}.xlsx", "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

    # Aportes a seguridad social por entidad
    det = DetalleLiquidacion.objects.filter(liquidacion__in=liqs)
    entidades = []
    mapa = [
        ("EPS", "contrato__empleado__eps__nombre", ["SALUD"], ["AP_SAL"]),
        ("Pensiones", "contrato__empleado__afp__nombre", ["PENS", "FSP"], ["AP_PEN"]),
        ("ARL", "contrato__arl__nombre", [], ["AP_ARL"]),
        ("Caja de compensación", "contrato__empleado__caja__nombre", [], ["AP_CCF"]),
    ]
    for tipo, campo, cod_emp, cod_empr in mapa:
        filas = (
            det.filter(concepto__codigo__in=cod_emp + cod_empr)
            .values(f"liquidacion__{campo}")
            .annotate(
                empleado=Sum("valor", filter=Q(concepto__codigo__in=cod_emp)),
                empleador=Sum("valor", filter=Q(concepto__codigo__in=cod_empr)),
                afiliados=Count("liquidacion__contrato", distinct=True),
            ).order_by(f"liquidacion__{campo}")
        )
        for f in filas:
            emp, empr = f["empleado"] or Decimal(0), f["empleador"] or Decimal(0)
            entidades.append({"tipo": tipo, "nombre": f[f"liquidacion__{campo}"], "afiliados": f["afiliados"],
                              "empleado": emp, "empleador": empr, "total": emp + empr})
    parafiscales = det.filter(concepto__codigo__in=["AP_ICBF", "AP_SENA"]).values("concepto__nombre").annotate(total=Sum("valor"))
    tot_ss = sum((e["total"] for e in entidades), Decimal(0)) + sum((p["total"] for p in parafiscales), Decimal(0))

    provisiones = det.filter(concepto__tipo="PRO").values("concepto__nombre").annotate(total=Sum("valor")).order_by("concepto__orden")

    return render(request, "nomina/reportes.html", {
        "anio": anio, "mes": mes, "meses": [(i, PeriodoNomina.MESES[i]) for i in range(1, 13)],
        "anios": sorted(set(PeriodoNomina.objects.values_list("anio", flat=True)) | {anio}, reverse=True),
        "costos": costos, "tot_costos": tot_costos, "entidades": entidades, "parafiscales": parafiscales,
        "tot_ss": tot_ss, "provisiones": provisiones, "tot_prov": sum((p["total"] for p in provisiones), Decimal(0)),
        "nombre_mes": PeriodoNomina.MESES[mes],
    })
