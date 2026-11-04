# Proposal — C-08 caja-movimientos-balance

## Why

C-02 dejó el modelo `MovimientoCaja` append-only, con constraints y guardas ORM/triggers, pero no hay endpoints ni pantalla para cobrar, registrar egresos o cerrar el día. C-08 cierra el MVP académico con el libro de caja y el resumen diario, sin tocar el modelo ni agregar migraciones.

## What Changes

- **Registro**: `POST /api/v1/caja/movimientos` para ingresos y egresos, con `tipo`, `medio_pago`, `monto > 0`, `concepto` y `turno_id` opcional. El `usuario_id` sale del JWT, nunca del body (R4).
- **Validación de turno**: si se vincula `turno_id`, el turno debe existir y tener `deleted_at IS NULL`; si no, 404 y no se persiste el movimiento.
- **Listado**: `GET /api/v1/caja/movimientos?fecha=YYYY-MM-DD`, ordenado por fecha descendente, para `admin` y `recepcion`.
- **Resumen**: `GET /api/v1/caja/resumen-diario?fecha=YYYY-MM-DD`, con totales por medio de pago, total de ingresos/egresos y balance neto.
- **Inmutabilidad**: sin `PATCH`/`DELETE`; una corrección es un movimiento inverso (contra-asiento), nunca un update.
- **Seña**: se registra manualmente como ingreso vinculado al turno cuando se cobra; `Turno.sena_monto` es solo una sugerencia y la UI muestra un aviso de “seña pendiente”, no genera un movimiento automático al reservar.
- **Frontend**: `/app/caja` con formulario de ingreso/egreso, selector de turno, tabla del libro diario y tarjetas de balance en ARS.

## Capabilities

### New Capabilities

- `cash-ledger`: libro append-only de movimientos, validación de turno, resumen diario y reglas de acceso.

### Modified Capabilities

- Ninguna. `core-data-model` ya define el modelo y sus guardas.

## Impact

- **Backend**: `modules/caja/{schemas,service,router}.py`, `api/v1/router.py`, `test/test_structure.py`.
- **Frontend**: `shared/api/caja.ts`, `features/caja/*`, `app/{router,layout}.tsx`.
- **Tests**: nuevos `test_caja_schemas.py`, `test_caja_service.py` y `test_caja_router.py` (integración con PostgreSQL).
- **Sin migración**: la tabla, constraints y triggers ya existen.
- **Fuera de alcance**: conciliación con Mercado Pago, exportación CSV, bloqueo de período y vínculo explícito `contra_asiento_de` (se usa concepto).
