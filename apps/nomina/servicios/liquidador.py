"""
Orquestación de la nómina periódica: carga datos, invoca el motor de cálculo,
persiste resultados y gestiona el ciclo de vida del periodo
(Abierto → Liquidado → Cerrado).
"""
from datetime import date

from django.db import transaction
from django.db.models import Q
from django.utils import timezone

from apps.core.auditoria import registrar
from apps.core.models import Empresa, ParametroLegal
from apps.personal.models import Contrato

from ..models import Concepto, DetalleLiquidacion, LiquidacionNomina, Novedad, PeriodoNomina, Prestamo
from .motor import CERO, MotorNomina


class ErrorNomina(Exception):
    """Error de negocio que se muestra al usuario."""


def fechas_periodo(periodicidad: str, anio: int, mes: int, numero: int) -> tuple[date, date]:
    import calendar

    ultimo = calendar.monthrange(anio, mes)[1]
    if periodicidad == Contrato.Periodicidad.MENSUAL:
        return date(anio, mes, 1), date(anio, mes, ultimo)
    if numero == 1:
        return date(anio, mes, 1), date(anio, mes, 15)
    return date(anio, mes, 16), date(anio, mes, ultimo)


def contratos_del_periodo(periodo: PeriodoNomina):
    return (
        Contrato.objects.select_related("empleado", "cargo", "centro_costo")
        .filter(periodicidad=periodo.periodicidad, fecha_inicio__lte=periodo.fecha_fin)
        .filter(Q(fecha_terminacion__isnull=True) | Q(fecha_terminacion__gte=periodo.fecha_inicio))
        .order_by("empleado__apellidos", "empleado__nombres")
    )


def novedades_del_contrato(contrato: Contrato, periodo: PeriodoNomina):
    candidatas = (
        Novedad.objects.select_related("concepto")
        .filter(contrato=contrato, estado=Novedad.Estado.PENDIENTE, fecha_inicio__lte=periodo.fecha_fin)
    )
    return [n for n in candidatas if n.concepto.captura != Concepto.Captura.DIAS or n.fecha_final >= periodo.fecha_inicio]


def prestamos_del_contrato(contrato: Contrato, periodo: PeriodoNomina):
    return list(
        Prestamo.objects.select_related("concepto")
        .filter(contrato=contrato, estado=Prestamo.Estado.ACTIVO, saldo__gt=0, fecha__lte=periodo.fecha_fin)
        .order_by("fecha")
    )


def crear_motor(fecha: date) -> MotorNomina:
    parametros = ParametroLegal.vigente(fecha)
    if not parametros:
        raise ErrorNomina(f"No hay parámetros legales vigentes al {fecha:%d/%m/%Y}. Regístrelos en Configuración.")
    empresa = Empresa.actual()
    if not empresa:
        raise ErrorNomina("No se han registrado los datos de la empresa.")
    conceptos = {c.codigo: c for c in Concepto.objects.all()}
    return MotorNomina(parametros, conceptos, empresa.exonerada_aportes)


@transaction.atomic
def liquidar_periodo(periodo: PeriodoNomina, usuario) -> int:
    """Liquida (o reliquida) todos los contratos del periodo. Devuelve el número de liquidaciones."""
    periodo = PeriodoNomina.objects.select_for_update().get(pk=periodo.pk)
    if periodo.estado == PeriodoNomina.Estado.CERRADO:
        raise ErrorNomina("El periodo está cerrado y no se puede reliquidar.")

    motor = crear_motor(periodo.fecha_fin)
    conceptos = motor.conceptos
    periodo.liquidaciones.all().delete()

    total = 0
    for contrato in contratos_del_periodo(periodo):
        res = motor.liquidar(
            contrato, periodo.fecha_inicio, periodo.fecha_fin, periodo.dias,
            novedades_del_contrato(contrato, periodo), prestamos_del_contrato(contrato, periodo),
        )
        if res.dias_periodo == 0:
            continue
        devengado = res.total("DEV", conceptos)
        deducciones = res.total("DED", conceptos)
        liq = LiquidacionNomina.objects.create(
            periodo=periodo, contrato=contrato, salario=contrato.salario,
            dias_periodo=res.dias_periodo, dias_trabajados=res.dias_trabajados,
            ibc=res.ibc, base_prestaciones=res.base_prestaciones,
            total_devengado=devengado, total_deducciones=deducciones, neto_pagar=devengado - deducciones,
            total_aportes=res.total("APO", conceptos), total_provisiones=res.total("PRO", conceptos),
            advertencias="\n".join(res.advertencias),
        )
        DetalleLiquidacion.objects.bulk_create([
            DetalleLiquidacion(
                liquidacion=liq, concepto=conceptos[l.codigo], cantidad=l.cantidad, base=l.base,
                tasa=l.tasa, valor=l.valor, novedad_id=l.novedad_id, prestamo_id=l.prestamo_id,
            )
            for l in res.lineas
        ])
        total += 1

    periodo.estado = PeriodoNomina.Estado.LIQUIDADO
    periodo.liquidado_por = usuario if getattr(usuario, "is_authenticated", False) else None
    periodo.fecha_liquidacion = timezone.now()
    periodo.save()
    registrar(usuario, "LIQUIDAR", periodo, f"{total} contratos liquidados")
    return total


@transaction.atomic
def cerrar_periodo(periodo: PeriodoNomina, usuario) -> None:
    """Cierra el periodo: aplica novedades y descuenta cuotas de préstamos."""
    periodo = PeriodoNomina.objects.select_for_update().get(pk=periodo.pk)
    if periodo.estado != PeriodoNomina.Estado.LIQUIDADO:
        raise ErrorNomina("Solo se puede cerrar un periodo liquidado.")

    detalles = DetalleLiquidacion.objects.filter(liquidacion__periodo=periodo).select_related("novedad__concepto", "prestamo")
    novedades = {d.novedad for d in detalles if d.novedad}
    for nov in novedades:
        if nov.concepto.captura == Concepto.Captura.DIAS and nov.fecha_final > periodo.fecha_fin:
            continue  # la ausencia continúa en el siguiente periodo
        nov.estado = Novedad.Estado.APLICADA
        nov.periodo_aplicacion = periodo
        nov.save(update_fields=["estado", "periodo_aplicacion"])

    for d in detalles:
        if d.prestamo:
            pre = Prestamo.objects.select_for_update().get(pk=d.prestamo_id)
            pre.saldo = max(pre.saldo - d.valor, CERO)
            if pre.saldo == 0:
                pre.estado = Prestamo.Estado.PAGADO
            pre.save(update_fields=["saldo", "estado"])

    periodo.estado = PeriodoNomina.Estado.CERRADO
    periodo.cerrado_por = usuario if getattr(usuario, "is_authenticated", False) else None
    periodo.fecha_cierre = timezone.now()
    periodo.save()
    registrar(usuario, "CERRAR", periodo)


@transaction.atomic
def reabrir_periodo(periodo: PeriodoNomina, usuario) -> None:
    """Revierte el cierre: devuelve novedades a pendiente y restituye saldos de préstamos."""
    periodo = PeriodoNomina.objects.select_for_update().get(pk=periodo.pk)
    if periodo.estado != PeriodoNomina.Estado.CERRADO:
        raise ErrorNomina("Solo se puede reabrir un periodo cerrado.")
    posterior = PeriodoNomina.objects.filter(
        periodicidad=periodo.periodicidad, fecha_inicio__gt=periodo.fecha_fin, estado=PeriodoNomina.Estado.CERRADO
    ).exists()
    if posterior:
        raise ErrorNomina("Existe un periodo posterior cerrado. Reábralo primero.")

    Novedad.objects.filter(periodo_aplicacion=periodo).update(estado=Novedad.Estado.PENDIENTE, periodo_aplicacion=None)
    for d in DetalleLiquidacion.objects.filter(liquidacion__periodo=periodo, prestamo__isnull=False):
        pre = Prestamo.objects.select_for_update().get(pk=d.prestamo_id)
        pre.saldo += d.valor
        pre.estado = Prestamo.Estado.ACTIVO
        pre.save(update_fields=["saldo", "estado"])

    periodo.estado = PeriodoNomina.Estado.LIQUIDADO
    periodo.cerrado_por = None
    periodo.fecha_cierre = None
    periodo.save()
    registrar(usuario, "REABRIR", periodo)
