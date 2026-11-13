from decimal import Decimal

from django import forms
from django.utils import timezone

from apps.core.formularios import FormularioBase
from apps.core.models import ParametroLegal

from .models import Area, Cargo, CentroCosto, Contrato, Empleado


class EmpleadoForm(FormularioBase):
    class Meta:
        model = Empleado
        exclude = ["creado", "actualizado"]


class ContratoForm(FormularioBase):
    class Meta:
        model = Contrato
        exclude = ["empleado", "estado", "fecha_terminacion", "motivo_terminacion"]

    def clean(self):
        datos = super().clean()
        tipo = datos.get("tipo")
        inicio, fin = datos.get("fecha_inicio"), datos.get("fecha_fin")
        if tipo == Contrato.Tipo.FIJO and not fin:
            self.add_error("fecha_fin", "Los contratos a término fijo requieren fecha de finalización.")
        if inicio and fin and fin <= inicio:
            self.add_error("fecha_fin", "Debe ser posterior a la fecha de inicio.")
        salario = datos.get("salario")
        params = ParametroLegal.vigente(inicio or timezone.localdate())
        if salario and params:
            if salario < params.smmlv:
                self.add_error("salario", f"No puede ser inferior al SMMLV ({params.smmlv:,.0f}).".replace(",", "."))
            if datos.get("tipo_salario") == Contrato.TipoSalario.INTEGRAL and salario < params.smmlv * Decimal("13"):
                self.add_error("salario", "El salario integral debe ser de al menos 13 SMMLV (10 + 30 % de factor prestacional).")
        return datos


class CentroCostoForm(FormularioBase):
    class Meta:
        model = CentroCosto
        fields = "__all__"


class AreaForm(FormularioBase):
    class Meta:
        model = Area
        fields = "__all__"


class CargoForm(FormularioBase):
    class Meta:
        model = Cargo
        fields = "__all__"


class FiltroEmpleadosForm(forms.Form):
    q = forms.CharField(required=False)
    estado = forms.ChoiceField(required=False, choices=[("", "Todos"), ("1", "Activos"), ("0", "Retirados")])
    centro = forms.ModelChoiceField(required=False, queryset=CentroCosto.objects.all(), empty_label="Todos los centros")
