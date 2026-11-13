"""
Catálogos generales: empresa, parámetros legales, entidades del sistema de
seguridad social y bitácora de auditoría.
"""
from decimal import Decimal

from django.conf import settings
from django.db import models


class Empresa(models.Model):
    """Datos del empleador. El sistema opera con una sola empresa (registro único)."""

    razon_social = models.CharField("razón social", max_length=150)
    nit = models.CharField("NIT", max_length=20, help_text="NIT con dígito de verificación.")
    direccion = models.CharField("dirección", max_length=150)
    ciudad = models.CharField(max_length=80)
    telefono = models.CharField("teléfono", max_length=30, blank=True)
    correo = models.EmailField("correo de nómina", blank=True)
    representante_legal = models.CharField("representante legal", max_length=120)
    actividad_economica = models.CharField("actividad económica", max_length=150, blank=True)
    exonerada_aportes = models.BooleanField(
        "exonerada art. 114-1 E.T.",
        default=True,
        help_text="Si es verdadero, no paga salud empleador, SENA ni ICBF por trabajadores que devenguen menos de 10 SMMLV.",
    )

    class Meta:
        db_table = "empresa"
        verbose_name = "empresa"
        verbose_name_plural = "empresa"

    def __str__(self):
        return self.razon_social

    @classmethod
    def actual(cls):
        return cls.objects.order_by("id").first()


class ParametroLegal(models.Model):
    """
    Valores legales vigentes a partir de una fecha. Para liquidar un periodo se
    usa el registro con la mayor `vigente_desde` que sea menor o igual a la
    fecha final del periodo.
    """

    vigente_desde = models.DateField("vigente desde", unique=True)
    descripcion = models.CharField("descripción", max_length=150, help_text="Norma o motivo del cambio.")
    smmlv = models.DecimalField("SMMLV", max_digits=14, decimal_places=2, help_text="Salario mínimo mensual legal vigente.")
    auxilio_transporte = models.DecimalField("auxilio de transporte", max_digits=14, decimal_places=2)
    uvt = models.DecimalField("UVT", max_digits=14, decimal_places=2, help_text="Unidad de valor tributario del año.")
    horas_mes = models.PositiveSmallIntegerField(
        "horas laborales al mes", help_text="Divisor para el valor de la hora ordinaria (jornada semanal × 5)."
    )
    pct_recargo_nocturno = models.DecimalField("% recargo nocturno", max_digits=6, decimal_places=4, default=Decimal("0.35"))
    pct_recargo_dominical = models.DecimalField("% recargo dominical y festivo", max_digits=6, decimal_places=4)
    pct_extra_diurna = models.DecimalField("% hora extra diurna", max_digits=6, decimal_places=4, default=Decimal("0.25"))
    pct_extra_nocturna = models.DecimalField("% hora extra nocturna", max_digits=6, decimal_places=4, default=Decimal("0.75"))
    pct_salud_empleado = models.DecimalField("% salud empleado", max_digits=6, decimal_places=4, default=Decimal("0.04"))
    pct_pension_empleado = models.DecimalField("% pensión empleado", max_digits=6, decimal_places=4, default=Decimal("0.04"))
    pct_salud_empleador = models.DecimalField("% salud empleador", max_digits=6, decimal_places=4, default=Decimal("0.085"))
    pct_pension_empleador = models.DecimalField("% pensión empleador", max_digits=6, decimal_places=4, default=Decimal("0.12"))
    pct_caja = models.DecimalField("% caja de compensación", max_digits=6, decimal_places=4, default=Decimal("0.04"))
    pct_icbf = models.DecimalField("% ICBF", max_digits=6, decimal_places=4, default=Decimal("0.03"))
    pct_sena = models.DecimalField("% SENA", max_digits=6, decimal_places=4, default=Decimal("0.02"))

    class Meta:
        db_table = "parametro_legal"
        ordering = ["-vigente_desde"]
        verbose_name = "parámetro legal"
        verbose_name_plural = "parámetros legales"

    def __str__(self):
        return f"Parámetros desde {self.vigente_desde:%d/%m/%Y}"

    @classmethod
    def vigente(cls, fecha):
        return cls.objects.filter(vigente_desde__lte=fecha).order_by("-vigente_desde").first()


class Entidad(models.Model):
    """Entidades del sistema de seguridad social y bancos."""

    class Tipo(models.TextChoices):
        EPS = "EPS", "EPS (salud)"
        AFP = "AFP", "Fondo de pensiones"
        CESANTIAS = "CES", "Fondo de cesantías"
        CAJA = "CCF", "Caja de compensación"
        ARL = "ARL", "Administradora de riesgos laborales"
        BANCO = "BAN", "Banco"

    tipo = models.CharField(max_length=3, choices=Tipo.choices)
    nombre = models.CharField(max_length=120)
    nit = models.CharField("NIT", max_length=20, blank=True)
    codigo = models.CharField("código", max_length=12, blank=True, help_text="Código interno o bancario de la entidad.")
    activa = models.BooleanField(default=True)

    class Meta:
        db_table = "entidad"
        ordering = ["tipo", "nombre"]
        unique_together = [("tipo", "nombre")]
        verbose_name = "entidad"
        verbose_name_plural = "entidades"

    def __str__(self):
        return self.nombre


class Auditoria(models.Model):
    """Bitácora de acciones relevantes realizadas por los usuarios."""

    fecha = models.DateTimeField(auto_now_add=True)
    usuario = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, on_delete=models.SET_NULL, related_name="+")
    accion = models.CharField("acción", max_length=40)
    objeto = models.CharField(max_length=120, help_text="Tipo e identificador del registro afectado.")
    detalle = models.TextField(blank=True)

    class Meta:
        db_table = "auditoria"
        ordering = ["-fecha"]
        verbose_name = "registro de auditoría"
        verbose_name_plural = "auditoría"

    def __str__(self):
        return f"{self.fecha:%Y-%m-%d %H:%M} {self.accion} {self.objeto}"
