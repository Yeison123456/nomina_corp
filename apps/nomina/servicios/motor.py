"""
Motor de cálculo de nómina.

Este módulo NO consulta la base de datos: recibe los objetos ya cargados
(contrato, parámetros, novedades, préstamos y catálogo de conceptos) y devuelve
un `Resultado` con las líneas calculadas. Así puede probarse de forma aislada y
el orden de las reglas queda explícito en un solo lugar.

Orden de cálculo
----------------
1. Días del contrato dentro del periodo (base 30 días por mes).
2. Ausencias por días (incapacidades, licencias, vacaciones, suspensiones).
3. Salario básico por los días restantes.
4. Horas extra y recargos.
5. Pagos por valor (comisiones, bonificaciones, auxilios).
6. Auxilio de transporte.
7. IBC (incluye regla del 40 % de pagos no salariales).
8. Deducciones de ley: salud, pensión, fondo de solidaridad.
9. Retención en la fuente (procedimiento 1).
10. Préstamos y descuentos, sin dejar el neto en negativo.
11. Aportes del empleador.
12. Provisiones de prestaciones sociales.
"""
from __future__ import annotations

import calendar
from dataclasses import dataclass, field
from datetime import date
from decimal import ROUND_HALF_UP, Decimal

CERO = Decimal("0")
UNO = Decimal("1")
TREINTA = Decimal("30")

PCT_CESANTIAS = Decimal("0.0833")
PCT_INTERESES = Decimal("0.12")
PCT_PRIMA = Decimal("0.0833")
PCT_VACACIONES = Decimal("0.0417")
FACTOR_INTEGRAL = Decimal("0.70")
LIMITE_NO_SALARIAL = Decimal("0.40")

# Retención en la fuente — tabla del art. 383 E.T. en UVT:
# (desde, hasta, tarifa marginal, impuesto fijo en UVT)
TABLA_RETENCION = [
    (Decimal("0"), Decimal("95"), Decimal("0"), Decimal("0")),
    (Decimal("95"), Decimal("150"), Decimal("0.19"), Decimal("0")),
    (Decimal("150"), Decimal("360"), Decimal("0.28"), Decimal("10")),
    (Decimal("360"), Decimal("640"), Decimal("0.33"), Decimal("69")),
    (Decimal("640"), Decimal("945"), Decimal("0.35"), Decimal("162")),
    (Decimal("945"), Decimal("2300"), Decimal("0.37"), Decimal("268")),
    (Decimal("2300"), None, Decimal("0.39"), Decimal("770")),
]
RENTA_EXENTA_PCT = Decimal("0.25")
RENTA_EXENTA_TOPE_UVT_MES = Decimal("790") / Decimal("12")
LIMITE_DEPURACION_PCT = Decimal("0.40")
LIMITE_DEPURACION_UVT_MES = Decimal("1340") / Decimal("12")

# Fondo de solidaridad pensional: (desde SMMLV, tarifa)
ESCALA_FSP = [
    (Decimal("20"), Decimal("0.020")),
    (Decimal("19"), Decimal("0.018")),
    (Decimal("18"), Decimal("0.016")),
    (Decimal("17"), Decimal("0.014")),
    (Decimal("16"), Decimal("0.012")),
    (Decimal("4"), Decimal("0.010")),
]

# Conceptos por días que reemplazan el salario de esos días y su tasa de pago.
TASA_AUSENCIA = {
    "INCL": UNO,
    "LMP": UNO,
    "LREM": UNO,
    "VACD": UNO,
    "LNR": CERO,
    "SUS": CERO,
    # INCG tiene tratamiento especial por tramos
}
ORDEN_AUSENCIAS = ["INCG", "INCL", "LMP", "LREM", "VACD", "LNR", "SUS"]


# --------------------------------------------------------------------------- utilidades

def redondear(valor: Decimal) -> Decimal:
    """Redondea a pesos enteros (mitad hacia arriba)."""
    return Decimal(valor).quantize(UNO, rounding=ROUND_HALF_UP)


def redondear_mil(valor: Decimal) -> Decimal:
    """Redondea al múltiplo de mil más cercano (usado en retención en la fuente)."""
    return (Decimal(valor) / Decimal("1000")).quantize(UNO, rounding=ROUND_HALF_UP) * Decimal("1000")


def _es_ultimo_dia_mes(d: date) -> bool:
    return d.day == calendar.monthrange(d.year, d.month)[1]


def dias360(inicio: date, fin: date) -> int:
    """
    Días entre dos fechas, ambas inclusive, con meses comerciales de 30 días.
    El día 31 y el último día de febrero equivalen al día 30.
    """
    if fin < inicio:
        return 0
    d1 = 30 if (inicio.day == 31 or _es_ultimo_dia_mes(inicio) and inicio.month == 2) else inicio.day
    d2 = 30 if _es_ultimo_dia_mes(fin) else min(fin.day, 30)
    return (fin.year - inicio.year) * 360 + (fin.month - inicio.month) * 30 + (d2 - d1) + 1


def interseccion(a_ini: date, a_fin: date, b_ini: date, b_fin: date):
    ini, fin = max(a_ini, b_ini), min(a_fin, b_fin)
    return (ini, fin) if ini <= fin else None


# --------------------------------------------------------------------------- estructuras

@dataclass
class Linea:
    codigo: str
    valor: Decimal
    cantidad: Decimal = CERO
    base: Decimal = CERO
    tasa: Decimal = CERO
    novedad_id: int | None = None
    prestamo_id: int | None = None


@dataclass
class Resultado:
    dias_periodo: int = 0
    dias_trabajados: int = 0
    ibc: Decimal = CERO
    base_parafiscales: Decimal = CERO
    base_prestaciones: Decimal = CERO
    base_vacaciones: Decimal = CERO
    lineas: list[Linea] = field(default_factory=list)
    advertencias: list[str] = field(default_factory=list)

    def total(self, tipo: str, conceptos: dict) -> Decimal:
        return sum((l.valor for l in self.lineas if conceptos[l.codigo].tipo == tipo), CERO)


# --------------------------------------------------------------------------- motor

class MotorNomina:
    """
    Parámetros
    ----------
    parametros: objeto con los atributos de `ParametroLegal`.
    conceptos:  dict código → objeto con los atributos de `Concepto`.
    exonerada:  si la empresa aplica la exoneración del art. 114-1 E.T.
    """

    def __init__(self, parametros, conceptos: dict, exonerada: bool):
        self.p = parametros
        self.conceptos = conceptos
        self.exonerada = exonerada

    # ------------------------------------------------------------------ API pública

    def liquidar(self, contrato, inicio: date, fin: date, dias_periodo_std: int,
                 novedades=(), prestamos=()) -> Resultado:
        r = Resultado()
        salario = Decimal(contrato.salario)
        integral = contrato.es_integral
        salario_dia = salario / TREINTA

        # 1. Días del contrato en el periodo
        fin_contrato = contrato.fecha_final_efectiva or fin
        tramo = interseccion(inicio, fin, contrato.fecha_inicio, fin_contrato)
        if not tramo:
            return r
        c_ini, c_fin = tramo
        dias = min(dias360(c_ini, c_fin), dias_periodo_std)
        if c_ini == inicio and c_fin == fin:
            dias = dias_periodo_std  # periodo completo: siempre 15 o 30
        r.dias_periodo = dias

        # 2. Ausencias
        dias_ausencia = 0
        dias_sin_pago = 0
        novedades_dia = sorted(
            [n for n in novedades if n.concepto.captura == "DIA"],
            key=lambda n: (ORDEN_AUSENCIAS.index(n.concepto.codigo) if n.concepto.codigo in ORDEN_AUSENCIAS else 99, n.fecha_inicio),
        )
        for nov in novedades_dia:
            cruce = interseccion(c_ini, c_fin, nov.fecha_inicio, nov.fecha_final)
            if not cruce:
                continue
            n_dias = min(dias360(*cruce), dias - dias_ausencia)
            if n_dias <= 0:
                r.advertencias.append(f"Novedad {nov.concepto.codigo} del {nov.fecha_inicio:%d/%m} se cruza con otra ausencia y no se tomó.")
                continue
            dias_ausencia += n_dias
            codigo = nov.concepto.codigo
            if codigo == "INCG":
                previos = dias360(nov.fecha_inicio, cruce[0]) - 1
                self._incapacidad_general(r, nov, n_dias, previos, salario_dia)
            else:
                tasa = TASA_AUSENCIA.get(codigo, UNO)
                if tasa == CERO:
                    dias_sin_pago += n_dias
                r.lineas.append(Linea(codigo, redondear(salario_dia * tasa * n_dias), Decimal(n_dias), redondear(salario_dia), tasa, nov.id))

        # 3. Salario básico
        dias_salario = dias - dias_ausencia
        r.dias_trabajados = dias_salario
        if dias_salario > 0:
            r.lineas.append(Linea("SAL", redondear(salario_dia * dias_salario), Decimal(dias_salario), redondear(salario), Decimal(dias_salario) / TREINTA))

        # 4. Horas extra y recargos
        valor_hora = salario / Decimal(self.p.horas_mes)
        for nov in (n for n in novedades if n.concepto.captura == "HOR"):
            if integral:
                r.advertencias.append(f"{nov.concepto.codigo}: el salario integral ya compensa horas extra y recargos; la novedad no se pagó.")
                continue
            factor = self.factor_hora(nov.concepto.codigo)
            r.lineas.append(Linea(nov.concepto.codigo, redondear(valor_hora * factor * nov.cantidad), nov.cantidad, redondear(valor_hora), factor, nov.id))

        # 5. Pagos y descuentos por valor
        descuentos = []
        for nov in (n for n in novedades if n.concepto.captura == "VAL"):
            if nov.concepto.tipo == "DED":
                descuentos.append(nov)
            else:
                r.lineas.append(Linea(nov.concepto.codigo, redondear(nov.valor), UNO, redondear(nov.valor), UNO, nov.id))

        # 6. Auxilio de transporte
        smmlv = Decimal(self.p.smmlv)
        if not integral and salario <= 2 * smmlv and dias_salario > 0:
            aux = Decimal(self.p.auxilio_transporte)
            r.lineas.append(Linea("AUXT", redondear(aux / TREINTA * dias_salario), Decimal(dias_salario), redondear(aux), Decimal(dias_salario) / TREINTA))

        # 7. IBC
        self._calcular_bases(r, integral, smmlv, dias - dias_sin_pago)

        # 8. Deducciones de ley
        tasa_salud, tasa_pension = Decimal(self.p.pct_salud_empleado), Decimal(self.p.pct_pension_empleado)
        salud = redondear(r.ibc * tasa_salud)
        r.lineas.append(Linea("SALUD", salud, base=r.ibc, tasa=tasa_salud))
        pension = CERO
        if getattr(contrato.empleado, "afp_id", None) or getattr(contrato.empleado, "afp", None):
            pension = redondear(r.ibc * tasa_pension)
            r.lineas.append(Linea("PENS", pension, base=r.ibc, tasa=tasa_pension))
            ibc_mensual = r.ibc * TREINTA / Decimal(dias) if dias else CERO
            tasa_fsp = self.tasa_fsp(ibc_mensual, smmlv)
            if tasa_fsp:
                r.lineas.append(Linea("FSP", redondear(r.ibc * tasa_fsp), base=r.ibc, tasa=tasa_fsp))

        # 9. Retención en la fuente
        self._retencion(r, dias)

        # 10. Préstamos y descuentos sin generar neto negativo
        devengado = r.total("DEV", self.conceptos)
        disponible = devengado - r.total("DED", self.conceptos)
        for pre in prestamos:
            cuota = min(Decimal(pre.valor_cuota), Decimal(pre.saldo), max(disponible, CERO))
            if cuota < Decimal(pre.valor_cuota) and Decimal(pre.saldo) > cuota:
                r.advertencias.append(f"Cuota de {pre.descripcion} ajustada a {cuota:,.0f} por falta de saldo a pagar.")
            if cuota > 0:
                r.lineas.append(Linea(pre.concepto.codigo, redondear(cuota), UNO, redondear(Decimal(pre.saldo)), prestamo_id=pre.id))
                disponible -= cuota
        for nov in descuentos:
            valor = min(Decimal(nov.valor), max(disponible, CERO))
            if valor < nov.valor:
                r.advertencias.append(f"Descuento {nov.observacion or nov.concepto.nombre} ajustado a {valor:,.0f} para no dejar el neto en negativo.")
            if valor > 0:
                r.lineas.append(Linea(nov.concepto.codigo, redondear(valor), UNO, redondear(nov.valor), UNO, nov.id))
                disponible -= valor

        # 11. Aportes del empleador
        self._aportes(r, contrato, smmlv, dias)

        # 12. Provisiones
        self._provisiones(r, integral)
        return r

    # ------------------------------------------------------------------ reglas

    def factor_hora(self, codigo: str) -> Decimal:
        p = self.p
        rn, rdf = Decimal(p.pct_recargo_nocturno), Decimal(p.pct_recargo_dominical)
        hed, hen = Decimal(p.pct_extra_diurna), Decimal(p.pct_extra_nocturna)
        return {
            "RN": rn,
            "HED": UNO + hed,
            "HEN": UNO + hen,
            "HDF": UNO + rdf,
            "HNDF": UNO + rdf + rn,
            "HEDDF": UNO + hed + rdf,
            "HENDF": UNO + hen + rdf,
        }[codigo]

    @staticmethod
    def tasa_fsp(ibc_mensual: Decimal, smmlv: Decimal) -> Decimal:
        veces = ibc_mensual / smmlv if smmlv else CERO
        for desde, tasa in ESCALA_FSP:
            if veces >= desde:
                return tasa
        return CERO

    def _incapacidad_general(self, r: Resultado, nov, n_dias: int, previos: int, salario_dia: Decimal):
        """Días 1 y 2: 100 %. Días 3-90: 66,67 %. Días 91-180: 50 %. Piso: SMMLV diario."""
        minimo_dia = Decimal(self.p.smmlv) / TREINTA
        tramos = {UNO: 0, Decimal("0.6667"): 0, Decimal("0.50"): 0}
        for i in range(previos + 1, previos + n_dias + 1):
            tasa = UNO if i <= 2 else (Decimal("0.6667") if i <= 90 else Decimal("0.50"))
            tramos[tasa] += 1
        for tasa, cant in tramos.items():
            if not cant:
                continue
            diario = salario_dia * tasa
            base, tasa_linea = salario_dia, tasa
            if diario < minimo_dia:
                # Piso legal: la incapacidad no puede ser inferior al SMMLV diario.
                diario, base, tasa_linea = minimo_dia, minimo_dia, UNO
                r.advertencias.append(f"Incapacidad desde el {nov.fecha_inicio:%d/%m}: {cant} día(s) ajustados al SMMLV diario.")
            r.lineas.append(Linea("INCG", redondear(diario * cant), Decimal(cant), redondear(base), tasa_linea, nov.id))

    def _calcular_bases(self, r: Resultado, integral: bool, smmlv: Decimal, dias_cotizables: int):
        c = self.conceptos
        devengados = [l for l in r.lineas if c[l.codigo].tipo == "DEV"]
        base_ss = sum((l.valor for l in devengados if c[l.codigo].base_seguridad_social), CERO)
        base_salarial = sum((l.valor for l in devengados if c[l.codigo].salarial), CERO)
        no_salarial = sum((l.valor for l in devengados if l.codigo in ("BONNS", "AUXNS")), CERO)
        if integral:
            base_ss *= FACTOR_INTEGRAL
            base_salarial *= FACTOR_INTEGRAL
        # Ley 1393 de 2010, art. 30: lo no salarial que exceda el 40 % del total entra al IBC.
        total_rem = base_ss + no_salarial
        exceso = max(no_salarial - total_rem * LIMITE_NO_SALARIAL, CERO)
        if exceso:
            r.advertencias.append(f"Pagos no salariales superan el 40 %: se suman {exceso:,.0f} al IBC.")
        ibc = base_ss + exceso
        if dias_cotizables > 0:
            piso = smmlv * Decimal(dias_cotizables) / TREINTA
            techo = smmlv * 25 * Decimal(dias_cotizables) / TREINTA
            ibc = min(max(ibc, piso), techo)
        r.ibc = redondear(ibc)
        r.base_parafiscales = redondear(min(base_salarial + exceso, r.ibc) if dias_cotizables else CERO)
        r.base_prestaciones = redondear(sum((l.valor for l in devengados if c[l.codigo].base_prestaciones), CERO))
        r.base_vacaciones = redondear(sum((l.valor for l in devengados if c[l.codigo].base_vacaciones), CERO))

    def _retencion(self, r: Resultado, dias: int):
        if not dias:
            return
        uvt = Decimal(self.p.uvt)
        factor = TREINTA / Decimal(dias)  # se lleva el periodo a valor mensual
        ingresos = r.total("DEV", self.conceptos) * factor
        incr = sum((l.valor for l in r.lineas if l.codigo in ("SALUD", "PENS", "FSP")), CERO) * factor
        neto = ingresos - incr
        exenta = min(neto * RENTA_EXENTA_PCT, RENTA_EXENTA_TOPE_UVT_MES * uvt)
        exenta = min(exenta, ingresos * LIMITE_DEPURACION_PCT, LIMITE_DEPURACION_UVT_MES * uvt)
        base_uvt = (neto - exenta) / uvt
        impuesto_uvt = CERO
        for desde, hasta, tarifa, fijo in TABLA_RETENCION:
            if hasta is None or base_uvt <= hasta:
                impuesto_uvt = (base_uvt - desde) * tarifa + fijo if base_uvt > desde else CERO
                break
        if impuesto_uvt <= 0:
            return
        mensual = redondear_mil(impuesto_uvt * uvt)
        valor = redondear(mensual / factor)
        r.lineas.append(Linea("RTEFTE", valor, base=redondear((neto - exenta) / factor), tasa=(valor / ((neto - exenta) / factor)).quantize(Decimal("0.00001"))))

    def _aportes(self, r: Resultado, contrato, smmlv: Decimal, dias: int):
        p = self.p
        ibc_mensual = r.ibc * TREINTA / Decimal(dias) if dias else CERO
        exonerado = self.exonerada and ibc_mensual < smmlv * 10
        lineas = []
        if not exonerado:
            lineas.append(("AP_SAL", r.ibc, Decimal(p.pct_salud_empleador)))
        if getattr(contrato.empleado, "afp_id", None) or getattr(contrato.empleado, "afp", None):
            lineas.append(("AP_PEN", r.ibc, Decimal(p.pct_pension_empleador)))
        lineas.append(("AP_ARL", r.ibc, Decimal(contrato.tarifa_arl)))
        lineas.append(("AP_CCF", r.base_parafiscales, Decimal(p.pct_caja)))
        if not exonerado:
            lineas.append(("AP_ICBF", r.base_parafiscales, Decimal(p.pct_icbf)))
            lineas.append(("AP_SENA", r.base_parafiscales, Decimal(p.pct_sena)))
        for codigo, base, tasa in lineas:
            if base > 0:
                r.lineas.append(Linea(codigo, redondear(base * tasa), base=base, tasa=tasa))

    def _provisiones(self, r: Resultado, integral: bool):
        if not integral and r.base_prestaciones > 0:
            ces = redondear(r.base_prestaciones * PCT_CESANTIAS)
            r.lineas.append(Linea("PR_CES", ces, base=r.base_prestaciones, tasa=PCT_CESANTIAS))
            r.lineas.append(Linea("PR_INT", redondear(ces * PCT_INTERESES), base=ces, tasa=PCT_INTERESES))
            r.lineas.append(Linea("PR_PRI", redondear(r.base_prestaciones * PCT_PRIMA), base=r.base_prestaciones, tasa=PCT_PRIMA))
        if r.base_vacaciones > 0:
            r.lineas.append(Linea("PR_VAC", redondear(r.base_vacaciones * PCT_VACACIONES), base=r.base_vacaciones, tasa=PCT_VACACIONES))
