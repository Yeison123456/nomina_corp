"""
Pruebas del motor de cálculo (sin base de datos) y del ciclo de un periodo
(con base de datos de pruebas).

Ejecutar:  python manage.py test apps.nomina
"""
from datetime import date
from decimal import Decimal
from types import SimpleNamespace as NS

from django.core.management import call_command
from django.test import SimpleTestCase, TestCase

from apps.personal.models import Contrato

from .catalogo import CONCEPTOS
from .servicios.motor import MotorNomina, dias360, redondear, redondear_mil

D = Decimal

CATALOGO = {
    c[0]: NS(codigo=c[0], nombre=c[1], tipo=c[2], captura=c[3], salarial=c[4], base_seguridad_social=c[5],
             base_prestaciones=c[6], base_vacaciones=c[7])
    for c in CONCEPTOS
}

PARAMS_2026 = NS(
    smmlv=D("1750905"), auxilio_transporte=D("249095"), uvt=D("52374"), horas_mes=210,
    pct_recargo_nocturno=D("0.35"), pct_recargo_dominical=D("0.90"), pct_extra_diurna=D("0.25"), pct_extra_nocturna=D("0.75"),
    pct_salud_empleado=D("0.04"), pct_pension_empleado=D("0.04"), pct_salud_empleador=D("0.085"),
    pct_pension_empleador=D("0.12"), pct_caja=D("0.04"), pct_icbf=D("0.03"), pct_sena=D("0.02"),
)


def contrato(salario, integral=False, inicio=date(2020, 1, 1), terminacion=None, riesgo=1, afp=True):
    return NS(
        salario=D(salario), es_integral=integral, fecha_inicio=inicio, fecha_final_efectiva=terminacion,
        tarifa_arl=Contrato.TARIFA_ARL[riesgo], empleado=NS(afp=object() if afp else None, afp_id=1 if afp else None),
    )


def novedad(codigo, inicio, fin=None, cantidad=0, valor=0, id_=1, obs=""):
    return NS(id=id_, concepto=CATALOGO[codigo], fecha_inicio=inicio, fecha_final=fin or inicio,
              cantidad=D(cantidad), valor=D(valor), observacion=obs)


def lineas(res):
    agrupado = {}
    for l in res.lineas:
        agrupado[l.codigo] = agrupado.get(l.codigo, D(0)) + l.valor
    return agrupado


class UtilidadesTest(SimpleTestCase):
    def test_dias360(self):
        self.assertEqual(dias360(date(2026, 11, 1), date(2026, 11, 30)), 30)
        self.assertEqual(dias360(date(2026, 10, 16), date(2026, 10, 31)), 15)
        self.assertEqual(dias360(date(2026, 2, 16), date(2026, 2, 28)), 15)
        self.assertEqual(dias360(date(2026, 1, 1), date(2026, 12, 31)), 360)
        self.assertEqual(dias360(date(2026, 11, 10), date(2026, 11, 9)), 0)

    def test_redondeos(self):
        self.assertEqual(redondear(D("1500.5")), D("1501"))
        self.assertEqual(redondear_mil(D("500342")), D("500000"))
        self.assertEqual(redondear_mil(D("4911600")), D("4912000"))


class MotorTest(SimpleTestCase):
    def setUp(self):
        self.motor = MotorNomina(PARAMS_2026, CATALOGO, exonerada=True)

    def liquidar_mes(self, c, novedades=(), prestamos=()):
        return self.motor.liquidar(c, date(2026, 11, 1), date(2026, 11, 30), 30, novedades, prestamos)

    def test_salario_minimo_mes_completo(self):
        r = self.liquidar_mes(contrato("1750905"))
        v = lineas(r)
        self.assertEqual(v["SAL"], D("1750905"))
        self.assertEqual(v["AUXT"], D("249095"))
        self.assertEqual(r.ibc, D("1750905"))
        self.assertEqual(v["SALUD"], D("70036"))
        self.assertEqual(v["PENS"], D("70036"))
        self.assertNotIn("FSP", v)
        self.assertNotIn("RTEFTE", v)
        # Exonerada: sin salud empleador, ICBF ni SENA
        self.assertNotIn("AP_SAL", v)
        self.assertNotIn("AP_ICBF", v)
        # Base de prestaciones incluye auxilio de transporte
        self.assertEqual(r.base_prestaciones, D("2000000"))
        self.assertEqual(v["PR_CES"], D("166600"))
        self.assertEqual(v["PR_INT"], D("19992"))
        self.assertEqual(v["PR_VAC"], D("73013"))

    def test_quincena_completa_siempre_15_dias(self):
        r = self.motor.liquidar(contrato("3000000"), date(2026, 10, 16), date(2026, 10, 31), 15)
        self.assertEqual(r.dias_periodo, 15)
        self.assertEqual(lineas(r)["SAL"], D("1500000"))

    def test_ingreso_a_mitad_de_periodo(self):
        r = self.liquidar_mes(contrato("3000000", inicio=date(2026, 11, 21)))
        self.assertEqual(r.dias_periodo, 10)
        self.assertEqual(lineas(r)["SAL"], D("1000000"))

    def test_sin_auxilio_sobre_dos_smmlv(self):
        r = self.liquidar_mes(contrato("3600000"))
        self.assertNotIn("AUXT", lineas(r))

    def test_horas_extra_y_recargos(self):
        c = contrato("2100000")  # hora = 10.000
        novs = [novedad("HED", date(2026, 11, 5), cantidad=4, id_=1), novedad("RN", date(2026, 11, 6), cantidad=8, id_=2),
                novedad("HEDDF", date(2026, 11, 8), cantidad=2, id_=3), novedad("HNDF", date(2026, 11, 8), cantidad=1, id_=4)]
        v = lineas(self.liquidar_mes(c, novs))
        self.assertEqual(v["HED"], D("50000"))     # 4 × 10.000 × 1,25
        self.assertEqual(v["RN"], D("28000"))      # 8 × 10.000 × 0,35
        self.assertEqual(v["HEDDF"], D("43000"))   # 2 × 10.000 × 2,15
        self.assertEqual(v["HNDF"], D("22500"))    # 1 × 10.000 × 2,25

    def test_incapacidad_general_con_piso_minimo(self):
        c = contrato("1950000")
        nov = novedad("INCG", date(2026, 11, 6), date(2026, 11, 10))
        r = self.liquidar_mes(c, [nov])
        incg = [l for l in r.lineas if l.codigo == "INCG"]
        self.assertEqual(incg[0].valor, D("130000"))   # 2 días al 100 %
        self.assertEqual(incg[1].valor, D("175091"))   # 3 días al SMMLV diario (66,67 % es menor)
        self.assertEqual(r.dias_trabajados, 25)

    def test_incapacidad_que_viene_de_periodo_anterior(self):
        c = contrato("6000000")
        nov = novedad("INCG", date(2026, 10, 28), date(2026, 11, 3))
        r = self.liquidar_mes(c, [nov])
        incg = [l for l in r.lineas if l.codigo == "INCG"]
        self.assertEqual(len(incg), 1)                 # los días 1 y 2 ya se pagaron en octubre
        self.assertEqual(incg[0].cantidad, D("3"))
        self.assertEqual(incg[0].tasa, D("0.6667"))

    def test_licencia_no_remunerada_reduce_ibc_minimo(self):
        c = contrato("1750905")
        r = self.liquidar_mes(c, [novedad("LNR", date(2026, 11, 3), date(2026, 11, 4))])
        self.assertEqual(r.dias_trabajados, 28)
        self.assertEqual(r.ibc, D("1634178"))  # 28 días: no se exige IBC de 30

    def test_regla_40_por_ciento(self):
        c = contrato("2000000")
        r = self.liquidar_mes(c, [novedad("BONNS", date(2026, 11, 10), valor=2000000)])
        # Total 4.000.000; 40 % = 1.600.000; excedente no salarial 400.000 entra al IBC
        self.assertEqual(r.ibc, D("2400000"))

    def test_salario_integral(self):
        r = self.liquidar_mes(contrato("28000000", integral=True), [novedad("HED", date(2026, 11, 5), cantidad=2)])
        v = lineas(r)
        self.assertEqual(r.ibc, D("19600000"))       # 70 %
        self.assertNotIn("HED", v)                   # el integral compensa extras
        self.assertNotIn("PR_CES", v)
        self.assertIn("AP_SAL", v)                   # más de 10 SMMLV: sin exoneración
        self.assertEqual(v["FSP"], D("196000"))
        self.assertEqual(v["RTEFTE"], D("4912000"))

    def test_retencion_en_la_fuente(self):
        r = self.liquidar_mes(contrato("9500000"), [novedad("BONNS", date(2026, 11, 10), valor=1500000)])
        self.assertEqual(lineas(r)["RTEFTE"], D("500000"))

    def test_fondo_solidaridad_escala(self):
        self.assertEqual(MotorNomina.tasa_fsp(D("7000000"), D("1750905")), D("0"))
        self.assertEqual(MotorNomina.tasa_fsp(D("7003620"), D("1750905")), D("0.010"))
        self.assertEqual(MotorNomina.tasa_fsp(D("29000000"), D("1750905")), D("0.012"))
        self.assertEqual(MotorNomina.tasa_fsp(D("40000000"), D("1750905")), D("0.020"))

    def test_tope_ibc_25_smmlv(self):
        r = self.liquidar_mes(contrato("60000000"))
        self.assertEqual(r.ibc, D("43772625"))

    def test_prestamo_no_deja_neto_negativo(self):
        c = contrato("1750905")
        pre = NS(id=9, concepto=CATALOGO["PREST"], valor_cuota=D("5000000"), saldo=D("5000000"), descripcion="Préstamo")
        r = self.liquidar_mes(c, prestamos=[pre])
        dev = r.total("DEV", CATALOGO)
        ded = r.total("DED", CATALOGO)
        self.assertEqual(dev - ded, D("0"))
        self.assertTrue(r.advertencias)

    def test_pensionado_no_cotiza_pension(self):
        v = lineas(self.liquidar_mes(contrato("3000000", afp=False)))
        self.assertNotIn("PENS", v)
        self.assertNotIn("AP_PEN", v)


class CicloPeriodoTest(TestCase):
    """Liquida, cierra y reabre un periodo con los datos de demostración."""

    @classmethod
    def setUpTestData(cls):
        from io import StringIO

        call_command("cargar_demo", "--sin-historia", stdout=StringIO())

    def test_ciclo_completo(self):
        from .models import Novedad, PeriodoNomina, Prestamo
        from .servicios import liquidador

        ini, fin = liquidador.fechas_periodo("Q", 2026, 9, 1)
        p = PeriodoNomina.objects.create(periodicidad="Q", anio=2026, mes=9, numero=1, fecha_inicio=ini, fecha_fin=fin, fecha_pago=fin)
        n = liquidador.liquidar_periodo(p, None)
        self.assertEqual(n, Contrato.objects.filter(periodicidad="Q").count())
        p.refresh_from_db()
        self.assertEqual(p.estado, "LIQ")
        for liq in p.liquidaciones.all():
            self.assertEqual(liq.neto_pagar, liq.total_devengado - liq.total_deducciones)
            self.assertGreaterEqual(liq.neto_pagar, 0)

        saldo_antes = Prestamo.objects.get(descripcion="Préstamo calamidad doméstica").saldo
        liquidador.cerrar_periodo(p, None)
        self.assertEqual(Prestamo.objects.get(descripcion="Préstamo calamidad doméstica").saldo, saldo_antes - 150000)
        self.assertTrue(Novedad.objects.filter(periodo_aplicacion=p).exists())

        liquidador.reabrir_periodo(p, None)
        self.assertEqual(Prestamo.objects.get(descripcion="Préstamo calamidad doméstica").saldo, saldo_antes)
        self.assertFalse(Novedad.objects.filter(periodo_aplicacion=p).exists())

    def test_periodo_cerrado_no_se_reliquida(self):
        from .models import PeriodoNomina
        from .servicios import liquidador

        ini, fin = liquidador.fechas_periodo("M", 2026, 9, 1)
        p = PeriodoNomina.objects.create(periodicidad="M", anio=2026, mes=9, numero=1, fecha_inicio=ini, fecha_fin=fin, fecha_pago=fin)
        liquidador.liquidar_periodo(p, None)
        liquidador.cerrar_periodo(p, None)
        with self.assertRaises(liquidador.ErrorNomina):
            liquidador.liquidar_periodo(p, None)
