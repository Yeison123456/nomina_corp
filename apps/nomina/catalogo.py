"""
Catálogo base de conceptos de nómina. Se carga con el comando
`python manage.py inicializar_catalogos`.

Columnas: código, nombre, tipo, captura, salarial, base SS, base prestaciones,
base vacaciones, orden, descripción.
"""

CONCEPTOS = [
    # ---- Devengados calculados ------------------------------------------------
    ("SAL", "Salario básico", "DEV", "SIS", True, True, True, True, 10, "Salario mensual / 30 × días pagados como salario."),
    ("AUXT", "Auxilio de transporte", "DEV", "SIS", False, False, True, False, 20, "Solo para salarios hasta 2 SMMLV. Proporcional a días trabajados."),
    # ---- Devengados por horas -------------------------------------------------
    ("RN", "Recargo nocturno", "DEV", "HOR", True, True, True, True, 30, "Hora ordinaria nocturna: valor hora × % recargo nocturno."),
    ("HED", "Hora extra diurna", "DEV", "HOR", True, True, True, False, 31, "Valor hora × (1 + % extra diurna)."),
    ("HEN", "Hora extra nocturna", "DEV", "HOR", True, True, True, False, 32, "Valor hora × (1 + % extra nocturna)."),
    ("HDF", "Hora dominical/festiva diurna", "DEV", "HOR", True, True, True, False, 33, "Valor hora × (1 + % dominical)."),
    ("HNDF", "Hora dominical/festiva nocturna", "DEV", "HOR", True, True, True, False, 34, "Valor hora × (1 + % dominical + % nocturno)."),
    ("HEDDF", "Hora extra diurna dominical/festiva", "DEV", "HOR", True, True, True, False, 35, "Valor hora × (1 + % extra diurna + % dominical)."),
    ("HENDF", "Hora extra nocturna dominical/festiva", "DEV", "HOR", True, True, True, False, 36, "Valor hora × (1 + % extra nocturna + % dominical)."),
    # ---- Devengados por días (ausencias) -------------------------------------
    ("INCG", "Incapacidad por enfermedad general", "DEV", "DIA", False, True, True, True, 40, "Días 1-2 al 100 %; desde el día 3 al 66,67 %, nunca menos del SMMLV diario."),
    ("INCL", "Incapacidad por accidente de trabajo", "DEV", "DIA", False, True, True, True, 41, "100 % del salario diario desde el primer día."),
    ("LMP", "Licencia de maternidad o paternidad", "DEV", "DIA", False, True, True, True, 42, "100 % del salario diario."),
    ("LREM", "Licencia remunerada", "DEV", "DIA", True, True, True, True, 43, "Luto, calamidad doméstica u otras licencias pagadas al 100 %."),
    ("VACD", "Vacaciones disfrutadas", "DEV", "DIA", True, True, True, True, 44, "Días calendario del rango pagados al salario diario. La cantidad registra los días hábiles."),
    ("LNR", "Licencia no remunerada", "INF", "DIA", False, False, False, False, 45, "Días sin pago. Se descuentan del salario."),
    ("SUS", "Suspensión disciplinaria", "INF", "DIA", False, False, False, False, 46, "Días sin pago. Se descuentan del salario."),
    # ---- Devengados por valor -------------------------------------------------
    ("COM", "Comisiones", "DEV", "VAL", True, True, True, False, 50, "Pago salarial variable."),
    ("BONS", "Bonificación salarial", "DEV", "VAL", True, True, True, False, 51, "Pago salarial ocasional por desempeño."),
    ("BONNS", "Bonificación no salarial", "DEV", "VAL", False, False, False, False, 52, "Pactada como no salarial (art. 128 CST). Cuenta para el límite del 40 %."),
    ("AUXNS", "Auxilio no salarial", "DEV", "VAL", False, False, False, False, 53, "Alimentación, rodamiento u otros auxilios no salariales."),
    # ---- Deducciones ----------------------------------------------------------
    ("SALUD", "Aporte salud empleado", "DED", "SIS", False, False, False, False, 10, "4 % del IBC."),
    ("PENS", "Aporte pensión empleado", "DED", "SIS", False, False, False, False, 11, "4 % del IBC."),
    ("FSP", "Fondo de solidaridad pensional", "DED", "SIS", False, False, False, False, 12, "Desde 4 SMMLV: 1 % a 2 % del IBC según escala."),
    ("RTEFTE", "Retención en la fuente", "DED", "SIS", False, False, False, False, 13, "Procedimiento 1, art. 383 E.T."),
    ("PREST", "Cuota préstamo empresa", "DED", "SIS", False, False, False, False, 20, "Cuota del préstamo otorgado por la empresa."),
    ("LIBR", "Cuota libranza", "DED", "SIS", False, False, False, False, 21, "Cuota de crédito de libranza con entidad financiera."),
    ("DESC", "Otros descuentos", "DED", "VAL", False, False, False, False, 30, "Descuentos autorizados por el trabajador."),
    # ---- Aportes del empleador ------------------------------------------------
    ("AP_SAL", "Salud empleador", "APO", "SIS", False, False, False, False, 10, "8,5 % del IBC, salvo exoneración."),
    ("AP_PEN", "Pensión empleador", "APO", "SIS", False, False, False, False, 11, "12 % del IBC."),
    ("AP_ARL", "Riesgos laborales", "APO", "SIS", False, False, False, False, 12, "Tarifa según clase de riesgo del contrato."),
    ("AP_CCF", "Caja de compensación", "APO", "SIS", False, False, False, False, 13, "4 % de la base de parafiscales."),
    ("AP_ICBF", "ICBF", "APO", "SIS", False, False, False, False, 14, "3 % de la base de parafiscales, salvo exoneración."),
    ("AP_SENA", "SENA", "APO", "SIS", False, False, False, False, 15, "2 % de la base de parafiscales, salvo exoneración."),
    # ---- Provisiones ----------------------------------------------------------
    ("PR_CES", "Provisión cesantías", "PRO", "SIS", False, False, False, False, 10, "8,33 % de la base de prestaciones."),
    ("PR_INT", "Provisión intereses de cesantías", "PRO", "SIS", False, False, False, False, 11, "12 % anual sobre la provisión de cesantías."),
    ("PR_PRI", "Provisión prima de servicios", "PRO", "SIS", False, False, False, False, 12, "8,33 % de la base de prestaciones."),
    ("PR_VAC", "Provisión vacaciones", "PRO", "SIS", False, False, False, False, 13, "4,17 % de la base de vacaciones."),
]

ENTIDADES = {
    "EPS": [("Nueva EPS", "900156264-2"), ("EPS Sura", "800088702-2"), ("Sanitas EPS", "800251440-6"),
            ("Compensar EPS", "860066942-7"), ("Salud Total EPS", "800130907-4"), ("Famisanar EPS", "830003564-7")],
    "AFP": [("Colpensiones", "900336004-7"), ("Porvenir", "800144331-3"), ("Protección", "800138188-1"),
            ("Colfondos", "800149496-2"), ("Skandia", "800148514-2")],
    "CES": [("Porvenir Cesantías", "800144331-3"), ("Protección Cesantías", "800138188-1"),
            ("Colfondos Cesantías", "800149496-2"), ("Fondo Nacional del Ahorro", "899999284-4")],
    "CCF": [("Compensar", "860066942-7"), ("Cafam", "860013570-3"), ("Colsubsidio", "860007336-1")],
    "ARL": [("ARL Sura", "800256161-9"), ("Positiva", "860011153-6"), ("Colmena Seguros", "800226175-3")],
    "BAN": [("Bancolombia", "890903938-8"), ("Banco de Bogotá", "860002964-4"), ("Davivienda", "860034313-7"),
            ("BBVA Colombia", "860003020-1"), ("Banco Popular", "860007738-9")],
}
