"""
Modelo de nómina: conceptos, novedades, préstamos, periodos, liquidaciones
periódicas y liquidaciones definitivas de contrato.
"""
from decimal import Decimal

from django.conf import settings
from django.db import models

from apps.personal.models import Contrato

CERO = Decimal("0")


class Concepto(models.Model):
    """Catálogo de conceptos que pueden aparecer en una liquidación."""

    class Tipo(models.TextChoices):
        DEVENGADO = "DEV", "Devengado"
        DEDUCCION = "DED", "Deducción"
        APORTE = "APO", "Aporte del empleador"
        PROVISION = "PRO", "Provisión de prestaciones"
        INFORMATIVO = "INF", "Informativo (ausencia sin pago)"

    class Captura(models.TextChoices):
        SISTEMA = "SIS", "Calculado por el sistema"
        HORAS = "HOR", "Novedad en horas"
        DIAS = "DIA", "Novedad en días (rango de fechas)"
        VALOR = "VAL", "Novedad en valor"

    codigo = models.CharField("código", max_length=10, unique=True)
    nombre = models.CharField(max_length=80)
    tipo = models.CharField(max_length=3, choices=Tipo.choices)
    captura = models.CharField(max_length=3, choices=Captura.choices, default=Captura.SISTEMA)
    salarial = models.BooleanField(default=False, help_text="Constituye salario (art. 127 CST).")
    base_seguridad_social = models.BooleanField("base seguridad social", default=False, help_text="Se suma al IBC.")
    base_prestaciones = models.BooleanField("base prestaciones", default=False, help_text="Se suma a la base de cesantías, intereses y prima.")
    base_vacaciones = models.BooleanField("base vacaciones", default=False, help_text="Se suma a la base de la provisión de vacaciones.")
    orden = models.PositiveSmallIntegerField(default=100, help_text="Orden de presentación en el desprendible.")
    descripcion = models.CharField("descripción", max_length=255, blank=True)
    activo = models.BooleanField(default=True)

    class Meta:
        db_table = "concepto"
        ordering = ["tipo", "orden", "codigo"]
        verbose_name = "concepto"
        verbose_name_plural = "conceptos"

    def __str__(self):
        return f"{self.codigo} · {self.nombre}"


class PeriodoNomina(models.Model):
    """Quincena o mes de nómina. Ciclo de vida: Abierto → Liquidado → Cerrado."""

    class Estado(models.TextChoices):
        BORRADOR = "BOR", "Abierto"
        LIQUIDADO = "LIQ", "Liquidado"
        CERRADO = "CER", "Cerrado"

    periodicidad = models.CharField(max_length=1, choices=Contrato.Periodicidad.choices)
    anio = models.PositiveSmallIntegerField("año")
    mes = models.PositiveSmallIntegerField()
    numero = models.PositiveSmallIntegerField("número", default=1, help_text="1 o 2 para quincenas; 1 para nómina mensual.")
    fecha_inicio = models.DateField("fecha de inicio")
    fecha_fin = models.DateField("fecha final")
    fecha_pago = models.DateField("fecha de pago")
    estado = models.CharField(max_length=3, choices=Estado.choices, default=Estado.BORRADOR)
    observaciones = models.TextField(blank=True)
    liquidado_por = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="+")
    fecha_liquidacion = models.DateTimeField("fecha de liquidación", null=True, blank=True)
    cerrado_por = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name="+")
    fecha_cierre = models.DateTimeField("fecha de cierre", null=True, blank=True)

    class Meta:
        db_table = "periodo_nomina"
        ordering = ["-anio", "-mes", "-numero", "periodicidad"]
        unique_together = [("periodicidad", "anio", "mes", "numero")]
        verbose_name = "periodo de nómina"
        verbose_name_plural = "periodos de nómina"

    MESES = ["", "Enero", "Febrero", "Marzo", "Abril", "Mayo", "Junio", "Julio",
             "Agosto", "Septiembre", "Octubre", "Noviembre", "Diciembre"]

    def __str__(self):
        return self.nombre

    @property
    def codigo(self):
        sufijo = f"Q{self.numero}" if self.periodicidad == Contrato.Periodicidad.QUINCENAL else "M"
        return f"{self.anio}-{self.mes:02d}-{sufijo}"

    @property
    def nombre(self):
        mes = self.MESES[self.mes]
        if self.periodicidad == Contrato.Periodicidad.QUINCENAL:
            orden = "Primera" if self.numero == 1 else "Segunda"
            return f"{orden} quincena de {mes.lower()} {self.anio}"
        return f"Nómina mensual de {mes.lower()} {self.anio}"

    @property
    def dias(self):
        return 15 if self.periodicidad == Contrato.Periodicidad.QUINCENAL else 30

    @property
    def editable(self):
        return self.estado != self.Estado.CERRADO


class Novedad(models.Model):
    """Hechos del periodo que modifican la liquidación de un contrato."""

    class Estado(models.TextChoices):
        PENDIENTE = "PEN", "Pendiente"
        APLICADA = "APL", "Aplicada"
        ANULADA = "ANU", "Anulada"

    contrato = models.ForeignKey(Contrato, on_delete=models.PROTECT, related_name="novedades")
    concepto = models.ForeignKey(Concepto, on_delete=models.PROTECT, related_name="novedades", limit_choices_to={"captura__in": ["HOR", "DIA", "VAL"]})
    fecha_inicio = models.DateField("fecha", help_text="Fecha del hecho o inicio del rango.")
    fecha_fin = models.DateField("fecha final", null=True, blank=True, help_text="Solo para novedades por días.")
    cantidad = models.DecimalField(max_digits=10, decimal_places=2, default=CERO, blank=True, help_text="Horas, o días hábiles en vacaciones.")
    valor = models.DecimalField(max_digits=14, decimal_places=2, default=CERO, blank=True, help_text="Solo para novedades por valor.")
    observacion = models.CharField("observación", max_length=255, blank=True)
    estado = models.CharField(max_length=3, choices=Estado.choices, default=Estado.PENDIENTE)
    periodo_aplicacion = models.ForeignKey(
        PeriodoNomina, null=True, blank=True, on_delete=models.PROTECT, related_name="novedades_aplicadas",
        verbose_name="periodo de aplicación", help_text="Periodo cerrado en el que la novedad quedó aplicada por completo.",
    )
    registrado_por = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL, related_name="+")
    creado = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "novedad"
        ordering = ["-fecha_inicio", "-id"]
        verbose_name = "novedad"
        verbose_name_plural = "novedades"

    def __str__(self):
        return f"{self.concepto.codigo} · {self.contrato.empleado} · {self.fecha_inicio:%d/%m/%Y}"

    @property
    def fecha_final(self):
        return self.fecha_fin or self.fecha_inicio


class Prestamo(models.Model):
    """Préstamos y libranzas que se descuentan en cuotas por periodo."""

    class Estado(models.TextChoices):
        ACTIVO = "ACT", "Activo"
        PAGADO = "PAG", "Pagado"
        ANULADO = "ANU", "Anulado"

    contrato = models.ForeignKey(Contrato, on_delete=models.PROTECT, related_name="prestamos")
    concepto = models.ForeignKey(Concepto, on_delete=models.PROTECT, related_name="+", limit_choices_to={"tipo": "DED", "captura": "SIS", "codigo__in": ["PREST", "LIBR"]})
    descripcion = models.CharField("descripción", max_length=150)
    fecha = models.DateField("fecha de desembolso")
    monto = models.DecimalField(max_digits=14, decimal_places=2)
    numero_cuotas = models.PositiveSmallIntegerField("número de cuotas")
    valor_cuota = models.DecimalField("valor de la cuota", max_digits=14, decimal_places=2)
    saldo = models.DecimalField(max_digits=14, decimal_places=2)
    estado = models.CharField(max_length=3, choices=Estado.choices, default=Estado.ACTIVO)
    creado = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "prestamo"
        ordering = ["-fecha"]
        verbose_name = "préstamo"
        verbose_name_plural = "préstamos"

    def __str__(self):
        return f"{self.descripcion} · {self.contrato.empleado}"


class LiquidacionNomina(models.Model):
    """Resultado de liquidar un contrato en un periodo (encabezado)."""

    periodo = models.ForeignKey(PeriodoNomina, on_delete=models.CASCADE, related_name="liquidaciones")
    contrato = models.ForeignKey(Contrato, on_delete=models.PROTECT, related_name="liquidaciones")
    salario = models.DecimalField("salario mensual", max_digits=14, decimal_places=2)
    dias_periodo = models.PositiveSmallIntegerField("días del contrato en el periodo")
    dias_trabajados = models.PositiveSmallIntegerField("días pagados como salario")
    ibc = models.DecimalField("IBC", max_digits=14, decimal_places=2, help_text="Ingreso base de cotización.")
    base_prestaciones = models.DecimalField("base de prestaciones", max_digits=14, decimal_places=2)
    total_devengado = models.DecimalField("total devengado", max_digits=14, decimal_places=2)
    total_deducciones = models.DecimalField("total deducciones", max_digits=14, decimal_places=2)
    neto_pagar = models.DecimalField("neto a pagar", max_digits=14, decimal_places=2)
    total_aportes = models.DecimalField("total aportes empleador", max_digits=14, decimal_places=2)
    total_provisiones = models.DecimalField("total provisiones", max_digits=14, decimal_places=2)
    advertencias = models.TextField(blank=True, help_text="Observaciones generadas por el motor de cálculo, una por línea.")
    creado = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "liquidacion_nomina"
        ordering = ["contrato__empleado__apellidos"]
        unique_together = [("periodo", "contrato")]
        verbose_name = "liquidación de nómina"
        verbose_name_plural = "liquidaciones de nómina"

    def __str__(self):
        return f"{self.periodo.codigo} · {self.contrato.empleado}"

    @property
    def costo_total(self):
        return self.total_devengado + self.total_aportes + self.total_provisiones


class DetalleLiquidacion(models.Model):
    """Línea de una liquidación: un concepto con su cantidad, base, tasa y valor."""

    liquidacion = models.ForeignKey(LiquidacionNomina, on_delete=models.CASCADE, related_name="detalles")
    concepto = models.ForeignKey(Concepto, on_delete=models.PROTECT, related_name="+")
    cantidad = models.DecimalField(max_digits=10, decimal_places=2, default=CERO, help_text="Días u horas, según el concepto.")
    base = models.DecimalField(max_digits=14, decimal_places=2, default=CERO)
    tasa = models.DecimalField(max_digits=8, decimal_places=5, default=CERO, help_text="Porcentaje o factor aplicado sobre la base.")
    valor = models.DecimalField(max_digits=14, decimal_places=2)
    novedad = models.ForeignKey(Novedad, null=True, blank=True, on_delete=models.SET_NULL, related_name="detalles")
    prestamo = models.ForeignKey(Prestamo, null=True, blank=True, on_delete=models.SET_NULL, related_name="cuotas")

    class Meta:
        db_table = "detalle_liquidacion"
        ordering = ["concepto__tipo", "concepto__orden"]
        verbose_name = "detalle de liquidación"
        verbose_name_plural = "detalles de liquidación"

    def __str__(self):
        return f"{self.concepto.codigo} {self.valor}"


class LiquidacionContrato(models.Model):
    """Liquidación definitiva de prestaciones sociales al terminar un contrato."""

    class Causa(models.TextChoices):
        RENUNCIA = "REN", "Renuncia voluntaria"
        MUTUO = "MUT", "Mutuo acuerdo"
        VENCIMIENTO = "VEN", "Vencimiento del término pactado"
        JUSTA_CAUSA = "JUS", "Despido con justa causa"
        SIN_JUSTA_CAUSA = "SJC", "Despido sin justa causa"

    class Estado(models.TextChoices):
        BORRADOR = "BOR", "Borrador"
        APROBADA = "APR", "Aprobada"

    contrato = models.OneToOneField(Contrato, on_delete=models.PROTECT, related_name="liquidacion_definitiva")
    fecha_retiro = models.DateField("fecha de retiro")
    causa = models.CharField(max_length=3, choices=Causa.choices)
    salario = models.DecimalField("salario mensual", max_digits=14, decimal_places=2)
    auxilio_transporte = models.DecimalField("auxilio de transporte", max_digits=14, decimal_places=2, default=CERO)
    promedio_variable = models.DecimalField("promedio salarial variable", max_digits=14, decimal_places=2, default=CERO)
    dias_cesantias = models.PositiveIntegerField("días para cesantías")
    base_cesantias = models.DecimalField("base de cesantías y prima", max_digits=14, decimal_places=2)
    cesantias = models.DecimalField("cesantías", max_digits=14, decimal_places=2)
    intereses_cesantias = models.DecimalField("intereses sobre cesantías", max_digits=14, decimal_places=2)
    dias_prima = models.PositiveIntegerField("días para prima")
    prima = models.DecimalField("prima de servicios", max_digits=14, decimal_places=2)
    dias_vacaciones = models.DecimalField("días de vacaciones pendientes", max_digits=8, decimal_places=2)
    vacaciones = models.DecimalField("vacaciones compensadas", max_digits=14, decimal_places=2)
    indemnizacion = models.DecimalField("indemnización", max_digits=14, decimal_places=2, default=CERO)
    total = models.DecimalField(max_digits=14, decimal_places=2)
    estado = models.CharField(max_length=3, choices=Estado.choices, default=Estado.BORRADOR)
    observaciones = models.TextField(blank=True)
    elaborado_por = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL, related_name="+")
    fecha_elaboracion = models.DateTimeField("fecha de elaboración", auto_now_add=True)

    class Meta:
        db_table = "liquidacion_contrato"
        ordering = ["-fecha_retiro"]
        verbose_name = "liquidación de contrato"
        verbose_name_plural = "liquidaciones de contrato"

    def __str__(self):
        return f"Liquidación {self.contrato.numero}"

    @property
    def prestaciones(self):
        """Total sin indemnización: cesantías, intereses, prima y vacaciones."""
        return self.total - self.indemnizacion
