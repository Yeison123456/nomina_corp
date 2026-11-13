"""
Liquidación definitiva de prestaciones sociales al terminar un contrato.

Fórmulas (días comerciales de 360 al año):
    cesantías   = base × días del año en curso / 360
    intereses   = cesantías × días × 12 % / 360
    prima       = base × días del semestre en curso / 360
    vacaciones  = salario / 30 × días pendientes (15 hábiles por cada 360 trabajados)
    base        = salario + auxilio de transporte + promedio de pagos salariales variables
"""
from dataclasses import dataclass
from datetime import date, timedelta
from decimal import Decimal

from django.db import transaction

from apps.core.auditoria import registrar
from apps.core.models import ParametroLegal
from apps.personal.models import Contrato

from ..models import DetalleLiquidacion, LiquidacionContrato, Novedad
from .liquidador import ErrorNomina
from .motor import CERO, TREINTA, dias360, interseccion, redondear

CONCEPTOS_VARIABLES = ["RN", "HED", "HEN", "HDF", "HNDF", "HEDDF", "HENDF", "COM", "BONS"]
DIAS_ANIO = Decimal("360")


@dataclass
class CalculoLiquidacion:
    salario: Decimal
    auxilio_transporte: Decimal
    promedio_variable: Decimal
    base_cesantias: Decimal
    dias_cesantias: int
    cesantias: Decimal
    intereses_cesantias: Decimal
    dias_prima: int
    prima: Decimal
    dias_laborados: int
    dias_vacaciones_causados: Decimal
    dias_vacaciones_disfrutados: Decimal
    dias_vacaciones: Decimal
    vacaciones: Decimal
    dias_indemnizacion: Decimal
    indemnizacion: Decimal
    total: Decimal


def _dias_sin_pago(contrato: Contrato, desde: date, hasta: date) -> int:
    """Días de licencia no remunerada y suspensión, que no cuentan como tiempo de servicio."""
    total = 0
    for nov in Novedad.objects.filter(contrato=contrato, concepto__codigo__in=["LNR", "SUS"]).exclude(estado=Novedad.Estado.ANULADA):
        cruce = interseccion(desde, hasta, nov.fecha_inicio, nov.fecha_final)
        if cruce:
            total += dias360(*cruce)
    return total


def _promedio_variable(contrato: Contrato, desde: date, hasta: date, dias: int) -> Decimal:
    if dias <= 0:
        return CERO
    valores = DetalleLiquidacion.objects.filter(
        liquidacion__contrato=contrato,
        liquidacion__periodo__fecha_inicio__gte=desde,
        liquidacion__periodo__fecha_fin__lte=hasta,
        liquidacion__periodo__estado="CER",
        concepto__codigo__in=CONCEPTOS_VARIABLES,
    ).values_list("valor", flat=True)
    return redondear(sum(valores, CERO) / Decimal(dias) * TREINTA)


def calcular(contrato: Contrato, fecha_retiro: date, causa: str) -> CalculoLiquidacion:
    if fecha_retiro < contrato.fecha_inicio:
        raise ErrorNomina("La fecha de retiro es anterior al inicio del contrato.")
    p = ParametroLegal.vigente(fecha_retiro)
    if not p:
        raise ErrorNomina("No hay parámetros legales vigentes para la fecha de retiro.")

    salario = Decimal(contrato.salario)
    integral = contrato.es_integral
    aux = Decimal(p.auxilio_transporte) if (not integral and salario <= 2 * p.smmlv) else CERO

    # Cesantías e intereses: año calendario en curso (las anteriores ya se consignaron al fondo)
    desde_ces = max(contrato.fecha_inicio, date(fecha_retiro.year, 1, 1))
    dias_ces = dias360(desde_ces, fecha_retiro) - _dias_sin_pago(contrato, desde_ces, fecha_retiro)
    variable = _promedio_variable(contrato, desde_ces, fecha_retiro, dias_ces)
    base = salario + aux + variable

    # Prima: semestre en curso
    inicio_semestre = date(fecha_retiro.year, 1 if fecha_retiro.month <= 6 else 7, 1)
    desde_prima = max(contrato.fecha_inicio, inicio_semestre)
    dias_prima = dias360(desde_prima, fecha_retiro) - _dias_sin_pago(contrato, desde_prima, fecha_retiro)

    if integral:
        cesantias = intereses = prima = CERO
    else:
        cesantias = redondear(base * dias_ces / DIAS_ANIO)
        intereses = redondear(cesantias * dias_ces * Decimal("0.12") / DIAS_ANIO)
        prima = redondear(base * dias_prima / DIAS_ANIO)

    # Vacaciones: 15 días hábiles por cada 360 de servicio, menos los disfrutados
    dias_laborados = dias360(contrato.fecha_inicio, fecha_retiro) - _dias_sin_pago(contrato, contrato.fecha_inicio, fecha_retiro)
    causados = (Decimal(dias_laborados) * 15 / DIAS_ANIO).quantize(Decimal("0.01"))
    disfrutados = sum(
        Novedad.objects.filter(contrato=contrato, concepto__codigo="VACD", fecha_inicio__lte=fecha_retiro)
        .exclude(estado=Novedad.Estado.ANULADA).values_list("cantidad", flat=True),
        CERO,
    )
    pendientes = max(causados - disfrutados, CERO)
    vacaciones = redondear(salario / TREINTA * pendientes)

    # Indemnización por despido sin justa causa (art. 64 CST)
    dias_ind = CERO
    salario_dia = salario / TREINTA
    if causa == LiquidacionContrato.Causa.SIN_JUSTA_CAUSA:
        if contrato.tipo == Contrato.Tipo.FIJO and contrato.fecha_fin:
            dias_ind = Decimal(max(dias360(fecha_retiro + timedelta(days=1), contrato.fecha_fin), 0))
        elif contrato.tipo == Contrato.Tipo.OBRA:
            dias_ind = Decimal(15)
        else:
            anios = Decimal(dias_laborados) / DIAS_ANIO
            primero, adicional = (30, 20) if salario < 10 * p.smmlv else (20, 15)
            dias_ind = Decimal(primero) + max(anios - 1, CERO) * adicional
        dias_ind = dias_ind.quantize(Decimal("0.01"))
    indemnizacion = redondear(salario_dia * dias_ind)

    total = cesantias + intereses + prima + vacaciones + indemnizacion
    return CalculoLiquidacion(
        salario=salario, auxilio_transporte=aux, promedio_variable=variable, base_cesantias=base,
        dias_cesantias=dias_ces, cesantias=cesantias, intereses_cesantias=intereses,
        dias_prima=dias_prima, prima=prima, dias_laborados=dias_laborados,
        dias_vacaciones_causados=causados, dias_vacaciones_disfrutados=disfrutados,
        dias_vacaciones=pendientes, vacaciones=vacaciones,
        dias_indemnizacion=dias_ind, indemnizacion=indemnizacion, total=total,
    )


@transaction.atomic
def guardar(contrato: Contrato, fecha_retiro: date, causa: str, observaciones: str, usuario) -> LiquidacionContrato:
    if hasattr(contrato, "liquidacion_definitiva"):
        raise ErrorNomina("El contrato ya tiene una liquidación registrada.")
    c = calcular(contrato, fecha_retiro, causa)
    liq = LiquidacionContrato.objects.create(
        contrato=contrato, fecha_retiro=fecha_retiro, causa=causa, salario=c.salario,
        auxilio_transporte=c.auxilio_transporte, promedio_variable=c.promedio_variable,
        dias_cesantias=c.dias_cesantias, base_cesantias=c.base_cesantias, cesantias=c.cesantias,
        intereses_cesantias=c.intereses_cesantias, dias_prima=c.dias_prima, prima=c.prima,
        dias_vacaciones=c.dias_vacaciones, vacaciones=c.vacaciones, indemnizacion=c.indemnizacion,
        total=c.total, observaciones=observaciones, elaborado_por=usuario,
    )
    registrar(usuario, "LIQ_CONTRATO", liq, f"Total {c.total}")
    return liq


@transaction.atomic
def aprobar(liq: LiquidacionContrato, usuario) -> None:
    """Aprueba la liquidación y termina el contrato en la fecha de retiro."""
    if liq.estado != LiquidacionContrato.Estado.BORRADOR:
        raise ErrorNomina("La liquidación ya fue aprobada.")
    contrato = liq.contrato
    contrato.estado = Contrato.Estado.TERMINADO
    contrato.fecha_terminacion = liq.fecha_retiro
    contrato.motivo_terminacion = liq.get_causa_display()
    contrato.save(update_fields=["estado", "fecha_terminacion", "motivo_terminacion"])
    empleado = contrato.empleado
    if not empleado.contratos.filter(estado=Contrato.Estado.VIGENTE).exists():
        empleado.activo = False
        empleado.save(update_fields=["activo"])
    liq.estado = LiquidacionContrato.Estado.APROBADA
    liq.save(update_fields=["estado"])
    registrar(usuario, "APROBAR_LIQ", liq)
