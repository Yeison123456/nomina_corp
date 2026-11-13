# Diccionario de datos

> Archivo generado con `python manage.py documentar_bd`. No lo edite a mano.

Motor: **MySQL 8**, juego de caracteres `utf8mb4`, motor de almacenamiento InnoDB. 
Todas las tablas tienen llave primaria `id BIGINT AUTO_INCREMENT`. Los valores monetarios 
se almacenan como `DECIMAL(14,2)` en pesos colombianos y los porcentajes como fracción 
decimal (`0.04` = 4 %).

## Índice de tablas

| Tabla | Módulo | Descripción |
|---|---|---|
| [`empresa`](#empresa) | Configuración general | Datos del empleador. El sistema opera con una sola empresa (registro único). |
| [`parametro_legal`](#parametro_legal) | Configuración general | Valores legales vigentes a partir de una fecha. Para liquidar un periodo se usa el registro con la mayor `vigente_desde` que sea menor o igual a la fecha final del periodo. |
| [`entidad`](#entidad) | Configuración general | Entidades del sistema de seguridad social y bancos. |
| [`auditoria`](#auditoria) | Configuración general | Bitácora de acciones relevantes realizadas por los usuarios. |
| [`centro_costo`](#centro_costo) | Personal | Agrupación contable a la que se imputa el costo de la nómina. |
| [`area`](#area) | Personal | Dependencia de la empresa. Pertenece a un centro de costo. |
| [`cargo`](#cargo) | Personal | Puesto de trabajo con su salario de referencia. |
| [`empleado`](#empleado) | Personal | Datos personales, cuenta de pago y afiliaciones a seguridad social del trabajador. |
| [`contrato`](#contrato) | Personal | Vínculo laboral: condiciones salariales, periodicidad de pago, cargo y riesgo ARL. |
| [`concepto`](#concepto) | Nómina | Catálogo de conceptos que pueden aparecer en una liquidación. |
| [`periodo_nomina`](#periodo_nomina) | Nómina | Quincena o mes de nómina. Ciclo de vida: Abierto → Liquidado → Cerrado. |
| [`novedad`](#novedad) | Nómina | Hechos del periodo que modifican la liquidación de un contrato. |
| [`prestamo`](#prestamo) | Nómina | Préstamos y libranzas que se descuentan en cuotas por periodo. |
| [`liquidacion_nomina`](#liquidacion_nomina) | Nómina | Resultado de liquidar un contrato en un periodo (encabezado). |
| [`detalle_liquidacion`](#detalle_liquidacion) | Nómina | Línea de una liquidación: un concepto con su cantidad, base, tasa y valor. |
| [`liquidacion_contrato`](#liquidacion_contrato) | Nómina | Liquidación definitiva de prestaciones sociales al terminar un contrato. |

Tablas del framework utilizadas: `auth_user` (usuarios), `auth_group` (roles), `auth_user_groups`, `django_session`, `django_migrations`.

## empresa

Datos del empleador. El sistema opera con una sola empresa (registro único).

| Columna | Tipo MySQL | Nulo | Llave | Predeterminado | Descripción |
|---|---|---|---|---|---|
| `id` | `bigint` | No | PK |  | Identificador único autoincremental. |
| `razon_social` | `varchar(150)` | No |  |  | Razón social. |
| `nit` | `varchar(20)` | No |  |  | NIT. NIT con dígito de verificación. |
| `direccion` | `varchar(150)` | No |  |  | Dirección. |
| `ciudad` | `varchar(80)` | No |  |  | Ciudad. |
| `telefono` | `varchar(30)` | No |  |  | Teléfono. |
| `correo` | `varchar(254)` | No |  |  | Correo de nómina. |
| `representante_legal` | `varchar(120)` | No |  |  | Representante legal. |
| `actividad_economica` | `varchar(150)` | No |  |  | Actividad económica. |
| `exonerada_aportes` | `tinyint(1)` | No |  | `True` | Exonerada art. 114-1 E.T. Si es verdadero, no paga salud empleador, SENA ni ICBF por trabajadores que devenguen menos de 10 SMMLV. |

## parametro_legal

Valores legales vigentes a partir de una fecha. Para liquidar un periodo se usa el registro con la mayor `vigente_desde` que sea menor o igual a la fecha final del periodo.

| Columna | Tipo MySQL | Nulo | Llave | Predeterminado | Descripción |
|---|---|---|---|---|---|
| `id` | `bigint` | No | PK |  | Identificador único autoincremental. |
| `vigente_desde` | `date` | No | UK |  | Vigente desde. |
| `descripcion` | `varchar(150)` | No |  |  | Descripción. Norma o motivo del cambio. |
| `smmlv` | `decimal(14,2)` | No |  |  | SMMLV. Salario mínimo mensual legal vigente. |
| `auxilio_transporte` | `decimal(14,2)` | No |  |  | Auxilio de transporte. |
| `uvt` | `decimal(14,2)` | No |  |  | UVT. Unidad de valor tributario del año. |
| `horas_mes` | `smallint UNSIGNED` | No |  |  | Horas laborales al mes. Divisor para el valor de la hora ordinaria (jornada semanal × 5). |
| `pct_recargo_nocturno` | `decimal(6,4)` | No |  | `0.35` | % recargo nocturno. |
| `pct_recargo_dominical` | `decimal(6,4)` | No |  |  | % recargo dominical y festivo. |
| `pct_extra_diurna` | `decimal(6,4)` | No |  | `0.25` | % hora extra diurna. |
| `pct_extra_nocturna` | `decimal(6,4)` | No |  | `0.75` | % hora extra nocturna. |
| `pct_salud_empleado` | `decimal(6,4)` | No |  | `0.04` | % salud empleado. |
| `pct_pension_empleado` | `decimal(6,4)` | No |  | `0.04` | % pensión empleado. |
| `pct_salud_empleador` | `decimal(6,4)` | No |  | `0.085` | % salud empleador. |
| `pct_pension_empleador` | `decimal(6,4)` | No |  | `0.12` | % pensión empleador. |
| `pct_caja` | `decimal(6,4)` | No |  | `0.04` | % caja de compensación. |
| `pct_icbf` | `decimal(6,4)` | No |  | `0.03` | % ICBF. |
| `pct_sena` | `decimal(6,4)` | No |  | `0.02` | % SENA. |

## entidad

Entidades del sistema de seguridad social y bancos.

| Columna | Tipo MySQL | Nulo | Llave | Predeterminado | Descripción |
|---|---|---|---|---|---|
| `id` | `bigint` | No | PK |  | Identificador único autoincremental. |
| `tipo` | `varchar(3)` | No |  |  | Tipo. Valores: `EPS` EPS (salud), `AFP` Fondo de pensiones, `CES` Fondo de cesantías, `CCF` Caja de compensación, `ARL` Administradora de riesgos laborales, `BAN` Banco. |
| `nombre` | `varchar(120)` | No |  |  | Nombre. |
| `nit` | `varchar(20)` | No |  |  | NIT. |
| `codigo` | `varchar(12)` | No |  |  | Código. Código interno o bancario de la entidad. |
| `activa` | `tinyint(1)` | No |  | `True` | Activa. |

**Restricciones**

- Único compuesto: (`tipo`, `nombre`)

## auditoria

Bitácora de acciones relevantes realizadas por los usuarios.

| Columna | Tipo MySQL | Nulo | Llave | Predeterminado | Descripción |
|---|---|---|---|---|---|
| `id` | `bigint` | No | PK |  | Identificador único autoincremental. |
| `fecha` | `datetime(6)` | No |  | fecha actual | Fecha. |
| `usuario_id` | `integer` | Sí | FK → `auth_user` |  | Usuario. |
| `accion` | `varchar(40)` | No |  |  | Acción. |
| `objeto` | `varchar(120)` | No |  |  | Objeto. Tipo e identificador del registro afectado. |
| `detalle` | `longtext` | No |  |  | Detalle. |

**Restricciones**

- `usuario_id` → `auth_user.id` (índice y llave foránea). Al eliminar el registro padre: la columna queda en NULL.

## centro_costo

Agrupación contable a la que se imputa el costo de la nómina.

| Columna | Tipo MySQL | Nulo | Llave | Predeterminado | Descripción |
|---|---|---|---|---|---|
| `id` | `bigint` | No | PK |  | Identificador único autoincremental. |
| `codigo` | `varchar(10)` | No | UK |  | Código. |
| `nombre` | `varchar(100)` | No |  |  | Nombre. |
| `activo` | `tinyint(1)` | No |  | `True` | Activo. |

## area

Dependencia de la empresa. Pertenece a un centro de costo.

| Columna | Tipo MySQL | Nulo | Llave | Predeterminado | Descripción |
|---|---|---|---|---|---|
| `id` | `bigint` | No | PK |  | Identificador único autoincremental. |
| `codigo` | `varchar(10)` | No | UK |  | Código. |
| `nombre` | `varchar(100)` | No |  |  | Nombre. |
| `centro_costo_id` | `bigint` | No | FK → `centro_costo` |  | Centro costo. |

**Restricciones**

- `centro_costo_id` → `centro_costo.id` (índice y llave foránea). Al eliminar el registro padre: se impide si existen registros relacionados.

## cargo

Puesto de trabajo con su salario de referencia.

| Columna | Tipo MySQL | Nulo | Llave | Predeterminado | Descripción |
|---|---|---|---|---|---|
| `id` | `bigint` | No | PK |  | Identificador único autoincremental. |
| `codigo` | `varchar(10)` | No | UK |  | Código. |
| `nombre` | `varchar(100)` | No |  |  | Nombre. |
| `area_id` | `bigint` | No | FK → `area` |  | Area. |
| `salario_referencia` | `decimal(14,2)` | No |  | `0` | Salario de referencia. Valor sugerido al crear un contrato para este cargo. |

**Restricciones**

- `area_id` → `area.id` (índice y llave foránea). Al eliminar el registro padre: se impide si existen registros relacionados.

## empleado

Datos personales, cuenta de pago y afiliaciones a seguridad social del trabajador.

| Columna | Tipo MySQL | Nulo | Llave | Predeterminado | Descripción |
|---|---|---|---|---|---|
| `id` | `bigint` | No | PK |  | Identificador único autoincremental. |
| `tipo_documento` | `varchar(3)` | No |  | `CC` | Tipo de documento. Valores: `CC` Cédula de ciudadanía, `CE` Cédula de extranjería, `PA` Pasaporte, `PPT` Permiso por protección temporal. |
| `numero_documento` | `varchar(20)` | No | UK |  | Número de documento. |
| `nombres` | `varchar(80)` | No |  |  | Nombres. |
| `apellidos` | `varchar(80)` | No |  |  | Apellidos. |
| `fecha_nacimiento` | `date` | No |  |  | Fecha de nacimiento. |
| `genero` | `varchar(1)` | No |  |  | Género. Valores: `F` Femenino, `M` Masculino, `O` Otro / no informa. |
| `correo` | `varchar(254)` | No |  |  | Correo. |
| `telefono` | `varchar(30)` | No |  |  | Teléfono. |
| `direccion` | `varchar(150)` | No |  |  | Dirección. |
| `ciudad` | `varchar(80)` | No |  | `Bogotá D.C.` | Ciudad. |
| `banco_id` | `bigint` | Sí | FK → `entidad` |  | Banco. |
| `tipo_cuenta` | `varchar(2)` | No |  |  | Tipo de cuenta. Valores: `AH` Ahorros, `CC` Corriente. |
| `numero_cuenta` | `varchar(30)` | No |  |  | Número de cuenta. |
| `eps_id` | `bigint` | No | FK → `entidad` |  | EPS. |
| `afp_id` | `bigint` | Sí | FK → `entidad` |  | Fondo de pensiones. Vacío solo para pensionados o trabajadores no obligados a cotizar. |
| `fondo_cesantias_id` | `bigint` | Sí | FK → `entidad` |  | Fondo de cesantías. |
| `caja_id` | `bigint` | No | FK → `entidad` |  | Caja de compensación. |
| `activo` | `tinyint(1)` | No |  | `True` | Activo. |
| `creado` | `datetime(6)` | No |  | fecha actual | Creado. |
| `actualizado` | `datetime(6)` | No |  | fecha actual | Actualizado. |

**Restricciones**

- `banco_id` → `entidad.id` (índice y llave foránea). Al eliminar el registro padre: se impide si existen registros relacionados.
- `eps_id` → `entidad.id` (índice y llave foránea). Al eliminar el registro padre: se impide si existen registros relacionados.
- `afp_id` → `entidad.id` (índice y llave foránea). Al eliminar el registro padre: se impide si existen registros relacionados.
- `fondo_cesantias_id` → `entidad.id` (índice y llave foránea). Al eliminar el registro padre: se impide si existen registros relacionados.
- `caja_id` → `entidad.id` (índice y llave foránea). Al eliminar el registro padre: se impide si existen registros relacionados.

## contrato

Vínculo laboral: condiciones salariales, periodicidad de pago, cargo y riesgo ARL.

| Columna | Tipo MySQL | Nulo | Llave | Predeterminado | Descripción |
|---|---|---|---|---|---|
| `id` | `bigint` | No | PK |  | Identificador único autoincremental. |
| `numero` | `varchar(20)` | No | UK |  | Número de contrato. |
| `empleado_id` | `bigint` | No | FK → `empleado` |  | Empleado. |
| `tipo` | `varchar(3)` | No |  |  | Tipo de contrato. Valores: `IND` Término indefinido, `FIJ` Término fijo, `OBR` Obra o labor. |
| `tipo_salario` | `varchar(3)` | No |  | `ORD` | Tipo de salario. Valores: `ORD` Ordinario, `INT` Integral. |
| `salario` | `decimal(14,2)` | No |  |  | Salario mensual. |
| `cargo_id` | `bigint` | No | FK → `cargo` |  | Cargo. |
| `centro_costo_id` | `bigint` | No | FK → `centro_costo` |  | Centro de costo. |
| `periodicidad` | `varchar(1)` | No |  | `Q` | Periodicidad de pago. Valores: `Q` Quincenal, `M` Mensual. |
| `clase_riesgo` | `smallint UNSIGNED` | No |  | `1` | Clase de riesgo ARL. Valores: `1` Clase I — 0,522 %, `2` Clase II — 1,044 %, `3` Clase III — 2,436 %, `4` Clase IV — 4,350 %, `5` Clase V — 6,960 %. |
| `arl_id` | `bigint` | No | FK → `entidad` |  | ARL. |
| `fecha_inicio` | `date` | No |  |  | Fecha de inicio. |
| `fecha_fin` | `date` | Sí |  |  | Fecha de finalización pactada. Obligatoria para contratos a término fijo. |
| `estado` | `varchar(3)` | No |  | `VIG` | Estado. Valores: `VIG` Vigente, `TER` Terminado. |
| `fecha_terminacion` | `date` | Sí |  |  | Fecha de terminación. |
| `motivo_terminacion` | `varchar(150)` | No |  |  | Motivo de terminación. |

**Restricciones**

- `empleado_id` → `empleado.id` (índice y llave foránea). Al eliminar el registro padre: se impide si existen registros relacionados.
- `cargo_id` → `cargo.id` (índice y llave foránea). Al eliminar el registro padre: se impide si existen registros relacionados.
- `centro_costo_id` → `centro_costo.id` (índice y llave foránea). Al eliminar el registro padre: se impide si existen registros relacionados.
- `arl_id` → `entidad.id` (índice y llave foránea). Al eliminar el registro padre: se impide si existen registros relacionados.

## concepto

Catálogo de conceptos que pueden aparecer en una liquidación.

| Columna | Tipo MySQL | Nulo | Llave | Predeterminado | Descripción |
|---|---|---|---|---|---|
| `id` | `bigint` | No | PK |  | Identificador único autoincremental. |
| `codigo` | `varchar(10)` | No | UK |  | Código. |
| `nombre` | `varchar(80)` | No |  |  | Nombre. |
| `tipo` | `varchar(3)` | No |  |  | Tipo. Valores: `DEV` Devengado, `DED` Deducción, `APO` Aporte del empleador, `PRO` Provisión de prestaciones, `INF` Informativo (ausencia sin pago). |
| `captura` | `varchar(3)` | No |  | `SIS` | Captura. Valores: `SIS` Calculado por el sistema, `HOR` Novedad en horas, `DIA` Novedad en días (rango de fechas), `VAL` Novedad en valor. |
| `salarial` | `tinyint(1)` | No |  | `False` | Salarial. Constituye salario (art. 127 CST). |
| `base_seguridad_social` | `tinyint(1)` | No |  | `False` | Base seguridad social. Se suma al IBC. |
| `base_prestaciones` | `tinyint(1)` | No |  | `False` | Base prestaciones. Se suma a la base de cesantías, intereses y prima. |
| `base_vacaciones` | `tinyint(1)` | No |  | `False` | Base vacaciones. Se suma a la base de la provisión de vacaciones. |
| `orden` | `smallint UNSIGNED` | No |  | `100` | Orden. Orden de presentación en el desprendible. |
| `descripcion` | `varchar(255)` | No |  |  | Descripción. |
| `activo` | `tinyint(1)` | No |  | `True` | Activo. |

## periodo_nomina

Quincena o mes de nómina. Ciclo de vida: Abierto → Liquidado → Cerrado.

| Columna | Tipo MySQL | Nulo | Llave | Predeterminado | Descripción |
|---|---|---|---|---|---|
| `id` | `bigint` | No | PK |  | Identificador único autoincremental. |
| `periodicidad` | `varchar(1)` | No |  |  | Periodicidad. Valores: `Q` Quincenal, `M` Mensual. |
| `anio` | `smallint UNSIGNED` | No |  |  | Año. |
| `mes` | `smallint UNSIGNED` | No |  |  | Mes. |
| `numero` | `smallint UNSIGNED` | No |  | `1` | Número. 1 o 2 para quincenas; 1 para nómina mensual. |
| `fecha_inicio` | `date` | No |  |  | Fecha de inicio. |
| `fecha_fin` | `date` | No |  |  | Fecha final. |
| `fecha_pago` | `date` | No |  |  | Fecha de pago. |
| `estado` | `varchar(3)` | No |  | `BOR` | Estado. Valores: `BOR` Abierto, `LIQ` Liquidado, `CER` Cerrado. |
| `observaciones` | `longtext` | No |  |  | Observaciones. |
| `liquidado_por_id` | `integer` | Sí | FK → `auth_user` |  | Liquidado por. |
| `fecha_liquidacion` | `datetime(6)` | Sí |  |  | Fecha de liquidación. |
| `cerrado_por_id` | `integer` | Sí | FK → `auth_user` |  | Cerrado por. |
| `fecha_cierre` | `datetime(6)` | Sí |  |  | Fecha de cierre. |

**Restricciones**

- Único compuesto: (`periodicidad`, `anio`, `mes`, `numero`)
- `liquidado_por_id` → `auth_user.id` (índice y llave foránea). Al eliminar el registro padre: la columna queda en NULL.
- `cerrado_por_id` → `auth_user.id` (índice y llave foránea). Al eliminar el registro padre: la columna queda en NULL.

## novedad

Hechos del periodo que modifican la liquidación de un contrato.

| Columna | Tipo MySQL | Nulo | Llave | Predeterminado | Descripción |
|---|---|---|---|---|---|
| `id` | `bigint` | No | PK |  | Identificador único autoincremental. |
| `contrato_id` | `bigint` | No | FK → `contrato` |  | Contrato. |
| `concepto_id` | `bigint` | No | FK → `concepto` |  | Concepto. |
| `fecha_inicio` | `date` | No |  |  | Fecha. Fecha del hecho o inicio del rango. |
| `fecha_fin` | `date` | Sí |  |  | Fecha final. Solo para novedades por días. |
| `cantidad` | `decimal(10,2)` | No |  | `0` | Cantidad. Horas, o días hábiles en vacaciones. |
| `valor` | `decimal(14,2)` | No |  | `0` | Valor. Solo para novedades por valor. |
| `observacion` | `varchar(255)` | No |  |  | Observación. |
| `estado` | `varchar(3)` | No |  | `PEN` | Estado. Valores: `PEN` Pendiente, `APL` Aplicada, `ANU` Anulada. |
| `periodo_aplicacion_id` | `bigint` | Sí | FK → `periodo_nomina` |  | Periodo de aplicación. Periodo cerrado en el que la novedad quedó aplicada por completo. |
| `registrado_por_id` | `integer` | Sí | FK → `auth_user` |  | Registrado por. |
| `creado` | `datetime(6)` | No |  | fecha actual | Creado. |

**Restricciones**

- `contrato_id` → `contrato.id` (índice y llave foránea). Al eliminar el registro padre: se impide si existen registros relacionados.
- `concepto_id` → `concepto.id` (índice y llave foránea). Al eliminar el registro padre: se impide si existen registros relacionados.
- `periodo_aplicacion_id` → `periodo_nomina.id` (índice y llave foránea). Al eliminar el registro padre: se impide si existen registros relacionados.
- `registrado_por_id` → `auth_user.id` (índice y llave foránea). Al eliminar el registro padre: la columna queda en NULL.

## prestamo

Préstamos y libranzas que se descuentan en cuotas por periodo.

| Columna | Tipo MySQL | Nulo | Llave | Predeterminado | Descripción |
|---|---|---|---|---|---|
| `id` | `bigint` | No | PK |  | Identificador único autoincremental. |
| `contrato_id` | `bigint` | No | FK → `contrato` |  | Contrato. |
| `concepto_id` | `bigint` | No | FK → `concepto` |  | Concepto. |
| `descripcion` | `varchar(150)` | No |  |  | Descripción. |
| `fecha` | `date` | No |  |  | Fecha de desembolso. |
| `monto` | `decimal(14,2)` | No |  |  | Monto. |
| `numero_cuotas` | `smallint UNSIGNED` | No |  |  | Número de cuotas. |
| `valor_cuota` | `decimal(14,2)` | No |  |  | Valor de la cuota. |
| `saldo` | `decimal(14,2)` | No |  |  | Saldo. |
| `estado` | `varchar(3)` | No |  | `ACT` | Estado. Valores: `ACT` Activo, `PAG` Pagado, `ANU` Anulado. |
| `creado` | `datetime(6)` | No |  | fecha actual | Creado. |

**Restricciones**

- `contrato_id` → `contrato.id` (índice y llave foránea). Al eliminar el registro padre: se impide si existen registros relacionados.
- `concepto_id` → `concepto.id` (índice y llave foránea). Al eliminar el registro padre: se impide si existen registros relacionados.

## liquidacion_nomina

Resultado de liquidar un contrato en un periodo (encabezado).

| Columna | Tipo MySQL | Nulo | Llave | Predeterminado | Descripción |
|---|---|---|---|---|---|
| `id` | `bigint` | No | PK |  | Identificador único autoincremental. |
| `periodo_id` | `bigint` | No | FK → `periodo_nomina` |  | Periodo. |
| `contrato_id` | `bigint` | No | FK → `contrato` |  | Contrato. |
| `salario` | `decimal(14,2)` | No |  |  | Salario mensual. |
| `dias_periodo` | `smallint UNSIGNED` | No |  |  | Días del contrato en el periodo. |
| `dias_trabajados` | `smallint UNSIGNED` | No |  |  | Días pagados como salario. |
| `ibc` | `decimal(14,2)` | No |  |  | IBC. Ingreso base de cotización. |
| `base_prestaciones` | `decimal(14,2)` | No |  |  | Base de prestaciones. |
| `total_devengado` | `decimal(14,2)` | No |  |  | Total devengado. |
| `total_deducciones` | `decimal(14,2)` | No |  |  | Total deducciones. |
| `neto_pagar` | `decimal(14,2)` | No |  |  | Neto a pagar. |
| `total_aportes` | `decimal(14,2)` | No |  |  | Total aportes empleador. |
| `total_provisiones` | `decimal(14,2)` | No |  |  | Total provisiones. |
| `advertencias` | `longtext` | No |  |  | Advertencias. Observaciones generadas por el motor de cálculo, una por línea. |
| `creado` | `datetime(6)` | No |  | fecha actual | Creado. |

**Restricciones**

- Único compuesto: (`periodo_id`, `contrato_id`)
- `periodo_id` → `periodo_nomina.id` (índice y llave foránea). Al eliminar el registro padre: se eliminan también estos registros.
- `contrato_id` → `contrato.id` (índice y llave foránea). Al eliminar el registro padre: se impide si existen registros relacionados.

## detalle_liquidacion

Línea de una liquidación: un concepto con su cantidad, base, tasa y valor.

| Columna | Tipo MySQL | Nulo | Llave | Predeterminado | Descripción |
|---|---|---|---|---|---|
| `id` | `bigint` | No | PK |  | Identificador único autoincremental. |
| `liquidacion_id` | `bigint` | No | FK → `liquidacion_nomina` |  | Liquidacion. |
| `concepto_id` | `bigint` | No | FK → `concepto` |  | Concepto. |
| `cantidad` | `decimal(10,2)` | No |  | `0` | Cantidad. Días u horas, según el concepto. |
| `base` | `decimal(14,2)` | No |  | `0` | Base. |
| `tasa` | `decimal(8,5)` | No |  | `0` | Tasa. Porcentaje o factor aplicado sobre la base. |
| `valor` | `decimal(14,2)` | No |  |  | Valor. |
| `novedad_id` | `bigint` | Sí | FK → `novedad` |  | Novedad. |
| `prestamo_id` | `bigint` | Sí | FK → `prestamo` |  | Prestamo. |

**Restricciones**

- `liquidacion_id` → `liquidacion_nomina.id` (índice y llave foránea). Al eliminar el registro padre: se eliminan también estos registros.
- `concepto_id` → `concepto.id` (índice y llave foránea). Al eliminar el registro padre: se impide si existen registros relacionados.
- `novedad_id` → `novedad.id` (índice y llave foránea). Al eliminar el registro padre: la columna queda en NULL.
- `prestamo_id` → `prestamo.id` (índice y llave foránea). Al eliminar el registro padre: la columna queda en NULL.

## liquidacion_contrato

Liquidación definitiva de prestaciones sociales al terminar un contrato.

| Columna | Tipo MySQL | Nulo | Llave | Predeterminado | Descripción |
|---|---|---|---|---|---|
| `id` | `bigint` | No | PK |  | Identificador único autoincremental. |
| `contrato_id` | `bigint` | No | FK → `contrato` |  | Contrato. |
| `fecha_retiro` | `date` | No |  |  | Fecha de retiro. |
| `causa` | `varchar(3)` | No |  |  | Causa. Valores: `REN` Renuncia voluntaria, `MUT` Mutuo acuerdo, `VEN` Vencimiento del término pactado, `JUS` Despido con justa causa, `SJC` Despido sin justa causa. |
| `salario` | `decimal(14,2)` | No |  |  | Salario mensual. |
| `auxilio_transporte` | `decimal(14,2)` | No |  | `0` | Auxilio de transporte. |
| `promedio_variable` | `decimal(14,2)` | No |  | `0` | Promedio salarial variable. |
| `dias_cesantias` | `integer UNSIGNED` | No |  |  | Días para cesantías. |
| `base_cesantias` | `decimal(14,2)` | No |  |  | Base de cesantías y prima. |
| `cesantias` | `decimal(14,2)` | No |  |  | Cesantías. |
| `intereses_cesantias` | `decimal(14,2)` | No |  |  | Intereses sobre cesantías. |
| `dias_prima` | `integer UNSIGNED` | No |  |  | Días para prima. |
| `prima` | `decimal(14,2)` | No |  |  | Prima de servicios. |
| `dias_vacaciones` | `decimal(8,2)` | No |  |  | Días de vacaciones pendientes. |
| `vacaciones` | `decimal(14,2)` | No |  |  | Vacaciones compensadas. |
| `indemnizacion` | `decimal(14,2)` | No |  | `0` | Indemnización. |
| `total` | `decimal(14,2)` | No |  |  | Total. |
| `estado` | `varchar(3)` | No |  | `BOR` | Estado. Valores: `BOR` Borrador, `APR` Aprobada. |
| `observaciones` | `longtext` | No |  |  | Observaciones. |
| `elaborado_por_id` | `integer` | Sí | FK → `auth_user` |  | Elaborado por. |
| `fecha_elaboracion` | `datetime(6)` | No |  | fecha actual | Fecha de elaboración. |

**Restricciones**

- `contrato_id` → `contrato.id` (índice y llave foránea). Al eliminar el registro padre: se impide si existen registros relacionados.
- `elaborado_por_id` → `auth_user.id` (índice y llave foránea). Al eliminar el registro padre: la columna queda en NULL.
