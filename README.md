# Libra — Sistema de Nómina

Software de nómina para **Cordillera Industrial S.A.S.** (empresa ficticia), bajo la legislación laboral colombiana. Se instala y funciona **localmente**, sin servicios en la nube y sin conexión a internet.

| | |
|---|---|
| **Versión** | 1.0.0 |
| **Tecnología** | Python 3.11+ · Django 5.2 LTS · MySQL 8 |
| **Periodicidad** | Quincenal y mensual |
| **Usuarios** | Administrador, Analista de nómina, Consulta |

## Funcionalidades

- **Personal**: empleados, contratos (indefinido, fijo, obra o labor; salario ordinario o integral), cargos, áreas y centros de costo.
- **Novedades**: horas extra y recargos, incapacidades, licencias, vacaciones, suspensiones, comisiones, bonificaciones, auxilios y descuentos.
- **Préstamos y libranzas** con descuento automático de cuotas y control de saldo.
- **Liquidación** de devengados, salud, pensión, fondo de solidaridad, retención en la fuente, aportes del empleador (con exoneración del art. 114-1 E.T.) y provisiones de prestaciones.
- **Ciclo de periodo**: abierto → liquidado → cerrado, con reapertura controlada.
- **Desprendibles de pago en PDF**, sábana de nómina y archivo de dispersión bancaria en Excel.
- **Liquidación definitiva de contratos**: cesantías, intereses, prima, vacaciones e indemnización.
- **Reportes**: costo por centro de costo, aportes por entidad y provisiones.
- **Parámetros legales con vigencia por fecha** (SMMLV, auxilio, UVT, jornada, recargos de la Ley 2466 de 2025).
- **Roles, auditoría** de acciones y tablero de control.

---

## Instalación

Las instrucciones están escritas para **Windows 10/11**. Al final hay notas para Linux y macOS.

### 1. Requisitos previos

| Software | Versión | Descarga |
|---|---|---|
| Python | 3.11, 3.12 o 3.13 (64 bits) | <https://www.python.org/downloads/> — marque **"Add python.exe to PATH"** al instalar |
| MySQL Server | 8.0 o superior | <https://dev.mysql.com/downloads/installer/> — durante la instalación defina la contraseña de `root` |
| Navegador | Chrome, Edge o Firefox actualizados | |

Verifique en una terminal (PowerShell o CMD):

```powershell
python --version      # Python 3.11.x o superior
mysql --version       # mysql  Ver 8.x
```

> Si `mysql` no se reconoce, agregue `C:\Program Files\MySQL\MySQL Server 8.4\bin` (o su versión) a la variable `PATH`, o use la ruta completa al ejecutable.
>
> **No use el MariaDB de XAMPP** (versión 10.4): Django 5.2 exige MySQL 8.0+ o MariaDB 10.5+.
>
> Alternativa para instalar MySQL desde la terminal: `winget install Oracle.MySQL`, y luego configure el servidor con *MySQL Configurator*.

### 2. Ubicar el proyecto

Copie la carpeta `nomina-corp` en el equipo, por ejemplo en `C:\Users\<usuario>\nomina-corp`, y abra una terminal en ella:

```powershell
cd C:\Users\<usuario>\nomina-corp
```

### 3. Crear el entorno virtual e instalar dependencias

```powershell
python -m venv .venv
.\.venv\Scripts\activate
python -m pip install --upgrade pip
pip install -r requirements.txt
```

Al activar el entorno, la línea de comandos muestra `(.venv)` al inicio. Todos los comandos siguientes se ejecutan con el entorno activo.

> Si PowerShell bloquea la activación con un error de *ejecución de scripts*, ejecute una vez `Set-ExecutionPolicy -Scope CurrentUser RemoteSigned` o use CMD con `.venv\Scripts\activate.bat`.

### 4. Crear la base de datos y el usuario en MySQL

```powershell
mysql -u root -p < scripts\crear_base_mysql.sql
```

Escriba la contraseña de `root`. El script crea:

- la base `libra_nomina` con `utf8mb4`;
- el usuario `libra` con contraseña `libra2026` (cámbiela en el script si lo desea);
- los permisos para las pruebas automatizadas.

### 5. Configurar el archivo `.env`

```powershell
copy .env.ejemplo .env
```

Abra `.env` con un editor y ajuste los valores:

```ini
SECRET_KEY=pegue-aqui-una-clave-aleatoria
DEBUG=True
ALLOWED_HOSTS=127.0.0.1,localhost
DB_NAME=libra_nomina
DB_USER=libra
DB_PASSWORD=libra2026
DB_HOST=127.0.0.1
DB_PORT=3306
```

Para generar una clave secreta:

```powershell
python -c "import secrets; print(secrets.token_urlsafe(50))"
```

### 6. Crear las tablas

```powershell
python manage.py migrate
```

### 7. Cargar datos

Elija **una** opción.

**Opción A — Empresa de demostración (recomendada para conocer el sistema)**

```powershell
python manage.py cargar_demo
```

Carga Cordillera Industrial S.A.S. con 24 empleados, novedades, préstamos y la nómina de septiembre y octubre de 2026 cerrada, más noviembre en curso. Crea tres usuarios:

| Usuario | Contraseña | Rol |
|---|---|---|
| `admin` | `Libra2026*` | Administrador |
| `analista` | `Libra2026*` | Analista de nómina |
| `consulta` | `Libra2026*` | Consulta |

**Opción B — Instalación limpia para datos propios**

```powershell
python manage.py inicializar_catalogos
python manage.py createsuperuser
```

Luego ingrese al sistema y registre los datos de la empresa en *Configuración → Empresa*, y la estructura en *Personal → Estructura organizacional*.

### 8. Iniciar el sistema

```powershell
python manage.py runserver
```

Abra <http://127.0.0.1:8000> en el navegador. Para detener el servidor, pulse `Ctrl + C` en la terminal.

En adelante puede iniciar el sistema con doble clic en **`iniciar.bat`**: activa el entorno, inicia el servidor y abre el navegador.

### 9. Verificar la instalación (opcional)

```powershell
python manage.py test apps.nomina
```

El resultado esperado es `Ran 19 tests … OK`.

---

## Linux y macOS

Los pasos son los mismos, con estas diferencias:

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.ejemplo .env
mysql -u root -p < scripts/crear_base_mysql.sql
```

Para compilar `mysqlclient` se requieren las cabeceras de MySQL:

- Debian/Ubuntu: `sudo apt install python3-dev default-libmysqlclient-dev build-essential pkg-config`
- macOS (Homebrew): `brew install mysql pkg-config`

---

## Uso rápido

1. **Personal → Empleados**: revise o registre empleados y sus contratos.
2. **Operación → Novedades**: registre horas extra, incapacidades, comisiones, etc.
3. **Operación → Periodos de nómina → Nuevo periodo**: cree la quincena o el mes.
4. En el periodo, pulse **Liquidar** y revise los resultados.
5. Pulse **Cerrar periodo** (Administrador) y descargue los **desprendibles PDF** y la **sábana Excel**.

El detalle completo está en el [manual de usuario](docs/04-manual-de-usuario.md).

---

## Documentación

| Documento | Contenido |
|---|---|
| [1. Arquitectura](docs/01-arquitectura.md) | Tecnologías, componentes, capas, flujos, estados, seguridad y decisiones de diseño. |
| [2. Base de datos](docs/02-base-de-datos.md) | Modelo conceptual y físico, tablas, integridad, convenciones, consultas y respaldo. |
| [2.1 Diagrama entidad-relación](docs/base-de-datos/diagrama-er.md) | Diagrama completo por módulo, generado desde el código. |
| [2.2 Diccionario de datos](docs/base-de-datos/diccionario.md) | Cada tabla y columna con su tipo, llaves y descripción. |
| [2.3 Script DDL](docs/base-de-datos/esquema.sql) | Sentencias `CREATE TABLE` del esquema MySQL. |
| [3. Reglas de cálculo](docs/03-reglas-de-calculo.md) | Fórmulas de liquidación, fundamento legal y ejemplo resuelto. |
| [4. Manual de usuario](docs/04-manual-de-usuario.md) | Operación de cada módulo paso a paso. |
| [5. Guía técnica](docs/05-guia-tecnica.md) | Comandos, pruebas, extensión del motor, configuración y solución de problemas. |

Los diagramas están escritos en **Mermaid** dentro de los documentos y se ven en Visual Studio Code con la extensión *Markdown Preview Mermaid Support* (`bierner.markdown-mermaid`). También están exportados como imágenes **SVG** en [`docs/diagramas/`](docs/diagramas/), que se abren con cualquier navegador:

| Archivo | Diagrama |
|---|---|
| `01-arquitectura-componentes.svg` | Componentes y capas |
| `02-arquitectura-secuencia-liquidacion.svg` | Secuencia de liquidación de un periodo |
| `03-arquitectura-estados-periodo.svg` | Estados del periodo |
| `04-arquitectura-estados-novedad.svg` | Estados de la novedad |
| `05-bd-modelo-conceptual.svg` | Modelo entidad-relación conceptual |
| `06-bd-modelo-fisico.svg` | Modelo físico de las tablas centrales |
| `07-calculo-orden.svg` | Orden de cálculo del motor |
| `08-manual-ciclo-mensual.svg` | Ciclo mensual de trabajo |
| `09` a `12-er-*.svg` | Diagramas ER completos por módulo y vista general |

---

## Estructura del proyecto

```
nomina-corp/
├── apps/
│   ├── core/          Empresa, parámetros legales, entidades, usuarios, auditoría, tablero
│   ├── personal/      Estructura organizacional, empleados y contratos
│   └── nomina/        Conceptos, novedades, préstamos, periodos, liquidaciones, reportes
│       └── servicios/ Motor de cálculo, liquidador, retiros y documentos
├── config/            Configuración de Django
├── docs/              Documentación
├── scripts/           Script SQL de creación de la base
├── static/            Hoja de estilos e imagen de marca
├── templates/         Plantillas HTML
├── iniciar.bat        Inicio rápido en Windows
├── manage.py
└── requirements.txt
```

## Aviso

Cordillera Industrial S.A.S., sus empleados y sus datos son **ficticios**. Los parámetros legales precargados corresponden a la normativa colombiana de 2025 y 2026; verifíquelos antes de usar el sistema con datos reales y actualícelos cada año en *Configuración → Parámetros legales*.
