# Diagrama entidad-relación

> Archivo generado con `python manage.py documentar_bd`. No lo edite a mano.

Notación: `PK` llave primaria, `FK` llave foránea, `UK` valor único. 
Las relaciones usan la notación *pata de gallo*: `||--o{` significa *uno a muchos*, 
`||--o|` *uno a cero o uno*.

## Módulo Configuración general

```mermaid
erDiagram
    EMPRESA {
        bigint id PK
        varchar razon_social
        varchar nit
        varchar direccion
        varchar ciudad
        varchar telefono
        varchar correo
        varchar representante_legal
        varchar actividad_economica
        tinyint exonerada_aportes
    }
    PARAMETRO_LEGAL {
        bigint id PK
        date vigente_desde UK
        varchar descripcion
        decimal smmlv
        decimal auxilio_transporte
        decimal uvt
        smallint horas_mes
        decimal pct_recargo_nocturno
        decimal pct_recargo_dominical
        decimal pct_extra_diurna
        decimal pct_extra_nocturna
        decimal pct_salud_empleado
        decimal pct_pension_empleado
        decimal pct_salud_empleador
        decimal pct_pension_empleador
        decimal pct_caja
        decimal pct_icbf
        decimal pct_sena
    }
    ENTIDAD {
        bigint id PK
        varchar tipo
        varchar nombre
        varchar nit
        varchar codigo
        tinyint activa
    }
    AUDITORIA {
        bigint id PK
        datetime fecha
        integer usuario_id FK
        varchar accion
        varchar objeto
        longtext detalle
    }
    AUTH_USER {
        bigint id PK
    }
    AUTH_USER |o--o{ AUDITORIA : "usuario"
```

## Módulo Personal

```mermaid
erDiagram
    CENTRO_COSTO {
        bigint id PK
        varchar codigo UK
        varchar nombre
        tinyint activo
    }
    AREA {
        bigint id PK
        varchar codigo UK
        varchar nombre
        bigint centro_costo_id FK
    }
    CARGO {
        bigint id PK
        varchar codigo UK
        varchar nombre
        bigint area_id FK
        decimal salario_referencia
    }
    EMPLEADO {
        bigint id PK
        varchar tipo_documento
        varchar numero_documento UK
        varchar nombres
        varchar apellidos
        date fecha_nacimiento
        varchar genero
        varchar correo
        varchar telefono
        varchar direccion
        varchar ciudad
        bigint banco_id FK
        varchar tipo_cuenta
        varchar numero_cuenta
        bigint eps_id FK
        bigint afp_id FK
        bigint fondo_cesantias_id FK
        bigint caja_id FK
        tinyint activo
        datetime creado
        datetime actualizado
    }
    CONTRATO {
        bigint id PK
        varchar numero UK
        bigint empleado_id FK
        varchar tipo
        varchar tipo_salario
        decimal salario
        bigint cargo_id FK
        bigint centro_costo_id FK
        varchar periodicidad
        smallint clase_riesgo
        bigint arl_id FK
        date fecha_inicio
        date fecha_fin
        varchar estado
        date fecha_terminacion
        varchar motivo_terminacion
    }
    ENTIDAD {
        bigint id PK
    }
    CENTRO_COSTO ||--o{ AREA : "centro_costo"
    AREA ||--o{ CARGO : "area"
    ENTIDAD |o--o{ EMPLEADO : "banco"
    ENTIDAD ||--o{ EMPLEADO : "eps"
    ENTIDAD |o--o{ EMPLEADO : "afp"
    ENTIDAD |o--o{ EMPLEADO : "fondo_cesantias"
    ENTIDAD ||--o{ EMPLEADO : "caja"
    EMPLEADO ||--o{ CONTRATO : "empleado"
    CARGO ||--o{ CONTRATO : "cargo"
    CENTRO_COSTO ||--o{ CONTRATO : "centro_costo"
    ENTIDAD ||--o{ CONTRATO : "arl"
```

## Módulo Nómina

```mermaid
erDiagram
    CONCEPTO {
        bigint id PK
        varchar codigo UK
        varchar nombre
        varchar tipo
        varchar captura
        tinyint salarial
        tinyint base_seguridad_social
        tinyint base_prestaciones
        tinyint base_vacaciones
        smallint orden
        varchar descripcion
        tinyint activo
    }
    PERIODO_NOMINA {
        bigint id PK
        varchar periodicidad
        smallint anio
        smallint mes
        smallint numero
        date fecha_inicio
        date fecha_fin
        date fecha_pago
        varchar estado
        longtext observaciones
        integer liquidado_por_id FK
        datetime fecha_liquidacion
        integer cerrado_por_id FK
        datetime fecha_cierre
    }
    NOVEDAD {
        bigint id PK
        bigint contrato_id FK
        bigint concepto_id FK
        date fecha_inicio
        date fecha_fin
        decimal cantidad
        decimal valor
        varchar observacion
        varchar estado
        bigint periodo_aplicacion_id FK
        integer registrado_por_id FK
        datetime creado
    }
    PRESTAMO {
        bigint id PK
        bigint contrato_id FK
        bigint concepto_id FK
        varchar descripcion
        date fecha
        decimal monto
        smallint numero_cuotas
        decimal valor_cuota
        decimal saldo
        varchar estado
        datetime creado
    }
    LIQUIDACION_NOMINA {
        bigint id PK
        bigint periodo_id FK
        bigint contrato_id FK
        decimal salario
        smallint dias_periodo
        smallint dias_trabajados
        decimal ibc
        decimal base_prestaciones
        decimal total_devengado
        decimal total_deducciones
        decimal neto_pagar
        decimal total_aportes
        decimal total_provisiones
        longtext advertencias
        datetime creado
    }
    DETALLE_LIQUIDACION {
        bigint id PK
        bigint liquidacion_id FK
        bigint concepto_id FK
        decimal cantidad
        decimal base
        decimal tasa
        decimal valor
        bigint novedad_id FK
        bigint prestamo_id FK
    }
    LIQUIDACION_CONTRATO {
        bigint id PK
        bigint contrato_id FK,UK
        date fecha_retiro
        varchar causa
        decimal salario
        decimal auxilio_transporte
        decimal promedio_variable
        integer dias_cesantias
        decimal base_cesantias
        decimal cesantias
        decimal intereses_cesantias
        integer dias_prima
        decimal prima
        decimal dias_vacaciones
        decimal vacaciones
        decimal indemnizacion
        decimal total
        varchar estado
        longtext observaciones
        integer elaborado_por_id FK
        datetime fecha_elaboracion
    }
    AUTH_USER {
        bigint id PK
    }
    CONTRATO {
        bigint id PK
    }
    AUTH_USER |o--o{ PERIODO_NOMINA : "liquidado_por"
    AUTH_USER |o--o{ PERIODO_NOMINA : "cerrado_por"
    CONTRATO ||--o{ NOVEDAD : "contrato"
    CONCEPTO ||--o{ NOVEDAD : "concepto"
    PERIODO_NOMINA |o--o{ NOVEDAD : "periodo_aplicacion"
    AUTH_USER |o--o{ NOVEDAD : "registrado_por"
    CONTRATO ||--o{ PRESTAMO : "contrato"
    CONCEPTO ||--o{ PRESTAMO : "concepto"
    PERIODO_NOMINA ||--o{ LIQUIDACION_NOMINA : "periodo"
    CONTRATO ||--o{ LIQUIDACION_NOMINA : "contrato"
    LIQUIDACION_NOMINA ||--o{ DETALLE_LIQUIDACION : "liquidacion"
    CONCEPTO ||--o{ DETALLE_LIQUIDACION : "concepto"
    NOVEDAD |o--o{ DETALLE_LIQUIDACION : "novedad"
    PRESTAMO |o--o{ DETALLE_LIQUIDACION : "prestamo"
    CONTRATO ||--o| LIQUIDACION_CONTRATO : "contrato"
    AUTH_USER |o--o{ LIQUIDACION_CONTRATO : "elaborado_por"
```

## Vista general de relaciones

```mermaid
erDiagram
    CENTRO_COSTO ||--o{ AREA : ""
    AREA ||--o{ CARGO : ""
    ENTIDAD ||--o{ EMPLEADO : ""
    EMPLEADO ||--o{ CONTRATO : ""
    CARGO ||--o{ CONTRATO : ""
    CENTRO_COSTO ||--o{ CONTRATO : ""
    ENTIDAD ||--o{ CONTRATO : ""
    CONTRATO ||--o{ NOVEDAD : ""
    CONCEPTO ||--o{ NOVEDAD : ""
    PERIODO_NOMINA ||--o{ NOVEDAD : ""
    CONTRATO ||--o{ PRESTAMO : ""
    CONCEPTO ||--o{ PRESTAMO : ""
    PERIODO_NOMINA ||--o{ LIQUIDACION_NOMINA : ""
    CONTRATO ||--o{ LIQUIDACION_NOMINA : ""
    LIQUIDACION_NOMINA ||--o{ DETALLE_LIQUIDACION : ""
    CONCEPTO ||--o{ DETALLE_LIQUIDACION : ""
    NOVEDAD ||--o{ DETALLE_LIQUIDACION : ""
    PRESTAMO ||--o{ DETALLE_LIQUIDACION : ""
    CONTRATO ||--o| LIQUIDACION_CONTRATO : ""
```
