"""
Carga la empresa ficticia Cordillera Industrial S.A.S. con su estructura,
24 empleados, novedades, préstamos y nómina histórica de septiembre y
octubre de 2026 (cerrada) y noviembre de 2026 (abierta).
"""
import random
from datetime import date, timedelta
from decimal import Decimal

from django.contrib.auth.models import Group, User
from django.core.management import call_command
from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from apps.core.models import Empresa, Entidad
from apps.core.roles import ADMIN, ANALISTA, CONSULTA
from apps.nomina.models import Concepto, Novedad, PeriodoNomina, Prestamo
from apps.nomina.servicios import liquidador
from apps.personal.models import Area, Cargo, CentroCosto, Contrato, Empleado

D = Decimal
CLAVE_DEMO = "Libra2026*"

CENTROS = [("100", "Administración"), ("200", "Producción"), ("300", "Comercial"), ("400", "Logística")]
AREAS = [
    ("GER", "Gerencia General", "100"), ("THU", "Talento Humano", "100"), ("FIN", "Contabilidad y Finanzas", "100"),
    ("PRO", "Planta de Producción", "200"), ("MAN", "Mantenimiento", "200"), ("CAL", "Aseguramiento de Calidad", "200"),
    ("VEN", "Ventas", "300"), ("MER", "Mercadeo", "300"), ("ALM", "Almacén y Despachos", "400"),
]
CARGOS = [
    ("C01", "Gerente general", "GER", 28000000), ("C02", "Directora de talento humano", "THU", 9500000),
    ("C03", "Analista de nómina", "THU", 3600000), ("C04", "Contador", "FIN", 6200000),
    ("C05", "Auxiliar contable", "FIN", 2300000), ("C06", "Jefe de planta", "PRO", 7800000),
    ("C07", "Supervisor de turno", "PRO", 3900000), ("C08", "Operario de máquina", "PRO", 1950000),
    ("C09", "Operario de empaque", "PRO", 1750905), ("C10", "Técnico de mantenimiento", "MAN", 2900000),
    ("C11", "Inspector de calidad", "CAL", 2600000), ("C12", "Ejecutiva comercial", "VEN", 3200000),
    ("C13", "Coordinador de mercadeo", "MER", 4800000), ("C14", "Auxiliar de bodega", "ALM", 1850000),
    ("C15", "Conductor", "ALM", 2100000),
]
# (doc, nombres, apellidos, género, nacimiento, cargo, salario, tipo, inicio, fin, periodicidad, riesgo, tipo_salario)
EMPLEADOS = [
    ("52418903", "Mariana", "Ospina Restrepo", "F", date(1974, 3, 8), "C01", 28000000, "IND", date(2015, 2, 2), None, "M", 1, "INT"),
    ("1020734561", "Laura Camila", "Bermúdez Arango", "F", date(1986, 11, 21), "C02", 9500000, "IND", date(2019, 6, 4), None, "M", 1, "ORD"),
    ("1032456789", "Andrés Felipe", "Quintero Salazar", "M", date(1993, 1, 30), "C03", 3600000, "IND", date(2022, 3, 1), None, "M", 1, "ORD"),
    ("79856214", "Germán", "Valderrama Pinto", "M", date(1979, 7, 15), "C04", 6200000, "IND", date(2017, 9, 11), None, "M", 1, "ORD"),
    ("1015478236", "Paola Andrea", "Rincón Gaitán", "F", date(1997, 4, 2), "C05", 2300000, "FIJ", date(2025, 12, 15), date(2026, 12, 14), "M", 1, "ORD"),
    ("80123987", "Jairo Alberto", "Mesa Cárdenas", "M", date(1981, 9, 19), "C06", 7800000, "IND", date(2016, 5, 16), None, "Q", 3, "ORD"),
    ("1023987456", "Diana Marcela", "Cortés Peña", "F", date(1990, 12, 3), "C07", 3900000, "IND", date(2020, 8, 3), None, "Q", 3, "ORD"),
    ("1018456321", "Wilson", "Ariza Montoya", "M", date(1988, 6, 27), "C07", 3900000, "IND", date(2018, 2, 19), None, "Q", 3, "ORD"),
    ("1030567842", "Brayan Steven", "Gómez Rojas", "M", date(1999, 2, 14), "C08", 1950000, "IND", date(2023, 1, 16), None, "Q", 3, "ORD"),
    ("1012348765", "Yesenia", "Moreno Castro", "F", date(1995, 8, 9), "C08", 1950000, "IND", date(2021, 10, 4), None, "Q", 3, "ORD"),
    ("1007896543", "Luis Eduardo", "Patiño Vargas", "M", date(1992, 5, 23), "C08", 1950000, "IND", date(2019, 4, 8), None, "Q", 3, "ORD"),
    ("1026789123", "Karen Lizeth", "Sánchez Duarte", "F", date(2001, 10, 11), "C09", 1750905, "FIJ", date(2026, 1, 13), date(2026, 12, 31), "Q", 3, "ORD"),
    ("1019654782", "Jhon Fredy", "Castañeda León", "M", date(1996, 3, 17), "C09", 1750905, "OBR", date(2026, 6, 1), None, "Q", 3, "ORD"),
    ("1022145698", "Nelson Javier", "Rubio Fajardo", "M", date(1985, 11, 29), "C09", 1750905, "IND", date(2017, 7, 24), None, "Q", 3, "ORD"),
    ("1014785236", "Sandra Milena", "Ortiz Beltrán", "F", date(1989, 1, 6), "C10", 2900000, "IND", date(2018, 11, 13), None, "Q", 4, "ORD"),
    ("1031258963", "Óscar Iván", "Lozano Herrera", "M", date(1994, 7, 31), "C10", 2900000, "FIJ", date(2025, 11, 25), date(2026, 11, 24), "Q", 4, "ORD"),
    ("1016987412", "Catalina", "Pardo Suárez", "F", date(1991, 9, 4), "C11", 2600000, "IND", date(2020, 2, 10), None, "Q", 2, "ORD"),
    ("1028741596", "Valentina", "Acosta Ríos", "F", date(1998, 6, 18), "C12", 3200000, "IND", date(2022, 9, 5), None, "M", 1, "ORD"),
    ("1013698547", "Sebastián", "Mejía Franco", "M", date(1995, 12, 22), "C12", 3200000, "IND", date(2024, 4, 15), None, "M", 1, "ORD"),
    ("1024563178", "Natalia", "Henao Villamil", "F", date(1990, 4, 26), "C13", 4800000, "IND", date(2021, 1, 18), None, "M", 1, "ORD"),
    ("1017412589", "Héctor Mauricio", "Torres Guzmán", "M", date(1987, 8, 13), "C14", 1850000, "IND", date(2019, 9, 2), None, "Q", 2, "ORD"),
    ("1029632587", "Daniela", "Rojas Molina", "F", date(2000, 1, 9), "C14", 1850000, "FIJ", date(2026, 2, 2), date(2027, 2, 1), "Q", 2, "ORD"),
    ("79412365", "Rafael Antonio", "Vanegas Cruz", "M", date(1976, 10, 30), "C15", 2100000, "IND", date(2014, 3, 3), None, "Q", 4, "ORD"),
    ("1021478963", "Julián David", "Cifuentes Parra", "M", date(1993, 5, 5), "C15", 2100000, "IND", date(2023, 8, 22), None, "Q", 4, "ORD"),
]


class Command(BaseCommand):
    help = "Carga datos de demostración (empresa ficticia Cordillera Industrial S.A.S.)."

    def add_arguments(self, parser):
        parser.add_argument("--sin-historia", action="store_true", help="No liquida ni cierra periodos históricos.")

    @transaction.atomic
    def handle(self, *args, **op):
        if Empleado.objects.exists():
            raise CommandError("La base de datos ya tiene empleados. Los datos de demostración solo se cargan en una base vacía.")
        call_command("inicializar_catalogos", stdout=self.stdout)
        rnd = random.Random(2026)

        Empresa.objects.update_or_create(id=1, defaults=dict(
            razon_social="Cordillera Industrial S.A.S.", nit="901.482.317-5",
            direccion="Carrera 68D # 17-50, Zona Industrial Montevideo", ciudad="Bogotá D.C.",
            telefono="(601) 745 2290", correo="nomina@cordillera-industrial.example",
            representante_legal="Mariana Ospina Restrepo",
            actividad_economica="2229 — Fabricación de artículos de plástico y empaques", exonerada_aportes=True,
        ))

        centros = {c: CentroCosto.objects.create(codigo=c, nombre=n) for c, n in CENTROS}
        areas = {c: Area.objects.create(codigo=c, nombre=n, centro_costo=centros[cc]) for c, n, cc in AREAS}
        cargos = {c: Cargo.objects.create(codigo=c, nombre=n, area=areas[a], salario_referencia=D(s)) for c, n, a, s in CARGOS}

        ent = lambda tipo: list(Entidad.objects.filter(tipo=tipo))
        eps, afp, ces, ccf, arl, ban = (ent(t) for t in ("EPS", "AFP", "CES", "CCF", "ARL", "BAN"))

        contratos = []
        for i, (doc, nom, ape, gen, nac, cargo, sal, tipo, ini, fin, per, riesgo, tsal) in enumerate(EMPLEADOS, start=1):
            usuario_correo = (nom.split()[0] + "." + ape.split()[0]).lower()
            for a, b in (("á", "a"), ("é", "e"), ("í", "i"), ("ó", "o"), ("ú", "u"), ("ñ", "n")):
                usuario_correo = usuario_correo.replace(a, b)
            e = Empleado.objects.create(
                tipo_documento="CC", numero_documento=doc, nombres=nom, apellidos=ape, genero=gen, fecha_nacimiento=nac,
                correo=f"{usuario_correo}@cordillera-industrial.example", telefono=f"3{rnd.randint(100000000, 229999999)}",
                direccion=f"Calle {rnd.randint(1, 170)} # {rnd.randint(1, 120)}-{rnd.randint(1, 99)}", ciudad="Bogotá D.C.",
                banco=rnd.choice(ban), tipo_cuenta=rnd.choice(["AH", "AH", "CC"]), numero_cuenta=str(rnd.randint(10**9, 10**10 - 1)),
                eps=rnd.choice(eps), afp=rnd.choice(afp), fondo_cesantias=None if tsal == "INT" else rnd.choice(ces), caja=ccf[i % len(ccf)],
            )
            area = cargos[cargo].area
            contratos.append(Contrato.objects.create(
                numero=f"CI-{i:05d}", empleado=e, tipo=tipo, tipo_salario=tsal, salario=D(sal), cargo=cargos[cargo],
                centro_costo=area.centro_costo, periodicidad=per, clase_riesgo=riesgo, arl=arl[0],
                fecha_inicio=ini, fecha_fin=fin,
            ))

        self._usuarios()
        self._prestamos(contratos)
        self._novedades(contratos, rnd)

        if not op["sin_historia"]:
            self._historia()

        self.stdout.write(self.style.SUCCESS(
            f"Datos de demostración cargados: {Empleado.objects.count()} empleados, {Novedad.objects.count()} novedades, "
            f"{PeriodoNomina.objects.count()} periodos."
        ))
        self.stdout.write(f"Usuarios: admin / analista / consulta — contraseña: {CLAVE_DEMO}")

    # ------------------------------------------------------------------

    def _usuarios(self):
        for usuario, nombre, apellido, rol, super_ in (
            ("admin", "Administrador", "del sistema", ADMIN, True),
            ("analista", "Andrés Felipe", "Quintero", ANALISTA, False),
            ("consulta", "Germán", "Valderrama", CONSULTA, False),
        ):
            u, _ = User.objects.get_or_create(username=usuario, defaults=dict(first_name=nombre, last_name=apellido, is_staff=super_, is_superuser=super_))
            u.set_password(CLAVE_DEMO)
            u.save()
            u.groups.set([Group.objects.get(name=rol)])

    def _prestamos(self, contratos):
        prest, libr = Concepto.objects.get(codigo="PREST"), Concepto.objects.get(codigo="LIBR")
        datos = [
            (contratos[8], prest, "Préstamo calamidad doméstica", date(2026, 8, 20), D("1200000"), 8),
            (contratos[14], libr, "Libranza Banco Popular", date(2026, 7, 10), D("6000000"), 24),
            (contratos[2], prest, "Préstamo para estudio", date(2026, 8, 25), D("2400000"), 6),
        ]
        for contrato, concepto, desc, fecha, monto, cuotas in datos:
            Prestamo.objects.create(contrato=contrato, concepto=concepto, descripcion=desc, fecha=fecha, monto=monto,
                                    numero_cuotas=cuotas, valor_cuota=(monto / cuotas).quantize(D("1")), saldo=monto)

    def _novedades(self, contratos, rnd):
        c = {x.codigo: x for x in Concepto.objects.all()}
        operativos = [k for k in contratos if k.periodicidad == "Q" and k.cargo.codigo in ("C07", "C08", "C09", "C10", "C14", "C15")]
        comerciales = [k for k in contratos if k.cargo.codigo == "C12"]

        def nov(contrato, cod, ini, fin=None, cant=0, valor=0, obs=""):
            Novedad.objects.create(contrato=contrato, concepto=c[cod], fecha_inicio=ini, fecha_fin=fin,
                                   cantidad=D(cant), valor=D(valor), observacion=obs)

        quincenas = [(date(2026, 9, 1), 15), (date(2026, 9, 16), 15), (date(2026, 10, 1), 15),
                     (date(2026, 10, 16), 16), (date(2026, 11, 1), 15)]
        for inicio, largo in quincenas:
            for k in operativos:
                if rnd.random() < 0.7:
                    nov(k, "HED", inicio + timedelta(days=rnd.randint(0, largo - 1)), cant=rnd.choice([2, 3, 4, 6, 8]), obs="Cierre de pedido")
                if rnd.random() < 0.45:
                    nov(k, "RN", inicio + timedelta(days=rnd.randint(0, largo - 1)), cant=rnd.choice([8, 16, 24]), obs="Turno nocturno")
                if rnd.random() < 0.25:
                    nov(k, "HDF", inicio + timedelta(days=rnd.randint(0, largo - 1)), cant=8, obs="Domingo de producción")
                if rnd.random() < 0.15:
                    nov(k, "HEN", inicio + timedelta(days=rnd.randint(0, largo - 1)), cant=rnd.choice([2, 3, 4]))

        for mes in (9, 10, 11):
            for k in comerciales:
                nov(k, "COM", date(2026, mes, 28 if mes != 11 else 10), valor=rnd.choice([850000, 1200000, 1650000, 2100000]), obs="Comisión sobre ventas del mes")
            nov(contratos[19], "AUXNS", date(2026, mes, 5), valor=400000, obs="Auxilio de rodamiento")
        nov(contratos[1], "BONNS", date(2026, 10, 20), valor=1500000, obs="Bono por cumplimiento de indicadores (no salarial)")

        # Ausencias
        nov(contratos[9], "INCG", date(2026, 10, 6), date(2026, 10, 10), obs="Incapacidad EPS — infección respiratoria")
        nov(contratos[22], "INCL", date(2026, 9, 22), date(2026, 9, 26), obs="Accidente de trabajo — esguince en cargue")
        nov(contratos[3], "VACD", date(2026, 9, 14), date(2026, 9, 25), cant=10, obs="Vacaciones periodo 2025-2026")
        nov(contratos[16], "LREM", date(2026, 10, 27), date(2026, 10, 29), obs="Licencia de luto")
        nov(contratos[10], "LNR", date(2026, 11, 3), date(2026, 11, 4), obs="Diligencia personal")
        nov(contratos[13], "INCG", date(2026, 11, 10), date(2026, 11, 19), obs="Incapacidad EPS — cirugía ambulatoria")
        nov(contratos[18], "LMP", date(2026, 11, 4), date(2026, 11, 13), obs="Licencia de paternidad")
        nov(contratos[11], "DESC", date(2026, 11, 8), valor=85000, obs="Dotación extraviada")

    def _historia(self):
        def crear(per, anio, mes, num, pago):
            ini, fin = liquidador.fechas_periodo(per, anio, mes, num)
            return PeriodoNomina.objects.create(periodicidad=per, anio=anio, mes=mes, numero=num, fecha_inicio=ini, fecha_fin=fin, fecha_pago=pago)

        historicos = [
            ("Q", 2026, 9, 1, date(2026, 9, 15)), ("Q", 2026, 9, 2, date(2026, 9, 30)), ("M", 2026, 9, 1, date(2026, 9, 30)),
            ("Q", 2026, 10, 1, date(2026, 10, 15)), ("Q", 2026, 10, 2, date(2026, 10, 30)), ("M", 2026, 10, 1, date(2026, 10, 30)),
        ]
        for datos in historicos:
            p = crear(*datos)
            liquidador.liquidar_periodo(p, None)
            liquidador.cerrar_periodo(p, None)
        actual = crear("Q", 2026, 11, 1, date(2026, 11, 13))
        liquidador.liquidar_periodo(actual, None)
        crear("M", 2026, 11, 1, date(2026, 11, 30))
