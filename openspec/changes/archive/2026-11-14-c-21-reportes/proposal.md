# Proposal — C-21 reportes

## Why

El consultorio opera con agenda multi-sillón, caja append-only y cuenta corriente, pero carece de vistas de gestión que crucen los datos operativos: no sabe cuánto se ocupa cada sillón o profesional, cuánto factura por medio de pago u obra social, ni qué tanto se recupera de los turnos no asistidos. Sin reportes, el administrador supervisa la ocupación y la caja a mano (KB 01/03). C-21 cierra el MVP expandido con consultas de solo lectura sobre Turno, MovimientoCaja, Sillon, Profesional, Paciente y obras sociales.

## What Changes

- **Ocupación por sillón y profesional**: se agrega `GET /api/v1/reportes/ocupacion` que, por rango de fechas, devuelve turnos atendidos vs reservados, horas bloqueadas y tasa de ocupación por sillón y por profesional (sobre Turno + Sillon + Profesional).
- **Facturación por medio de pago y OS**: se agrega `GET /api/v1/reportes/facturacion` que devuelve ingresos agrupados por `medio_pago` y, cuando hay afiliación/convenio, desglose por obra social (sobre MovimientoCaja + Paciente + OS).
- **Ausentismo y recuperación**: se agrega `GET /api/v1/reportes/ausentismo` que devuelve turnos cancelados / no presentados vs turnos recuperados (reagendados) por rango.
- **Filtros de rango de fechas**: todos los endpoints aceptan `desde` y `hasta` (día calendario ART, default 30 días), validados `desde <= hasta`.
- **Export CSV es-AR por reporte**: cada reporte tiene variante `.../export.csv` con BOM UTF-8, separador `;`, decimales con coma, fechas `dd/mm/aaaa`, `Content-Disposition: attachment`; sin DNI ni datos clínicos (R9).
- **Sin migración**: consultas de solo lectura sobre tablas existentes (C-02, C-04, C-08, C-12, C-13a); ninguna tabla nueva.
- **RBAC de reportes**: `admin` y `recepcion` leen todos los reportes; `odontologo` tiene lectura limitada a sus propios turnos/ocupación (403 sobre los demás); sin token 401 (R8).
- **Páginas de reportes en el frontend**: páginas `/app/reportes/*` con filtros de rango, tablas de resumen y botones de export CSV.

## Capabilities

### New Capabilities

- `reports`: reportes de gestión de solo lectura (ocupación, facturación, ausentismo) con filtros de rango y export CSV es-AR, sobre tablas existentes de turno, caja y obras sociales. Crea `openspec/specs/reports/spec.md`.

### Modified Capabilities

- (ninguna): C-21 solo lee de `cash-ledger`, `agenda`, `insurance-coverage` y `core-data-model` sin modificar sus requisitos.

## Impact

- **Backend**: `modules/reportes/{schemas,service,router}.py` (endpoints de solo lectura), `api/v1/router.py` (montar rutas), tests `test_reportes_*.py`.
- **Base de datos**: ninguna migración (R5 no aplica a schema; solo consultas sobre tablas existentes). Sin `tenant_id` (R2).
- **Frontend**: `shared/api/reportes.ts`, `features/reportes/*`, `app/router.tsx`.
- **Contratos existentes**: sin cambios; solo agrega endpoints.
- **Documentación**: `CHANGES.md` marca C-21 `[ ]` hasta archivar; `AGENTS.md` no requiere cambios de reglas duras.
- **Fuera de alcance**: export masivo multi-día, programación de envíos por email, dashboards en tiempo real, integración con ARCA/Mercado Pago.
- **Coordinación**: consume C-09a (agenda avanzada), C-12 (cierre/cuenta corriente), C-13a (OS/nomenclador), C-16 (presupuestos), C-17 (pagos simulados).
- **Brechas de KB detectadas**: `US-041` citado en `CHANGES.md` (leer antes KB 06) NO existe en `knowledge-base/06_funcionalidades.md` (solo US-001 a US-011). No se inventa; se registra como pregunta abierta en `design.md`.
