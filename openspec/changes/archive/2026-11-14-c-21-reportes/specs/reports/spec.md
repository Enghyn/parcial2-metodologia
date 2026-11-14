# Spec Delta — reports (C-21)

## ADDED Requirements

### Requirement: Reporte de ocupación por sillón y profesional

El sistema SHALL exponer `GET /api/v1/reportes/ocupacion` para `admin` y `recepcion`, devolviendo por cada sillón y cada profesional: cantidad de turnos `reservado`, `presente`, `atendido`, `cancelado`, tasa de ocupación y horas bloqueadas, agrupados por rango de fechas.

#### Scenario: Ocupación por sillón en rango

- **WHEN** se consulta ocupación con `desde` y `hasta`
- **THEN** la API devuelve una fila por sillón con conteos de turnos por estado y tasa de ocupación

#### Scenario: Ocupación por profesional

- **WHEN** se consulta ocupación filtrando por `profesional_id`
- **THEN** la API devuelve solo las filas de ese profesional

#### Scenario: Rango sin turnos

- **WHEN** el rango no tiene turnos
- **THEN** la API devuelve listas vacías y tasas en cero

### Requirement: Reporte de facturación por medio de pago y obra social

El sistema SHALL exponer `GET /api/v1/reportes/facturacion` para `admin` y `recepcion`, devolviendo ingresos agrupados por `medio_pago` y, cuando el turno del movimiento tenga paciente con afiliación a OS/convenio vigente, desglose por obra social (monto OS y monto paciente).

#### Scenario: Facturación por medio de pago

- **WHEN** se consulta facturación en un rango con ingresos
- **THEN** la API devuelve total por medio (`efectivo`, `transferencia`, `debito`, `credito`, `otro`) y balance neto

#### Scenario: Desglose por obra social

- **WHEN** hay movimientos vinculados a turnos de pacientes afiliados
- **THEN** la API desglosa por OS con monto OS, copago y monto a cargo del paciente

#### Scenario: Paciente sin afiliación

- **WHEN** el movimiento no tiene paciente afiliado
- **THEN** se agrupa bajo "sin OS" y el paciente paga el 100%

### Requirement: Reporte de ausentismo y recuperación

El sistema SHALL exponer `GET /api/v1/reportes/ausentismo` para `admin` y `recepcion`, devolviendo turnos `cancelado` o no presentados, turnos recuperados (reagendados del mismo paciente) y tasa de ausentismo por rango.

#### Scenario: Ausentismo en rango

- **WHEN** se consulta ausentismo con `desde` y `hasta`
- **THEN** la API devuelve cancelados, no presentados, recuperados y tasa de ausentismo

#### Scenario: Sin ausentismo

- **WHEN** todos los turnos del rango fueron atendidos
- **THEN** la tasa de ausentismo es cero

### Requirement: Filtros por rango de fechas

Todos los endpoints de reportes SHALL aceptar `desde` y `hasta` (fechas `YYYY-MM-DD`, día calendario ART). Sin `desde` SHALL usar hoy menos 30 días; sin `hasta` SHALL usar hoy. `desde` posterior a `hasta` SHALL responder 422.

#### Scenario: Rango por defecto

- **WHEN** se consulta sin `desde` ni `hasta`
- **THEN` se usa los últimos 30 días calendario ART

#### Scenario: Desde después de hasta

- **WHEN** `desde` es posterior a `hasta`
- **THEN` la API responde 422

### Requirement: Export CSV es-AR

Cada reporte SHALL tener una variante `.../export.csv` que devuelva `text/csv; charset=utf-8` con BOM UTF-8, separador `;`, decimales con coma, fechas `dd/mm/aaaa` y `Content-Disposition: attachment`. Nunca incluir DNI, diagnósticos, hallazgos ni datos de salud (R9).

#### Scenario: Export de ocupación

- **WHEN** se solicita el CSV de ocupación
- **THEN` la API devuelve el archivo con encabezados y filas de ocupación, sin datos clínicos

### Requirement: RBAC de reportes

El sistema SHALL permitir consulta de todos los reportes a `admin` y `recepcion`; un `odontologo` SHALL recibir 403 sobre reportes globales y solo leer su propia ocupación; una request sin token SHALL recibir 401, independientemente de lo que muestre el frontend (R8).

#### Scenario: Odontólogo en reporte global

- **WHEN** un `odontologo` llama a `GET /reportes/facturacion`
- **THEN` la API responde 403

#### Scenario: Sin token

- **WHEN** se llama a reportes sin token válido
- **THEN` la API responde 401
