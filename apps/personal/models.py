"""
Estructura organizacional y personal: centros de costo, áreas, cargos,
empleados y contratos laborales.
"""
from decimal import Decimal

from django.db import models

from apps.core.models import Entidad


class CentroCosto(models.Model):
    """Agrupación contable a la que se imputa el costo de la nómina."""

    codigo = models.CharField("código", max_length=10, unique=True)
    nombre = models.CharField(max_length=100)
    activo = models.BooleanField(default=True)

    class Meta:
        db_table = "centro_costo"
        ordering = ["codigo"]
        verbose_name = "centro de costo"
        verbose_name_plural = "centros de costo"

    def __str__(self):
        return f"{self.codigo} · {self.nombre}"


class Area(models.Model):
    """Dependencia de la empresa. Pertenece a un centro de costo."""

    codigo = models.CharField("código", max_length=10, unique=True)
    nombre = models.CharField(max_length=100)
    centro_costo = models.ForeignKey(CentroCosto, on_delete=models.PROTECT, related_name="areas")

    class Meta:
        db_table = "area"
        ordering = ["nombre"]
        verbose_name = "área"
        verbose_name_plural = "áreas"

    def __str__(self):
        return self.nombre


class Cargo(models.Model):
    """Puesto de trabajo con su salario de referencia."""

    codigo = models.CharField("código", max_length=10, unique=True)
    nombre = models.CharField(max_length=100)
    area = models.ForeignKey(Area, on_delete=models.PROTECT, related_name="cargos")
    salario_referencia = models.DecimalField(
        "salario de referencia", max_digits=14, decimal_places=2, default=Decimal("0"),
        help_text="Valor sugerido al crear un contrato para este cargo.",
    )

    class Meta:
        db_table = "cargo"
        ordering = ["nombre"]
        verbose_name = "cargo"
        verbose_name_plural = "cargos"

    def __str__(self):
        return self.nombre


class Empleado(models.Model):
    """Datos personales, cuenta de pago y afiliaciones a seguridad social del trabajador."""

    class TipoDocumento(models.TextChoices):
        CC = "CC", "Cédula de ciudadanía"
        CE = "CE", "Cédula de extranjería"
        PA = "PA", "Pasaporte"
        PPT = "PPT", "Permiso por protección temporal"

    class Genero(models.TextChoices):
        F = "F", "Femenino"
        M = "M", "Masculino"
        O = "O", "Otro / no informa"

    class TipoCuenta(models.TextChoices):
        AHORROS = "AH", "Ahorros"
        CORRIENTE = "CC", "Corriente"

    tipo_documento = models.CharField("tipo de documento", max_length=3, choices=TipoDocumento.choices, default=TipoDocumento.CC)
    numero_documento = models.CharField("número de documento", max_length=20, unique=True)
    nombres = models.CharField(max_length=80)
    apellidos = models.CharField(max_length=80)
    fecha_nacimiento = models.DateField("fecha de nacimiento")
    genero = models.CharField("género", max_length=1, choices=Genero.choices)
    correo = models.EmailField(blank=True)
    telefono = models.CharField("teléfono", max_length=30, blank=True)
    direccion = models.CharField("dirección", max_length=150, blank=True)
    ciudad = models.CharField(max_length=80, default="Bogotá D.C.")
    banco = models.ForeignKey(
        Entidad, null=True, blank=True, on_delete=models.PROTECT, related_name="+",
        limit_choices_to={"tipo": Entidad.Tipo.BANCO},
    )
    tipo_cuenta = models.CharField("tipo de cuenta", max_length=2, choices=TipoCuenta.choices, blank=True)
    numero_cuenta = models.CharField("número de cuenta", max_length=30, blank=True)
    eps = models.ForeignKey(Entidad, on_delete=models.PROTECT, related_name="+", limit_choices_to={"tipo": Entidad.Tipo.EPS}, verbose_name="EPS")
    afp = models.ForeignKey(
        Entidad, null=True, blank=True, on_delete=models.PROTECT, related_name="+",
        limit_choices_to={"tipo": Entidad.Tipo.AFP}, verbose_name="fondo de pensiones",
        help_text="Vacío solo para pensionados o trabajadores no obligados a cotizar.",
    )
    fondo_cesantias = models.ForeignKey(
        Entidad, null=True, blank=True, on_delete=models.PROTECT, related_name="+",
        limit_choices_to={"tipo": Entidad.Tipo.CESANTIAS}, verbose_name="fondo de cesantías",
    )
    caja = models.ForeignKey(Entidad, on_delete=models.PROTECT, related_name="+", limit_choices_to={"tipo": Entidad.Tipo.CAJA}, verbose_name="caja de compensación")
    activo = models.BooleanField(default=True)
    creado = models.DateTimeField(auto_now_add=True)
    actualizado = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "empleado"
        ordering = ["apellidos", "nombres"]
        verbose_name = "empleado"
        verbose_name_plural = "empleados"

    def __str__(self):
        return self.nombre_completo

    @property
    def nombre_completo(self):
        return f"{self.nombres} {self.apellidos}"

    @property
    def contrato_vigente(self):
        return self.contratos.filter(estado=Contrato.Estado.VIGENTE).order_by("-fecha_inicio").first()


class Contrato(models.Model):
    """Vínculo laboral: condiciones salariales, periodicidad de pago, cargo y riesgo ARL."""

    class Tipo(models.TextChoices):
        INDEFINIDO = "IND", "Término indefinido"
        FIJO = "FIJ", "Término fijo"
        OBRA = "OBR", "Obra o labor"

    class TipoSalario(models.TextChoices):
        ORDINARIO = "ORD", "Ordinario"
        INTEGRAL = "INT", "Integral"

    class Periodicidad(models.TextChoices):
        QUINCENAL = "Q", "Quincenal"
        MENSUAL = "M", "Mensual"

    class Estado(models.TextChoices):
        VIGENTE = "VIG", "Vigente"
        TERMINADO = "TER", "Terminado"

    class ClaseRiesgo(models.IntegerChoices):
        I = 1, "Clase I — 0,522 %"
        II = 2, "Clase II — 1,044 %"
        III = 3, "Clase III — 2,436 %"
        IV = 4, "Clase IV — 4,350 %"
        V = 5, "Clase V — 6,960 %"

    TARIFA_ARL = {
        1: Decimal("0.00522"),
        2: Decimal("0.01044"),
        3: Decimal("0.02436"),
        4: Decimal("0.04350"),
        5: Decimal("0.06960"),
    }

    numero = models.CharField("número de contrato", max_length=20, unique=True)
    empleado = models.ForeignKey(Empleado, on_delete=models.PROTECT, related_name="contratos")
    tipo = models.CharField("tipo de contrato", max_length=3, choices=Tipo.choices)
    tipo_salario = models.CharField("tipo de salario", max_length=3, choices=TipoSalario.choices, default=TipoSalario.ORDINARIO)
    salario = models.DecimalField("salario mensual", max_digits=14, decimal_places=2)
    cargo = models.ForeignKey(Cargo, on_delete=models.PROTECT, related_name="contratos")
    centro_costo = models.ForeignKey(CentroCosto, on_delete=models.PROTECT, related_name="contratos", verbose_name="centro de costo")
    periodicidad = models.CharField("periodicidad de pago", max_length=1, choices=Periodicidad.choices, default=Periodicidad.QUINCENAL)
    clase_riesgo = models.PositiveSmallIntegerField("clase de riesgo ARL", choices=ClaseRiesgo.choices, default=ClaseRiesgo.I)
    arl = models.ForeignKey(Entidad, on_delete=models.PROTECT, related_name="+", limit_choices_to={"tipo": Entidad.Tipo.ARL}, verbose_name="ARL")
    fecha_inicio = models.DateField("fecha de inicio")
    fecha_fin = models.DateField("fecha de finalización pactada", null=True, blank=True, help_text="Obligatoria para contratos a término fijo.")
    estado = models.CharField(max_length=3, choices=Estado.choices, default=Estado.VIGENTE)
    fecha_terminacion = models.DateField("fecha de terminación", null=True, blank=True)
    motivo_terminacion = models.CharField("motivo de terminación", max_length=150, blank=True)

    class Meta:
        db_table = "contrato"
        ordering = ["-fecha_inicio"]
        verbose_name = "contrato"
        verbose_name_plural = "contratos"

    def __str__(self):
        return f"{self.numero} · {self.empleado}"

    @property
    def es_integral(self):
        return self.tipo_salario == self.TipoSalario.INTEGRAL

    @property
    def tarifa_arl(self):
        return self.TARIFA_ARL[self.clase_riesgo]

    @property
    def fecha_final_efectiva(self):
        """
        Último día en que el contrato produce efectos para la nómina. La fecha
        pactada (`fecha_fin`) no corta la nómina: si llega sin terminación
        registrada, el contrato se entiende prorrogado.
        """
        return self.fecha_terminacion
