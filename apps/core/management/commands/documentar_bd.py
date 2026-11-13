"""
Genera la documentación de la base de datos a partir de los modelos:

* docs/base-de-datos/diagrama-er.md   — diagrama entidad-relación (Mermaid)
* docs/base-de-datos/diccionario.md   — diccionario de datos tabla por tabla

Uso:  python manage.py documentar_bd
"""
from pathlib import Path

from django.apps import apps
from django.conf import settings
from django.core.management.base import BaseCommand
from django.db import connection, models

APPS_PROPIAS = ["core", "personal", "nomina"]
MODULOS = {"core": "Configuración general", "personal": "Personal", "nomina": "Nómina"}


def _tipo_mysql(campo) -> str:
    tipo = campo.db_type(connection) or ""
    return tipo.replace(" AUTO_INCREMENT", "").replace("numeric", "decimal").replace("bool", "tinyint(1)").replace(", ", ",")


def _descripcion(campo) -> str:
    if campo.primary_key:
        return "Identificador único autoincremental."
    nombre = str(campo.verbose_name)
    partes = [nombre[:1].upper() + nombre[1:]]
    if campo.help_text:
        partes.append(str(campo.help_text))
    if campo.choices and not isinstance(campo, models.ForeignKey):
        opciones = ", ".join(f"`{v}` {t}" for v, t in campo.choices)
        partes.append(f"Valores: {opciones}.")
    return ". ".join(p.rstrip(".") for p in partes) + "."


def _nombre_er(tabla: str) -> str:
    return tabla.upper()


class Command(BaseCommand):
    help = "Genera el diagrama entidad-relación y el diccionario de datos en docs/base-de-datos/."

    def handle(self, *args, **op):
        destino = Path(settings.BASE_DIR) / "docs" / "base-de-datos"
        destino.mkdir(parents=True, exist_ok=True)
        modelos = [m for a in APPS_PROPIAS for m in apps.get_app_config(a).get_models()]
        usuario = apps.get_model("auth", "User")

        (destino / "diagrama-er.md").write_text(self._diagrama(modelos, usuario), encoding="utf-8")
        (destino / "diccionario.md").write_text(self._diccionario(modelos), encoding="utf-8")
        self.stdout.write(self.style.SUCCESS(f"Documentación generada en {destino}"))

    # ------------------------------------------------------------------

    def _diagrama(self, modelos, usuario) -> str:
        lineas = [
            "# Diagrama entidad-relación",
            "",
            "> Archivo generado con `python manage.py documentar_bd`. No lo edite a mano.",
            "",
            "Notación: `PK` llave primaria, `FK` llave foránea, `UK` valor único. ",
            "Las relaciones usan la notación *pata de gallo*: `||--o{` significa *uno a muchos*, ",
            "`||--o|` *uno a cero o uno*.",
            "",
        ]
        for app in APPS_PROPIAS:
            lineas += [f"## Módulo {MODULOS[app]}", "", "```mermaid", "erDiagram"]
            propios = [m for m in modelos if m._meta.app_label == app]
            externos = set()
            for m in propios:
                for f in m._meta.concrete_fields:
                    if f.is_relation and f.related_model._meta.app_label != app:
                        externos.add(f.related_model)
            for m in propios:
                lineas += self._entidad(m, detallado=True)
            for m in sorted(externos, key=lambda x: x._meta.db_table):
                lineas.append(f"    {_nombre_er(m._meta.db_table)} {{")
                lineas.append(f"        bigint id PK")
                lineas.append("    }")
            for m in propios:
                for f in m._meta.concrete_fields:
                    if not f.is_relation:
                        continue
                    destino = _nombre_er(f.related_model._meta.db_table)
                    origen = _nombre_er(m._meta.db_table)
                    card = "||--o|" if isinstance(f, models.OneToOneField) else "||--o{"
                    if f.null:
                        card = card.replace("||", "|o", 1)
                    lineas.append(f'    {destino} {card} {origen} : "{f.name}"')
            lineas += ["```", ""]

        # Vista global solo con relaciones
        lineas += ["## Vista general de relaciones", "", "```mermaid", "erDiagram"]
        vistas = set()
        for m in modelos:
            for f in m._meta.concrete_fields:
                if f.is_relation and f.related_model is not usuario:
                    clave = (f.related_model._meta.db_table, m._meta.db_table)
                    if clave in vistas:
                        continue
                    vistas.add(clave)
                    card = "||--o|" if isinstance(f, models.OneToOneField) else "||--o{"
                    lineas.append(f'    {_nombre_er(clave[0])} {card} {_nombre_er(clave[1])} : ""')
        lineas += ["```", ""]
        return "\n".join(lineas)

    def _entidad(self, m, detallado=True):
        out = [f"    {_nombre_er(m._meta.db_table)} {{"]
        for f in m._meta.concrete_fields:
            tipo = _tipo_mysql(f).split("(")[0].split()[0] or "bigint"
            marcas = []
            if f.primary_key:
                marcas.append("PK")
            if f.is_relation:
                marcas.append("FK")
            if f.unique and not f.primary_key:
                marcas.append("UK")
            out.append(f"        {tipo} {f.column} {','.join(marcas)}".rstrip())
        out.append("    }")
        return out

    def _diccionario(self, modelos) -> str:
        lineas = [
            "# Diccionario de datos",
            "",
            "> Archivo generado con `python manage.py documentar_bd`. No lo edite a mano.",
            "",
            "Motor: **MySQL 8**, juego de caracteres `utf8mb4`, motor de almacenamiento InnoDB. ",
            "Todas las tablas tienen llave primaria `id BIGINT AUTO_INCREMENT`. Los valores monetarios ",
            "se almacenan como `DECIMAL(14,2)` en pesos colombianos y los porcentajes como fracción ",
            "decimal (`0.04` = 4 %).",
            "",
            "## Índice de tablas",
            "",
            "| Tabla | Módulo | Descripción |",
            "|---|---|---|",
        ]
        for m in modelos:
            doc = " ".join((m.__doc__ or "").strip().split("\n\n")[0].split())
            if doc.startswith(m.__name__ + "("):
                doc = str(m._meta.verbose_name_plural).capitalize() + "."
            lineas.append(f"| [`{m._meta.db_table}`](#{m._meta.db_table.replace('_', '_')}) | {MODULOS[m._meta.app_label]} | {doc} |")
        lineas.append("")
        lineas.append("Tablas del framework utilizadas: `auth_user` (usuarios), `auth_group` (roles), `auth_user_groups`, `django_session`, `django_migrations`.")
        lineas.append("")

        for m in modelos:
            lineas += [f"## {m._meta.db_table}", ""]
            doc = (m.__doc__ or "").strip()
            if doc and not doc.startswith(m.__name__ + "("):
                lineas += [" ".join(doc.split()), ""]
            lineas += ["| Columna | Tipo MySQL | Nulo | Llave | Predeterminado | Descripción |", "|---|---|---|---|---|---|"]
            for f in m._meta.concrete_fields:
                llave = "PK" if f.primary_key else ("FK → `%s`" % f.related_model._meta.db_table if f.is_relation else ("UK" if f.unique else ""))
                defecto = ""
                if f.has_default() and not callable(f.default):
                    defecto = f"`{f.default}`"
                elif getattr(f, "auto_now_add", False) or getattr(f, "auto_now", False):
                    defecto = "fecha actual"
                lineas.append(
                    f"| `{f.column}` | `{_tipo_mysql(f)}` | {'Sí' if f.null else 'No'} | {llave} | {defecto} | {_descripcion(f)} |"
                )
            restricciones = []
            for grupo in m._meta.unique_together:
                restricciones.append("Único compuesto: (" + ", ".join(f"`{m._meta.get_field(c).column}`" for c in grupo) + ")")
            fks = [f for f in m._meta.concrete_fields if f.is_relation]
            for f in fks:
                accion = {models.PROTECT: "se impide si existen registros relacionados", models.CASCADE: "se eliminan también estos registros",
                          models.SET_NULL: "la columna queda en NULL"}.get(f.remote_field.on_delete, "—")
                restricciones.append(f"`{f.column}` → `{f.related_model._meta.db_table}.id` (índice y llave foránea). Al eliminar el registro padre: {accion}.")
            if restricciones:
                lineas += ["", "**Restricciones**", ""] + [f"- {r}" for r in restricciones]
            lineas.append("")
        return "\n".join(lineas)
