from datetime import date
from decimal import Decimal

from django.contrib.auth.models import Group
from django.core.management.base import BaseCommand
from django.db import transaction

from apps.core.models import Entidad, ParametroLegal
from apps.core.roles import ROLES
from apps.nomina.catalogo import CONCEPTOS, ENTIDADES
from apps.nomina.models import Concepto

D = Decimal

# Valores legales de Colombia. Verifique y actualice cada año en Configuración → Parámetros legales.
PARAMETROS = [
    dict(vigente_desde=date(2025, 1, 1), descripcion="Decreto 1572 de 2024 — SMMLV 2025; jornada 46 h (Ley 2101 de 2021)",
         smmlv=D("1423500"), auxilio_transporte=D("200000"), uvt=D("49799"), horas_mes=230, pct_recargo_dominical=D("0.75")),
    dict(vigente_desde=date(2025, 7, 1), descripcion="Ley 2466 de 2025 — recargo dominical y festivo al 80 %",
         smmlv=D("1423500"), auxilio_transporte=D("200000"), uvt=D("49799"), horas_mes=230, pct_recargo_dominical=D("0.80")),
    dict(vigente_desde=date(2025, 7, 15), descripcion="Ley 2101 de 2021 — jornada máxima de 44 h semanales",
         smmlv=D("1423500"), auxilio_transporte=D("200000"), uvt=D("49799"), horas_mes=220, pct_recargo_dominical=D("0.80")),
    dict(vigente_desde=date(2026, 1, 1), descripcion="SMMLV, auxilio de transporte y UVT 2026",
         smmlv=D("1750905"), auxilio_transporte=D("249095"), uvt=D("52374"), horas_mes=220, pct_recargo_dominical=D("0.80")),
    dict(vigente_desde=date(2026, 7, 1), descripcion="Ley 2466 de 2025 — recargo dominical y festivo al 90 %",
         smmlv=D("1750905"), auxilio_transporte=D("249095"), uvt=D("52374"), horas_mes=220, pct_recargo_dominical=D("0.90")),
    dict(vigente_desde=date(2026, 7, 15), descripcion="Ley 2101 de 2021 — jornada máxima de 42 h semanales",
         smmlv=D("1750905"), auxilio_transporte=D("249095"), uvt=D("52374"), horas_mes=210, pct_recargo_dominical=D("0.90")),
]


class Command(BaseCommand):
    help = "Carga los catálogos base: conceptos de nómina, entidades, parámetros legales y roles de usuario."

    @transaction.atomic
    def handle(self, *args, **opciones):
        for rol in ROLES:
            Group.objects.get_or_create(name=rol)

        for (codigo, nombre, tipo, captura, salarial, base_ss, base_prest, base_vac, orden, desc) in CONCEPTOS:
            Concepto.objects.update_or_create(codigo=codigo, defaults=dict(
                nombre=nombre, tipo=tipo, captura=captura, salarial=salarial, base_seguridad_social=base_ss,
                base_prestaciones=base_prest, base_vacaciones=base_vac, orden=orden, descripcion=desc,
            ))

        for tipo, lista in ENTIDADES.items():
            for nombre, nit in lista:
                Entidad.objects.get_or_create(tipo=tipo, nombre=nombre, defaults={"nit": nit})

        for p in PARAMETROS:
            ParametroLegal.objects.get_or_create(vigente_desde=p["vigente_desde"], defaults=p)

        self.stdout.write(self.style.SUCCESS(
            f"Catálogos listos: {Concepto.objects.count()} conceptos, {Entidad.objects.count()} entidades, "
            f"{ParametroLegal.objects.count()} parámetros legales, {len(ROLES)} roles."
        ))
