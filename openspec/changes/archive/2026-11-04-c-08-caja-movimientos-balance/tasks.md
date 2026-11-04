# Tasks — C-08 caja-movimientos-balance

> **TDD estricto.** Backend desde `backend/`; integración con PostgreSQL migrado y sembrado.

## 1. Safety net

- [x] 1.1 Correr `pytest -m "not integration" -q` y `pytest -q` con base; registrar la línea base (esperado: 168/8/79 y 248/7).
- [x] 1.2 Releer `test_caja_inmutable.py` y los triggers de `0003`; no modificar el modelo ni las guardas.

## 2. Schemas

- [x] 2.1 **RED**: crear `test_caja_schemas.py` con tests que fallen: `extra="forbid"`, `tipo`/`medio_pago` Literal, `monto > 0`, `concepto` no vacío, `usuario_id` rechazado, `turno_id` opcional.
- [x] 2.2 **GREEN**: implementar `modules/caja/schemas.py`; verificar verde.
- [x] 2.3 **TRIANGULATE**: agregar montos con dos decimales y concepto en el límite; verificar.

## 3. Servicio

- [x] 3.1 **RED**: crear `test_caja_service.py` con casos que fallen: registrar ingreso/egreso con usuario, turno borrado 404, listado por fecha ART, resumen con ingresos/egresos y resumen vacío en cero.
- [x] 3.2 **GREEN**: implementar `CajaService` en `modules/caja/service.py`; no exponer update/delete; verificar.
- [x] 3.3 **TRIANGULATE**: agregar contra-asiento (dos filas, signo opuesto), filtro por día ART y totales por medio; verificar.
- [x] 3.4 **REFACTOR**: reusar `inicio_dia`/`fin_dia` y `ahora` de `core/timezone`; correr `ruff`.

## 4. Router y montaje

- [x] 4.1 **RED**: crear `test_caja_router.py` con 401 sin token, 403 odontólogo, 201 ingreso, 422 monto/body, 404 turno borrado, listado y resumen.
- [x] 4.2 **GREEN**: implementar `modules/caja/router.py` con `prefix="/caja"` y `require_role("admin","recepcion")`; montar en `api/v1/router.py`.
- [x] 4.3 Actualizar `test_structure.py`: `caja` en `MODULOS_SIN_STUBS` y `MODULOS_CON_RUTAS`.
- [x] 4.4 Verificar que no existan rutas `PATCH`/`DELETE` de movimientos.

## 5. Frontend

- [x] 5.1 Crear `shared/api/caja.ts` tipado: `crearMovimiento`, `listarMovimientos`, `resumenDiario`.
- [x] 5.2 Crear `features/caja/CajaPage.tsx`: formulario ingreso/egreso, selector de turno del día, tabla y tarjetas (Efectivo, Transferencias, Tarjetas, Total, Egresos, Balance) con `formatArs`; mostrar aviso de “seña pendiente” si el turno tiene `sena_monto > 0` y no hay ingreso de seña vinculado.
- [x] 5.3 Actualizar `features/caja/index.ts`, `app/router.tsx` y `app/layout.tsx` (link Caja).
- [x] 5.4 Verificar `npm test`, `npm run lint`, `npx tsc --noEmit` y `npm run build`.

## 6. Verificación

- [x] 6.1 Correr `pytest -q` con PostgreSQL **dos veces** y confirmar que no queda data sucia.
- [x] 6.2 Correr `ruff check src test` en cero.
- [x] 6.3 Correr `openspec validate "c-08-caja-movimientos-balance" --strict` y `openspec validate --all`.
- [x] 6.4 Pasar `business-rule-coverage-auditor` sobre C-08 (RN-CJ-01/02/03, R3/R4/R8/R9/R13) y actualizar la matriz.

## Workflow follow-up

- Revisión humana de las decisiones de `design.md` (seña manual, contra-asiento sin columna).
- Aplicar con TDD y actualizar checkboxes.
- Archivar con `openspec archive "c-08-caja-movimientos-balance" -y`.
- Marcar C-08 `[x]` en `CHANGES.md` y `AGENTS.md` (cierre del MVP).
