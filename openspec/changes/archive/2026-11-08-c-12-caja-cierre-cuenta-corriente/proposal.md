# Proposal — C-12 caja-cierre-cuenta-corriente

## Why

C-08 dejó el libro append-only (`movimientos_caja`) con registro de ingresos/egresos, validación de turno y resumen diario, pero el día nunca se "cierra": un recepcionista o administrador puede seguir creando movimientos de ayer, no hay quien apruebe el arqueo, no existe cuenta corriente por paciente con saldo derivado, no hay ajustes auditados y no hay export CSV del libro ni del cierre. C-13a (OS/nomenclador), C-13b (comprobante), C-16 (presupuestos), C-17 (pagos), C-20 (auditoría/export) y C-21 (reportes) dependen de C-12 (árbol de dependencias de CHANGES.md): necesitan un período cerrado, saldos de pacientes confiables y trazabilidad de ajustes. Sin cierre, el libro queda abierto a cambios retroactivos y las cuentas corrientes no son auditable.

## What Changes

- **Cierre diario**: `POST /api/v1/caja/cierres` (solo `admin`) crea el cierre del día calendario ART con el balance calculado del libro y lo aprueba; `GET /api/v1/caja/cierres` consulta cierres. Un día cerrado bloquea creación de movimientos con fecha de ese día (bloqueo de período).
- **Cuenta corriente por paciente**: `GET /api/v1/caja/cuenta-corriente/{pacienteId}` devuelve el saldo derivado (suma de movimientos vinculados a turnos del paciente) y el detalle de movimientos; `GET /api/v1/caja/cuentas-corrientes` lista saldos de pacientes con saldo distinto de cero.
- **Ajustes auditados**: las correcciones siguen siendo contra-asientos (fila nueva, nunca UPDATE/DELETE del libro). Se agrega `AjusteCaja` que vincula el contra-asiento al movimiento corregido, registra motivo, fecha y usuario aprobador (`admin`). Nunca se toca el movimiento original.
- **Export CSV**: `GET /api/v1/caja/export?fecha=YYYY-MM-DD` (y opcionalmente para cierre) devuelve CSV del libro del día/cierre (UTF-8, ARS, columnas de MovimientoCaja + usuario). No incluye datos clínicos (R9).
- **Migración `0008_caja_cierre_cuenta_corriente`**: tablas `cierres_caja`, `cuentas_corrientes_paciente` (vista o tabla derivada) y `ajustes_caja`; reversible con `downgrade`. Última migración aplicada es `0007_ficha_clinica_avanzada`, por tanto `0008` es la siguiente.
- **Frontend**: página `/app/caja/cierre` (cierre diario, aprobación, bloqueo de período, export CSV) y `/app/caja/cuenta-corriente` (saldo y detalle por paciente).
- **Tests**: schemas, servicio (cierre, bloqueo, saldo derivado, ajuste), router (401/403/422/409 bloqueo), export CSV, frontend (tsc/eslint/build).

## Capabilities

### New Capabilities

- Ninguna. `cierre-cuenta-corriente` sería una near-duplicate de `cash-ledger` (mismo libro, mismas guardas, mismo dominio de caja). Todo el alcance se modela como requisitos adicionales sobre la capability existente `cash-ledger` y sobre `core-data-model` (persistencia/migración), siguiendo el criterio de C-11 (no separar consentimiento en capacidad propia).

### Modified Capabilities

- `cash-ledger`: se agregan requisitos de cierre diario aprobado por `admin`, bloqueo de período (rechazo de movimientos en día cerrado), cuenta corriente por paciente con saldo derivado, ajustes auditados (`AjusteCaja`), export CSV del libro y del cierre, y la migración `0008`.
- `core-data-model`: se agregan requisitos de persistencia para `cierres_caja`, `cuentas_corrientes_paciente` y `ajustes_caja`, la migración reversible `0008_caja_cierre_cuenta_corriente`, y la restricción de que un día cerrado no admita nuevos movimientos.

## Impact

- **Backend**: `modules/caja/{models,schemas,service,router}.py` (nuevos modelos/schemas/endpoints de cierre, cuenta corriente, ajuste, export); `db/migrations/versions/0008_caja_cierre_cuenta_corriente.py`; `api/v1/router.py` (ya monta caja; solo agregar rutas si el prefijo cambia, no se espera); `test/test_structure.py` (caja ya está listado); tests nuevos `test_caja_cierre_*.py`, `test_caja_cuenta_corriente_*.py`, `test_caja_export_csv.py`.
- **Base de datos**: tres tablas nuevas (`cierres_caja`, `cuentas_corrientes_paciente`, `ajustes_caja`), índices, check constraints y FKs. Sin `tenant_id` (R2). Migración reversible.
- **Frontend**: `shared/api/caja.ts` (agregar `cerrarCaja`, `listarCierres`, `cuentaCorriente`, `exportCajaCsv`), `features/caja/CierreCajaPage.tsx`, `features/caja/CuentaCorrientePage.tsx`, `app/router.tsx`, `app/layout.tsx`.
- **Contratos existentes**: `POST /caja/movimientos` se modifica para rechazar movimientos en día cerrado (409). El resto de endpoints de C-08 se mantienen sin cambios.
- **Documentación**: `CHANGES.md` mantiene C-12 `[ ]` hasta archivar; `AGENTS.md` no requiere cambios de reglas duras (se aplican las existentes).
- **Fuera de alcance**: conciliación bancaria, clave de idempotencia para doble submit, anulación con columna dedicada (se usa contra-asiento), integración con ARCA/Mercado Pago, cierre multi-sede (mono-consultorio, R2), export masivo de múltiples días.
- **Gobernanza CRÍTICO**: este propose es solo análisis. La implementación requiere aprobación humana explícita antes de `/opsx:apply`.
