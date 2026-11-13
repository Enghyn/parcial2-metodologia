# audit-log Specification

## Purpose
TBD - created by archiving change c-20-auditoria-export. Update Purpose after archive.

## Requirements

### Requirement: Tabla auditorias

El sistema SHALL crear mediante la migración `0016_auditoria` (encadenada a `0015_cierres_estado_varchar`, reversible con `downgrade`) la tabla `auditorias`, sin `tenant_id` (R2).

#### Scenario: Fila de auditoría creada
- **WHEN** se aplica la migración y se inserta una fila válida
- **THEN** `auditorias` acepta la fila y `fecha` se completa por default

#### Scenario: Downgrade sin objetos huérfanos
- **WHEN** se ejecuta `alembic downgrade` hasta `0015_cierres_estado_varchar`
- **THEN** `auditorias` no existe y no quedan índices ni constraints huérfanos

### Requirement: Columnas y constraints de auditorias

`auditorias` SHALL tener: `id` (UUID PK), `fecha` (timestamp, server_default now, no nulo), `usuario_id` (UUID FK opcional a `usuarios`, ON DELETE SET NULL), `accion` (varchar(40), no nulo), `recurso` (varchar(60), no nulo), `recurso_id` (UUID nullable), `diff` (JSONB nullable, ya enmascarado), `ip` (varchar(45) nullable) y `user_agent` (varchar(255) nullable). `accion` y `recurso` tendrán CHECK sobre catálogos controlados. Índices: `fecha`, `(recurso, recurso_id)`, `usuario_id`.

#### Scenario: Acción fuera del catálogo
- **WHEN** se intenta persistir `accion = 'borrar'`
- **THEN** la base rechaza la operación por violación del CHECK `accion`

#### Scenario: Recurso fuera del catálogo
- **WHEN** se intenta persistir `recurso = 'foo'`
- **THEN** la base rechaza la operación por violación del CHECK `recurso`

### Requirement: Registro de auditoría atómico

El sistema SHALL registrar una fila en `auditorias` por cada escritura sensible de turnos, caja (movimientos, cierres, ajustes), presupuestos y odontograma (hallazgos), en la **misma transacción** que la escritura auditada. Si la escritura de auditoría falla, la transacción completa se revierte (no se persiste la escritura de negocio sin su auditoría).

#### Scenario: Crear turno genera auditoría
- **WHEN** se crea un turno exitosamente
- **THEN** existe una fila en `auditorias` con `accion = crear`, `recurso = turno`, `recurso_id` igual al turno creado y `usuario_id` del JWT

#### Scenario: Fallo de auditoría revierte la escritura
- **WHEN** la inserción de la fila de auditoría falla (por ejemplo, CHECK violado)
- **THEN** la escritura de negocio no se persiste y se devuelve error 500

### Requirement: Enmascarado de datos sensibles

El sistema SHALL enmascarar los valores de campos sensibles (salud y PII: motivos clínicos, observaciones, diagnósticos, documentos, notas, y cualquier campo listado en la lista de denegación) **antes de persistir** el `diff` en `auditorias`, y SHALL re-aplicar el enmascarado al exportar. El `diff` persistido nunca contendrá valores sensibles en claro.

#### Scenario: Diff enmascarado al crear
- **WHEN** se crea un hallazgo con observación clínica
- **THEN** la fila de auditoría guarda la observación como `[REDACTED]` (o equivalente) en el `diff`

#### Scenario: Export no filtra datos sensibles
- **WHEN** se exporta auditoría a CSV
- **THEN** ninguna columna contiene valores de los campos enmascarados

### Requirement: Visor paginado

El sistema SHALL exponer `GET /api/v1/auditoria` (solo `admin`) con paginación (`page`, `size`) y filtros por `fecha_desde`, `fecha_hasta`, `recurso`, `accion`, `usuario_id`. Los filtros SHALL usar únicamente datos no sensibles (R9: ningún dato de salud ni texto libre en parámetros de URL).

#### Scenario: Paginación por defecto
- **WHEN** se consulta sin parámetros
- **THEN** se devuelven los registros más recientes primero, con `page=1` y `size` por defecto (≤ 50)

#### Scenario: Filtro por recurso
- **WHEN** se consulta con `recurso=turno`
- **THEN** solo se devuelven filas con `recurso = turno`

### Requirement: Export CSV

El sistema SHALL exponer `GET /api/v1/auditoria/export` (solo `admin`) que devuelve un CSV con los mismos filtros del visor, con `Content-Type: text/csv` y `Content-Disposition: attachment`, enmascarado, con un tope de filas por export.

#### Scenario: Export exitoso
- **WHEN** un admin solicita export con filtros válidos
- **THEN** la respuesta es un CSV descargable con cabecera y filas enmascaradas

#### Scenario: Export sin permiso
- **WHEN** un usuario no admin solicita export
- **THEN** se responde 403

### Requirement: RBAC de auditoría

El sistema SHALL aplicar el RBAC en backend: solo `admin` puede consultar y exportar auditoría; `recepcion` y `odontologo` reciben 403. La UI solo oculta/deshabilita cosméticamente (R8).

#### Scenario: No admin recibe 403
- **WHEN** `recepcion` o `odontologo` consulta `/api/v1/auditoria`
- **THEN** se responde 403
