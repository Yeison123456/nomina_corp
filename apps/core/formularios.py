"""Base de formularios: asigna las clases CSS del sistema a cada control."""
from django import forms


class FormularioBase(forms.ModelForm):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for nombre, field in self.fields.items():
            w = field.widget
            if isinstance(w, forms.CheckboxInput):
                w.attrs["class"] = "control-check"
            elif isinstance(w, forms.Select):
                w.attrs["class"] = "control control--select"
            else:
                w.attrs["class"] = "control"
            if isinstance(w, forms.DateInput):
                w.input_type = "date"
                w.format = "%Y-%m-%d"
            if isinstance(w, forms.Textarea):
                w.attrs["rows"] = 3


class FormularioSimple(forms.Form):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field in self.fields.values():
            w = field.widget
            if isinstance(w, forms.CheckboxInput):
                w.attrs["class"] = "control-check"
            elif isinstance(w, forms.Select):
                w.attrs["class"] = "control control--select"
            else:
                w.attrs["class"] = "control"
            if isinstance(w, forms.DateInput):
                w.input_type = "date"
                w.format = "%Y-%m-%d"
