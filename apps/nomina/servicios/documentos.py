"""
Generación de documentos: desprendibles de pago en PDF y reportes en Excel.
"""
from decimal import Decimal
from io import BytesIO

from openpyxl import Workbook
from openpyxl.styles import Alignment, Border, Font, PatternFill, Side
from openpyxl.utils import get_column_letter
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import mm
from reportlab.pdfgen import canvas

from apps.core.models import Empresa

from ..models import Concepto, DetalleLiquidacion, LiquidacionContrato, LiquidacionNomina, PeriodoNomina

PIZARRA = colors.HexColor("#1F3B3A")
COBRE = colors.HexColor("#9A6A2F")
LINEA = colors.HexColor("#C9CDC8")
TENUE = colors.HexColor("#5E6763")
FONDO = colors.HexColor("#F2F1EC")


def pesos(valor) -> str:
    valor = Decimal(valor or 0)
    signo = "-" if valor < 0 else ""
    return f"{signo}$ {abs(valor):,.0f}".replace(",", ".")


def _cantidad(valor) -> str:
    valor = Decimal(valor or 0)
    if valor == valor.to_integral():
        return f"{valor:,.0f}".replace(",", ".")
    return f"{valor:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


# --------------------------------------------------------------------------- PDF

def _encabezado(c: canvas.Canvas, empresa: Empresa, titulo: str, subtitulo: str, ancho: float, alto: float):
    c.setFillColor(PIZARRA)
    c.rect(0, alto - 26 * mm, ancho, 26 * mm, stroke=0, fill=1)
    c.setFillColor(COBRE)
    c.rect(0, alto - 27.2 * mm, ancho, 1.2 * mm, stroke=0, fill=1)
    c.setFillColor(colors.white)
    c.setFont("Helvetica-Bold", 13)
    c.drawString(18 * mm, alto - 12 * mm, empresa.razon_social.upper())
    c.setFont("Helvetica", 8.5)
    c.drawString(18 * mm, alto - 17.5 * mm, f"NIT {empresa.nit}")
    c.setFillColor(colors.HexColor("#B9C9C6"))
    c.setFont("Helvetica", 7.5)
    c.drawString(18 * mm, alto - 22 * mm, f"{empresa.direccion}  ·  {empresa.ciudad}")
    c.setFillColor(colors.white)
    c.setFont("Helvetica-Bold", 10)
    c.drawRightString(ancho - 18 * mm, alto - 12 * mm, titulo)
    c.setFont("Helvetica", 8.5)
    c.drawRightString(ancho - 18 * mm, alto - 17.5 * mm, subtitulo)


def _campo(c, x, y, etiqueta, valor, ancho_max=None):
    c.setFillColor(TENUE)
    c.setFont("Helvetica", 6.8)
    c.drawString(x, y + 3.6 * mm, etiqueta.upper())
    c.setFillColor(colors.black)
    c.setFont("Helvetica", 9)
    texto = str(valor)
    if ancho_max:
        while c.stringWidth(texto, "Helvetica", 9) > ancho_max and len(texto) > 4:
            texto = texto[:-2]
    c.drawString(x, y, texto)


def _dibujar_desprendible(c: canvas.Canvas, liq: LiquidacionNomina, empresa: Empresa):
    ancho, alto = letter
    periodo = liq.periodo
    contrato = liq.contrato
    emp = contrato.empleado
    _encabezado(c, empresa, "COMPROBANTE DE PAGO DE NÓMINA", f"{periodo.nombre}  ·  {periodo.codigo}", ancho, alto)

    # Datos del empleado
    y = alto - 40 * mm
    col = [18 * mm, 78 * mm, 128 * mm, 168 * mm]
    _campo(c, col[0], y, "Empleado", emp.nombre_completo, 56 * mm)
    _campo(c, col[1], y, "Documento", f"{emp.tipo_documento} {emp.numero_documento}")
    _campo(c, col[2], y, "Contrato", contrato.numero)
    _campo(c, col[3], y, "Fecha de pago", f"{periodo.fecha_pago:%d/%m/%Y}")
    y -= 11 * mm
    _campo(c, col[0], y, "Cargo", contrato.cargo.nombre, 56 * mm)
    _campo(c, col[1], y, "Centro de costo", contrato.centro_costo.nombre, 46 * mm)
    _campo(c, col[2], y, "Salario mensual", pesos(liq.salario))
    _campo(c, col[3], y, "Días liquidados", f"{liq.dias_periodo}")
    y -= 11 * mm
    _campo(c, col[0], y, "EPS", emp.eps.nombre, 56 * mm)
    _campo(c, col[1], y, "Fondo de pensiones", emp.afp.nombre if emp.afp else "No cotiza", 46 * mm)
    _campo(c, col[2], y, "Periodo", f"{periodo.fecha_inicio:%d/%m/%Y} – {periodo.fecha_fin:%d/%m/%Y}")
    _campo(c, col[3], y, "IBC", pesos(liq.ibc))

    # Tablas de devengados y deducciones
    y -= 10 * mm
    detalles = list(liq.detalles.select_related("concepto").order_by("concepto__orden"))
    devengados = [d for d in detalles if d.concepto.tipo == Concepto.Tipo.DEVENGADO]
    deducciones = [d for d in detalles if d.concepto.tipo == Concepto.Tipo.DEDUCCION]

    def tabla(x, ancho_t, titulo, filas, total_etq, total):
        yy = y
        c.setFillColor(FONDO)
        c.rect(x, yy - 6 * mm, ancho_t, 6 * mm, stroke=0, fill=1)
        c.setFillColor(PIZARRA)
        c.setFont("Helvetica-Bold", 8)
        c.drawString(x + 2 * mm, yy - 4.1 * mm, titulo)
        c.drawRightString(x + ancho_t - 30 * mm, yy - 4.1 * mm, "CANT.")
        c.drawRightString(x + ancho_t - 2 * mm, yy - 4.1 * mm, "VALOR")
        yy -= 6 * mm
        c.setFont("Helvetica", 8.5)
        for d in filas:
            yy -= 5.4 * mm
            c.setFillColor(colors.black)
            c.drawString(x + 2 * mm, yy + 1.4 * mm, d.concepto.nombre[:34])
            c.setFillColor(TENUE)
            if d.cantidad:
                c.drawRightString(x + ancho_t - 30 * mm, yy + 1.4 * mm, _cantidad(d.cantidad))
            c.setFillColor(colors.black)
            c.drawRightString(x + ancho_t - 2 * mm, yy + 1.4 * mm, pesos(d.valor))
            c.setStrokeColor(LINEA)
            c.setLineWidth(0.4)
            c.line(x, yy, x + ancho_t, yy)
        return yy, (total_etq, total)

    ancho_t = (ancho - 36 * mm - 8 * mm) / 2
    y1, t1 = tabla(18 * mm, ancho_t, "DEVENGADOS", devengados, "Total devengado", liq.total_devengado)
    y2, t2 = tabla(18 * mm + ancho_t + 8 * mm, ancho_t, "DEDUCCIONES", deducciones, "Total deducciones", liq.total_deducciones)
    y_tot = min(y1, y2) - 7 * mm
    for x, (etq, val) in ((18 * mm, t1), (18 * mm + ancho_t + 8 * mm, t2)):
        c.setStrokeColor(PIZARRA)
        c.setLineWidth(0.8)
        c.line(x, y_tot + 5 * mm, x + ancho_t, y_tot + 5 * mm)
        c.setFillColor(PIZARRA)
        c.setFont("Helvetica-Bold", 9)
        c.drawString(x + 2 * mm, y_tot + 1 * mm, etq.upper())
        c.drawRightString(x + ancho_t - 2 * mm, y_tot + 1 * mm, pesos(val))

    # Neto a pagar
    y_neto = y_tot - 16 * mm
    c.setStrokeColor(PIZARRA)
    c.setLineWidth(1)
    c.rect(18 * mm, y_neto, ancho - 36 * mm, 12 * mm, stroke=1, fill=0)
    c.setFillColor(COBRE)
    c.rect(18 * mm, y_neto, 2 * mm, 12 * mm, stroke=0, fill=1)
    c.setFillColor(PIZARRA)
    c.setFont("Helvetica-Bold", 10)
    c.drawString(24 * mm, y_neto + 4.5 * mm, "NETO A PAGAR")
    c.setFont("Helvetica-Bold", 14)
    c.drawRightString(ancho - 22 * mm, y_neto + 4 * mm, pesos(liq.neto_pagar))
    c.setFont("Helvetica", 8)
    c.setFillColor(TENUE)
    if emp.banco:
        cuenta = f"Consignado en {emp.banco.nombre}, cuenta {emp.get_tipo_cuenta_display().lower()} terminada en {emp.numero_cuenta[-4:]}"
        c.drawString(18 * mm, y_neto - 5 * mm, cuenta)

    # Pie
    c.setFont("Helvetica", 7)
    c.setFillColor(TENUE)
    c.drawString(18 * mm, 14 * mm, "Documento generado por Libra — Sistema de Nómina. Este comprobante no requiere firma.")
    c.drawRightString(ancho - 18 * mm, 14 * mm, f"Liquidación #{liq.pk}")


def desprendible_pdf(liquidaciones) -> bytes:
    """PDF con un desprendible por página."""
    empresa = Empresa.actual()
    buf = BytesIO()
    c = canvas.Canvas(buf, pagesize=letter)
    c.setTitle("Comprobantes de pago de nómina")
    for liq in liquidaciones:
        _dibujar_desprendible(c, liq, empresa)
        c.showPage()
    c.save()
    return buf.getvalue()


def liquidacion_contrato_pdf(liq: LiquidacionContrato, calculo) -> bytes:
    empresa = Empresa.actual()
    ancho, alto = letter
    buf = BytesIO()
    c = canvas.Canvas(buf, pagesize=letter)
    c.setTitle(f"Liquidación de contrato {liq.contrato.numero}")
    _encabezado(c, empresa, "LIQUIDACIÓN DE PRESTACIONES SOCIALES", f"Contrato {liq.contrato.numero}", ancho, alto)
    contrato = liq.contrato
    emp = contrato.empleado
    y = alto - 40 * mm
    col = [18 * mm, 78 * mm, 128 * mm, 168 * mm]
    _campo(c, col[0], y, "Empleado", emp.nombre_completo, 56 * mm)
    _campo(c, col[1], y, "Documento", f"{emp.tipo_documento} {emp.numero_documento}")
    _campo(c, col[2], y, "Fecha de ingreso", f"{contrato.fecha_inicio:%d/%m/%Y}")
    _campo(c, col[3], y, "Fecha de retiro", f"{liq.fecha_retiro:%d/%m/%Y}")
    y -= 11 * mm
    _campo(c, col[0], y, "Cargo", contrato.cargo.nombre, 56 * mm)
    _campo(c, col[1], y, "Tipo de contrato", contrato.get_tipo_display())
    _campo(c, col[2], y, "Causa de terminación", liq.get_causa_display(), 70 * mm)
    y -= 11 * mm
    _campo(c, col[0], y, "Salario mensual", pesos(liq.salario))
    _campo(c, col[1], y, "Auxilio de transporte", pesos(liq.auxilio_transporte))
    _campo(c, col[2], y, "Promedio variable", pesos(liq.promedio_variable))
    _campo(c, col[3], y, "Base liquidación", pesos(liq.base_cesantias))

    filas = [
        ("Cesantías", f"{calculo.dias_cesantias} días", "base × días / 360", liq.cesantias),
        ("Intereses sobre cesantías", f"{calculo.dias_cesantias} días", "cesantías × días × 12 % / 360", liq.intereses_cesantias),
        ("Prima de servicios", f"{calculo.dias_prima} días", "base × días / 360", liq.prima),
        ("Vacaciones compensadas", f"{_cantidad(calculo.dias_vacaciones)} días", "salario / 30 × días pendientes", liq.vacaciones),
    ]
    if liq.indemnizacion:
        filas.append(("Indemnización (art. 64 CST)", f"{_cantidad(calculo.dias_indemnizacion)} días", "salario / 30 × días", liq.indemnizacion))

    y -= 12 * mm
    c.setFillColor(FONDO)
    c.rect(18 * mm, y - 6 * mm, ancho - 36 * mm, 6 * mm, stroke=0, fill=1)
    c.setFillColor(PIZARRA)
    c.setFont("Helvetica-Bold", 8)
    c.drawString(20 * mm, y - 4.1 * mm, "CONCEPTO")
    c.drawString(85 * mm, y - 4.1 * mm, "TIEMPO")
    c.drawString(115 * mm, y - 4.1 * mm, "FÓRMULA")
    c.drawRightString(ancho - 20 * mm, y - 4.1 * mm, "VALOR")
    y -= 6 * mm
    for nombre, tiempo, formula, valor in filas:
        y -= 6 * mm
        c.setFont("Helvetica", 9)
        c.setFillColor(colors.black)
        c.drawString(20 * mm, y + 1.8 * mm, nombre)
        c.setFillColor(TENUE)
        c.drawString(85 * mm, y + 1.8 * mm, tiempo)
        c.setFont("Helvetica", 7.5)
        c.drawString(115 * mm, y + 1.8 * mm, formula)
        c.setFont("Helvetica", 9)
        c.setFillColor(colors.black)
        c.drawRightString(ancho - 20 * mm, y + 1.8 * mm, pesos(valor))
        c.setStrokeColor(LINEA)
        c.setLineWidth(0.4)
        c.line(18 * mm, y, ancho - 18 * mm, y)

    y -= 16 * mm
    c.setStrokeColor(PIZARRA)
    c.setLineWidth(1)
    c.rect(18 * mm, y, ancho - 36 * mm, 12 * mm, stroke=1, fill=0)
    c.setFillColor(COBRE)
    c.rect(18 * mm, y, 2 * mm, 12 * mm, stroke=0, fill=1)
    c.setFillColor(PIZARRA)
    c.setFont("Helvetica-Bold", 10)
    c.drawString(24 * mm, y + 4.5 * mm, "TOTAL A PAGAR")
    c.setFont("Helvetica-Bold", 14)
    c.drawRightString(ancho - 22 * mm, y + 4 * mm, pesos(liq.total))

    y -= 40 * mm
    c.setStrokeColor(colors.black)
    c.setLineWidth(0.5)
    for x, etq in ((18 * mm, "Firma del trabajador"), (ancho / 2 + 10 * mm, "Firma del empleador")):
        c.line(x, y, x + 70 * mm, y)
        c.setFont("Helvetica", 8)
        c.setFillColor(TENUE)
        c.drawString(x, y - 4 * mm, etq)
    c.setFont("Helvetica", 7)
    c.drawString(18 * mm, 14 * mm, f"Estado: {liq.get_estado_display()}  ·  Elaborada el {liq.fecha_elaboracion:%d/%m/%Y}")
    c.showPage()
    c.save()
    return buf.getvalue()


# --------------------------------------------------------------------------- Excel

_FILL_ENC = PatternFill("solid", fgColor="1F3B3A")
_FONT_ENC = Font(bold=True, color="FFFFFF")
_BORDE = Border(bottom=Side(style="thin", color="C9CDC8"))
_FMT_PESOS = '"$" #,##0'


def _hoja(ws, titulo, encabezados, filas, columnas_moneda=()):
    empresa = Empresa.actual()
    ws.append([empresa.razon_social if empresa else ""])
    ws.append([titulo])
    ws["A1"].font = Font(bold=True, size=12, color="1F3B3A")
    ws["A2"].font = Font(size=10, color="5E6763")
    ws.append([])
    ws.append(encabezados)
    for celda in ws[4]:
        celda.fill = _FILL_ENC
        celda.font = _FONT_ENC
        celda.alignment = Alignment(vertical="center")
    for fila in filas:
        ws.append(fila)
    for fila in ws.iter_rows(min_row=5):
        for celda in fila:
            celda.border = _BORDE
            if celda.column in columnas_moneda:
                celda.number_format = _FMT_PESOS
    for i, enc in enumerate(encabezados, start=1):
        largo = max([len(str(enc))] + [len(str(f[i - 1])) for f in filas if i - 1 < len(f)] + [8])
        ws.column_dimensions[get_column_letter(i)].width = min(largo + 3, 45)
    ws.freeze_panes = "A5"


def sabana_excel(periodo: PeriodoNomina) -> bytes:
    """Sábana de nómina: un empleado por fila y un concepto por columna, más resumen por concepto."""
    liqs = list(periodo.liquidaciones.select_related("contrato__empleado", "contrato__cargo", "contrato__centro_costo"))
    detalles = DetalleLiquidacion.objects.filter(liquidacion__periodo=periodo).select_related("concepto")
    conceptos = sorted({d.concepto for d in detalles}, key=lambda c: ("DEV DED INF APO PRO".split().index(c.tipo), c.orden))
    valores = {}
    for d in detalles:
        valores[(d.liquidacion_id, d.concepto_id)] = valores.get((d.liquidacion_id, d.concepto_id), Decimal(0)) + d.valor

    wb = Workbook()
    ws = wb.active
    ws.title = "Sábana"
    enc = ["Documento", "Empleado", "Cargo", "Centro de costo", "Días", "Salario", "IBC"] + [c.nombre for c in conceptos] + [
        "Total devengado", "Total deducciones", "Neto a pagar", "Aportes", "Provisiones", "Costo total"]
    filas = []
    for l in liqs:
        e = l.contrato.empleado
        filas.append([e.numero_documento, e.nombre_completo, l.contrato.cargo.nombre, l.contrato.centro_costo.nombre,
                      l.dias_periodo, l.salario, l.ibc] + [valores.get((l.id, c.id), 0) for c in conceptos] + [
                      l.total_devengado, l.total_deducciones, l.neto_pagar, l.total_aportes, l.total_provisiones, l.costo_total])
    moneda = [6, 7] + list(range(8, len(enc) + 1))
    _hoja(ws, f"Sábana de nómina — {periodo.nombre} ({periodo.codigo})", enc, filas, moneda)

    ws2 = wb.create_sheet("Resumen por concepto")
    filas2 = []
    for c in conceptos:
        total = sum((v for (lid, cid), v in valores.items() if cid == c.id), Decimal(0))
        filas2.append([c.codigo, c.nombre, c.get_tipo_display(), total])
    _hoja(ws2, f"Resumen por concepto — {periodo.codigo}", ["Código", "Concepto", "Tipo", "Valor"], filas2, [4])

    ws3 = wb.create_sheet("Dispersión bancaria")
    filas3 = [[l.contrato.empleado.numero_documento, l.contrato.empleado.nombre_completo,
               l.contrato.empleado.banco.nombre if l.contrato.empleado.banco else "",
               l.contrato.empleado.get_tipo_cuenta_display(), l.contrato.empleado.numero_cuenta, l.neto_pagar] for l in liqs]
    _hoja(ws3, f"Archivo de dispersión — pago {periodo.fecha_pago:%d/%m/%Y}", ["Documento", "Beneficiario", "Banco", "Tipo de cuenta", "Número de cuenta", "Valor"], filas3, [6])

    buf = BytesIO()
    wb.save(buf)
    return buf.getvalue()


def costos_excel(filas, titulo: str) -> bytes:
    wb = Workbook()
    ws = wb.active
    ws.title = "Costos"
    enc = ["Centro de costo", "Empleados", "Devengado", "Aportes", "Provisiones", "Costo total"]
    _hoja(ws, titulo, enc, [[f["centro"], f["empleados"], f["devengado"], f["aportes"], f["provisiones"], f["costo"]] for f in filas], [3, 4, 5, 6])
    buf = BytesIO()
    wb.save(buf)
    return buf.getvalue()
