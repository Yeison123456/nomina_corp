from django import forms
from django.contrib.auth.models import Group, User

from .formularios import FormularioBase
from .models import Empresa, Entidad, ParametroLegal
from .roles import ROLES


class EmpresaForm(FormularioBase):
    class Meta:
        model = Empresa
        fields = "__all__"


class ParametroLegalForm(FormularioBase):
    class Meta:
        model = ParametroLegal
        fields = "__all__"


class EntidadForm(FormularioBase):
    class Meta:
        model = Entidad
        fields = "__all__"


class UsuarioForm(FormularioBase):
    rol = forms.ChoiceField(choices=[(r, r) for r in ROLES])
    clave = forms.CharField(
        label="contraseña", required=False, widget=forms.PasswordInput,
        help_text="Mínimo 8 caracteres. Déjela vacía para conservar la actual.",
    )

    class Meta:
        model = User
        fields = ["username", "first_name", "last_name", "email", "is_active"]
        labels = {"username": "usuario", "first_name": "nombres", "last_name": "apellidos", "is_active": "activo"}

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance.pk:
            grupo = self.instance.groups.first()
            self.fields["rol"].initial = grupo.name if grupo else None
        else:
            self.fields["clave"].required = True
            self.fields["clave"].help_text = "Mínimo 8 caracteres."

    def clean_clave(self):
        clave = self.cleaned_data.get("clave")
        if clave and len(clave) < 8:
            raise forms.ValidationError("La contraseña debe tener al menos 8 caracteres.")
        return clave

    def save(self, commit=True):
        usuario = super().save(commit=False)
        if self.cleaned_data.get("clave"):
            usuario.set_password(self.cleaned_data["clave"])
        usuario.save()
        grupo, _ = Group.objects.get_or_create(name=self.cleaned_data["rol"])
        usuario.groups.set([grupo])
        return usuario
