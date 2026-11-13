from decimal import Decimal, ROUND_UP

from django import forms
from django.utils import timezone

from apps.core.formularios import FormularioBase, FormularioSimple
from apps.personal.models import Contrato

from .models import Concepto, LiquidacionContrato, Novedad, PeriodoNomina, Prestamo
from .servicios.liquidador import fechas_periodo


class ContratoChoiceField(forms.ModelChoiceField):
    def label_from_instance(self, obj):
        return f"{obj.empleado.apellidos} {obj.empleado.nombres} — {obj.numero} ({obj.get_periodicidad_display().lower()})"


def contratos_vigentes():
    return Contrato.objects.filter(estado=Contrato.Estado.VIGENTE).select_related("empleado").order_by("empleado__apellidos")


class PeriodoForm(FormularioBase):
    class Meta:
        model = PeriodoNomina
        fields = ["periodicidad", "anio", "mes", "numero", "fecha_pago", "observaciones"]
        widgets = {"mes": forms.Select(choices=[(i, PeriodoNomina.MESES[i]) for i in range(1, 13)]),
                   "numero": forms.Select(choices=[(1, "1 — primera quincena / mes completo"), (2, "2 — segunda quincena")])}

    def clean(self):
        datos = super().clean()
        per, anio, mes, num = datos.get("periodicidad"), datos.get("anio"), datos.get("mes"), datos.get("numero")
        if per == Contrato.Periodicidad.MENSUAL:
            datos["numero"] = 1
            num = 1
        if per and anio and mes and num:
            if PeriodoNomina.objects.filter(periodicidad=per, anio=anio, mes=mes, numero=num).exclude(pk=self.instance.pk).exists():
                raise forms.ValidationError("Ya existe un periodo con esa periodicidad, año, mes y número.")
            self.instance.fecha_inicio, self.instance.fecha_fin = fechas_periodo(per, anio, mes, num)
            pago = datos.get("fecha_pago")
            if pago and pago < self.instance.fecha_inicio:
                self.add_error("fecha_pago", "La fecha de pago no puede ser anterior al inicio del periodo.")
        return datos


class NovedadForm(FormularioBase):
    contrato = ContratoChoiceField(queryset=contratos_vigentes(), label="empleado / contrato")

    class Meta:
        model = Novedad
        fields = ["contrato", "concepto", "fecha_inicio", "fecha_fin", "cantidad", "valor", "observacion"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["contrato"].queryset = contratos_vigentes()
        self.fields["concepto"].queryset = Concepto.objects.filter(activo=True, captura__in=["HOR", "DIA", "VAL"]).order_by("captura", "orden")
        # Mapa concepto → tipo de captura, para que la interfaz muestre solo los campos que aplican
        self.capturas = {str(pk): cap for pk, cap in Concepto.objects.values_list("pk", "captura")}

    def clean(self):
        datos = super().clean()
        concepto = datos.get("concepto")
        if not concepto:
            return datos
        ini, fin = datos.get("fecha_inicio"), datos.get("fecha_fin")
        if concepto.captura == "HOR":
            if not datos.get("cantidad") or datos["cantidad"] <= 0:
                self.add_error("cantidad", "Indique el número de horas.")
            if (datos.get("cantidad") or 0) > 48:
                self.add_error("cantidad", "Registre las horas por evento; más de 48 horas en una novedad no es razonable.")
            datos["fecha_fin"], datos["valor"] = None, Decimal(0)
        elif concepto.captura == "DIA":
            if not fin:
                self.add_error("fecha_fin", "Las novedades por días requieren fecha final.")
            elif ini and fin < ini:
                self.add_error("fecha_fin", "Debe ser igual o posterior a la fecha inicial.")
            if concepto.codigo == "VACD" and (not datos.get("cantidad") or datos["cantidad"] <= 0):
                self.add_error("cantidad", "Indique los días hábiles de vacaciones que se descuentan del saldo.")
            if concepto.codigo != "VACD":
                datos["cantidad"] = Decimal(0)
            datos["valor"] = Decimal(0)
        else:
            if not datos.get("valor") or datos["valor"] <= 0:
                self.add_error("valor", "Indique el valor.")
            datos["fecha_fin"], datos["cantidad"] = None, Decimal(0)
        contrato = datos.get("contrato")
        if contrato and ini and ini < contrato.fecha_inicio:
            self.add_error("fecha_inicio", "La fecha es anterior al inicio del contrato.")
        return datos


class PrestamoForm(FormularioBase):
    contrato = ContratoChoiceField(queryset=contratos_vigentes(), label="empleado / contrato")
    valor_cuota = forms.DecimalField(label="valor de la cuota", required=False, help_text="Si se deja vacío se calcula como monto / cuotas.")

    class Meta:
        model = Prestamo
        fields = ["contrato", "concepto", "descripcion", "fecha", "monto", "numero_cuotas", "valor_cuota"]

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["contrato"].queryset = contratos_vigentes()
        self.fields["concepto"].queryset = Concepto.objects.filter(codigo__in=["PREST", "LIBR"])

    def clean(self):
        datos = super().clean()
        monto, cuotas = datos.get("monto"), datos.get("numero_cuotas")
        if monto is not None and monto <= 0:
            self.add_error("monto", "Debe ser mayor que cero.")
        if cuotas is not None and cuotas <= 0:
            self.add_error("numero_cuotas", "Debe ser mayor que cero.")
        if monto and cuotas and not datos.get("valor_cuota"):
            datos["valor_cuota"] = (monto / cuotas).quantize(Decimal("1"), rounding=ROUND_UP)
        return datos

    def save(self, commit=True):
        obj = super().save(commit=False)
        obj.valor_cuota = self.cleaned_data["valor_cuota"]
        if not obj.pk:
            obj.saldo = obj.monto
        obj.save()
        return obj


class LiquidacionContratoForm(FormularioSimple):
    contrato = ContratoChoiceField(queryset=contratos_vigentes(), label="empleado / contrato")
    fecha_retiro = forms.DateField(label="fecha de retiro", widget=forms.DateInput)
    causa = forms.ChoiceField(choices=LiquidacionContrato.Causa.choices, label="causa de terminación")
    observaciones = forms.CharField(required=False, widget=forms.Textarea(attrs={"rows": 2}))

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["contrato"].queryset = contratos_vigentes().filter(liquidacion_definitiva__isnull=True)
        self.fields["fecha_retiro"].initial = timezone.localdate()
