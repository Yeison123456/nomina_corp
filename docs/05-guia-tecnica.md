# 5. Guía técnica

Dirigida a quien mantiene o extiende el sistema. La instalación está en el [README](../README.md).

## 5.1 Comandos de administración

| Comando | Qué hace | Cuándo usarlo |
|---|---|---|
| `python manage.py migrate` | Crea o actualiza las tablas en MySQL. | Instalación y cada actualización del código. |
| `python manage.py inicializar_catalogos` | Carga o actualiza conceptos, entidades, parámetros legales y roles. Es idempotente: se puede ejecutar varias veces. | Instalación limpia (sin datos demo). |
| `python manage.py cargar_demo` | Carga la empresa ficticia, 24 empleados, novedades, préstamos y la nómina de septiembre a noviembre de 2026. Solo funciona con la base vacía. | Demostraciones y pruebas manuales. |
| `python manage.py cargar_demo --sin-historia` | Igual, pero sin liquidar ni cerrar periodos. | Practicar el ciclo completo desde cero. |
| `python manage.py createsuperuser` | Crea un usuario Administrador. | Instalación limpia. |
| `python manage.py documentar_bd` | Regenera `docs/base-de-datos/diagrama-er.md` y `diccionario.md` desde los modelos. | Después de cambiar modelos. |
| `python manage.py test apps.nomina` | Ejecuta las pruebas automatizadas. | Antes de cada cambio en reglas de cálculo. |
| `python manage.py runserver` | Inicia el servidor local en el puerto 8000. | Uso diario. |

## 5.2 Pruebas automatizadas

`apps/nomina/tests.py` contiene 19 pruebas:

| Grupo | Qué verifica |
|---|---|
| `UtilidadesTest` | Días comerciales (`dias360`) y redondeos. |
| `MotorTest` | Salario mínimo completo, quincenas, ingreso a mitad de periodo, auxilio de transporte, factores de horas, incapacidad con piso mínimo y continuidad entre periodos, licencia no remunerada, regla del 40 %, salario integral, retención en la fuente, escala del FSP, tope de 25 SMMLV, préstamo sin neto negativo y pensionados. |
| `CicloPeriodoTest` | Liquidar, cerrar y reabrir con datos reales en MySQL; un periodo cerrado no se reliquida. |

`MotorTest` no usa la base de datos (`SimpleTestCase`): construye contratos, novedades y parámetros en memoria, así que se ejecuta en milisegundos. `CicloPeriodoTest` crea la base temporal `test_libra_nomina`; el usuario de MySQL necesita permiso para crearla (ver README).

```bash
python manage.py test apps.nomina -v 2
```

## 5.3 Cómo agregar un concepto de nómina

Ejemplo: un **auxilio de conectividad** no salarial pagado por valor.

1. Agréguelo al catálogo en `apps/nomina/catalogo.py`:

   ```python
   ("AUXCO", "Auxilio de conectividad", "DEV", "VAL", False, False, False, False, 54, "Auxilio no salarial para trabajo en casa."),
   ```

   Columnas: código, nombre, tipo (`DEV`, `DED`, `APO`, `PRO`, `INF`), captura (`SIS`, `HOR`, `DIA`, `VAL`), salarial, base de seguridad social, base de prestaciones, base de vacaciones, orden y descripción.

2. Ejecute `python manage.py inicializar_catalogos`.

3. Si es **no salarial** y debe contar para la regla del 40 %, agréguelo a la tupla en `MotorNomina._calcular_bases`:

   ```python
   no_salarial = sum((l.valor for l in devengados if l.codigo in ("BONNS", "AUXNS", "AUXCO")), CERO)
   ```

Los conceptos por **valor** no requieren más código: el motor los paga o descuenta según su tipo. Los conceptos por **horas** necesitan su factor en `MotorNomina.factor_hora`. Los conceptos **por días** necesitan su tasa en `TASA_AUSENCIA` y su posición en `ORDEN_AUSENCIAS`. Los conceptos **calculados por el sistema** (`SIS`) requieren una regla nueva en `MotorNomina.liquidar`.

4. Escriba una prueba en `MotorTest`.

## 5.4 Actualización anual de parámetros

Cada enero (y cuando cambie la jornada o un recargo):

1. *Configuración → Parámetros legales → **Nueva vigencia***, o
2. agregue el registro a `PARAMETROS` en `apps/core/management/commands/inicializar_catalogos.py` y ejecute el comando (para que una instalación nueva lo traiga).

El motor toma la vigencia con la mayor `vigente_desde` que sea menor o igual a la **fecha final** del periodo. Por eso un cambio con vigencia el 15 de julio se aplica a toda la primera quincena de julio.

## 5.5 Puntos de extensión del motor

`MotorNomina.liquidar()` aplica las reglas en 12 pasos numerados en el código. Para agregar una regla:

- Reciba los datos como atributos de los objetos que ya llegan (`contrato`, `novedades`, `prestamos`, `parametros`) para mantener el motor sin acceso a la base de datos.
- Agregue líneas con `r.lineas.append(Linea(codigo, valor, cantidad, base, tasa, novedad_id, prestamo_id))`.
- Si la regla debe advertir algo al usuario, use `r.advertencias.append("…")`. Se muestra en la página del periodo y en el detalle.

Las bases (`ibc`, `base_parafiscales`, `base_prestaciones`, `base_vacaciones`) se calculan con las banderas del catálogo, así que un devengado nuevo entra en ellas sin cambiar el código.

## 5.6 Interfaz

| Elemento | Ubicación |
|---|---|
| Hoja de estilos única | `static/css/libra.css`. Las variables de color están al inicio (`--pizarra-700`, `--cobre`, etc.). |
| Plantilla base con menú | `templates/base.html` |
| Campo de formulario | `templates/comun/_campo.html`, usado con `{% campo form.x 6 %}` (el número es el ancho en una rejilla de 12 columnas). |
| Formularios genéricos | `templates/comun/formulario.html` + `apps/core/vistas_base.formulario()` |
| Filtros de formato | `apps/core/templatetags/libra.py`: `pesos`, `numero`, `porcentaje`, `estado`, `iniciales`. |

Paleta institucional:

| Variable | Color | Uso |
|---|---|---|
| `--pizarra-900` | `#16302F` | Menú lateral |
| `--pizarra-700` | `#1F3B3A` | Botón primario, cifra destacada, encabezados de PDF y Excel |
| `--cobre` | `#9A6A2F` | Acento: opción activa, cierre de periodo, subrayado de cifras |
| `--papel` | `#F4F3EF` | Fondo de la aplicación |

## 5.7 Configuración (`.env`)

| Variable | Descripción | Ejemplo |
|---|---|---|
| `SECRET_KEY` | Clave criptográfica de Django. Única por instalación. | cadena aleatoria de 50 caracteres |
| `DEBUG` | `True` muestra errores detallados. Use `False` si otras personas acceden al equipo. | `True` |
| `ALLOWED_HOSTS` | Nombres o IP con los que se accede, separados por coma. | `127.0.0.1,localhost` |
| `DB_NAME` | Base de datos | `libra_nomina` |
| `DB_USER` / `DB_PASSWORD` | Credenciales de MySQL | `libra` / `…` |
| `DB_HOST` / `DB_PORT` | Servidor de MySQL | `127.0.0.1` / `3306` |

Con `DEBUG=False`, ejecute `python manage.py collectstatic` y sirva la carpeta `staticfiles/` con un servidor web, o use `python manage.py runserver --insecure` solo en uso local.

## 5.8 Uso desde otros equipos de la red local

```bash
python manage.py runserver 0.0.0.0:8000
```

Agregue la IP del equipo a `ALLOWED_HOSTS` (por ejemplo `192.168.1.20`) y permita el puerto 8000 en el firewall de Windows. Para uso permanente con varios usuarios, se recomienda un servidor WSGI (por ejemplo `waitress` en Windows) en lugar de `runserver`.

## 5.9 Auditoría

`apps.core.auditoria.registrar(usuario, accion, objeto, detalle)` deja un registro en la tabla `auditoria`. Acciones registradas actualmente: `CREAR`, `EDITAR`, `ANULAR`, `ELIMINAR`, `LIQUIDAR`, `CERRAR`, `REABRIR`, `LIQ_CONTRATO`, `APROBAR_LIQ`. Llame a `registrar` desde cualquier vista o servicio nuevo que modifique datos.

## 5.10 Solución de problemas

| Síntoma | Causa probable | Solución |
|---|---|---|
| `django.db.utils.OperationalError: (2003, "Can't connect to MySQL server")` | MySQL no está iniciado, o el puerto en `.env` es incorrecto. | Inicie el servicio `MySQL80` en *Servicios* de Windows y verifique `DB_PORT`. |
| `(1045, "Access denied for user 'libra'")` | Usuario o contraseña de `.env` incorrectos. | Verifique las credenciales o vuelva a ejecutar el script de creación del usuario. |
| `(1049, "Unknown database 'libra_nomina'")` | No se creó la base. | Ejecute el paso de creación de la base del README. |
| `MariaDB 10.5 or later is required` | Se está usando MariaDB antigua (por ejemplo, la de XAMPP). | Instale MySQL 8.0 o superior. |
| Error al instalar `mysqlclient` | Versión de Python sin rueda precompilada. | Use Python 3.11, 3.12 o 3.13 de 64 bits. |
| Las pruebas fallan con `Got an error creating the test database` | El usuario de MySQL no puede crear `test_libra_nomina`. | Otorgue `GRANT ALL ON test_libra_nomina.* TO 'libra'@'localhost';` |
| La página se ve sin estilos | `DEBUG=False` sin servir archivos estáticos. | Ver sección 5.7. |
| Acentos incorrectos en la consola de Windows | Codificación de la consola. | Ejecute `chcp 65001` o defina `PYTHONIOENCODING=utf-8`. No afecta a la aplicación. |
