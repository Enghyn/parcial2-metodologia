# Tasks — C-12 caja-cierre-cuenta-corriente

> **TDD estricto.** Backend desde `backend/`; integración con PostgreSQL migrado y sembrado (`alembic upgrade head`, `python -m app.db.seed`). Frente desde `frontend/`. Regla dura R11: sin commit sin pedido explícito. Gobernanza CRÍTICO: apply solo con aprobación humana.

## 0. Safety net (línea base)

- [ ] 0.1 Ejecutar `python -m pytest -m "not integration" -q` desde `backend/` y registrar la línea base (tests pasando antes de tocar nada).
- [ ] 0.2 Ejecutar `python -m pytest -q` con PostgreSQL migrada y sembrada; registrar línea base de integración.
- [ ] 0.3 Cualquier falla preexistente se reporta como "pre-existing failure" y no se corrige en este change.

## 1. Migración y modelos de base (0008)

- [ ] 1.1 **RED**: crear `test_caja_cierre_models.py` con tests que fallen: tablas `cierres_caja`, `cuentas_corrientes_paciente`, `ajustes_caja` existen; `fecha_dia` UNIQUE; `ajustes_caja` bloquea UPDATE/DELETE por trigger; sin `tenant_id`.
- [ ] 1.2 **GREEN**: escribir migración `0008_caja_cierre_cuenta_corriente.py` (`upgrade`/`downgrade`) y modelos SQLAlchemy `CierreCaja`, `CuentaCorrientePaciente`, `AjusteCaja` en `modules/caja/models.py`; verificar verde.
- [ ] 1.3 **TRIANGULATE**: agregar tests de check constraint `estado` en (`pendiente`, `cerrado`, `reabierto`) y FK de `ajustes_caja` a `movimientos_caja` (ambos lados); verificar.
- [ ] 1.4 **REFACTOR**: reusar convenciones de nombres de constraint (`NAMING_CONVENTION`) y `ImmutableLedgerMixin`-style triggers para `ajustes_caja`; correr `ruff`.

## 2. Schemas de cierre, cuenta corriente, ajuste y export

- [ ] 2.1 **RED**: crear `test_caja_cierre_schemas.py` con tests que fallen: `CierreCreate`/`CierreOut` con `extra="forbid"` (R1), `estado` Literal, `AjusteCreate` con motivo no vacío y `usuario_aprobador_id` rechazado en body (sale del JWT), `CuentaCorrienteOut` con `saldo` y `detalle`.
- [ ] 2.2 **GREEN**: implementar en `modules/caja/schemas.py`: `CierreCreate`, `CierreOut`, `CuentaCorrienteOut`, `MovimientoCuentaCorriente`, `AjusteCreate`, `AjusteOut`; verificar verde.
- [ ] 2.3 **TRIANGULATE**: agregar caso de `monto` negativo rechazado y `concepto` vacío rechazado en ajuste; verificar.

## 3. Servicio de cierre, cuenta corriente y ajuste

- [ ] 3.1 **RED**: crear `test_caja_cierre_service.py` con tests que fallen: cerrar día (201 con balance y aprobador), día ya cerrado (409), `registrar` rechaza movimiento en día cerrado (409), saldo derivado de cuenta corriente, paciente sin movimientos (saldo 0), paciente dado de baja (404), ajuste aprobado por admin crea contra-asiento + fila en `ajustes_caja`, recepción no puede ajustar (403).
- [ ] 3.2 **GREEN**: implementar en `modules/caja/service.py`: `CierreService.cerrar`, `CajaService.registrar` (bloqueo día cerrado), `CuentaCorrienteService.saldo/detalle`, `AjusteService.registrar`; verificar verde.
- [ ] 3.3 **TRIANGULATE**: agregar cierre de día sin movimientos (balance cero) y ajuste con motivo largo/límite; verificar.
- [ ] 3.4 **REFACTOR**: reusar `inicio_dia`/`fin_dia`/`ahora` de `core/timezone` y `require_role`; correr `ruff`.

## 4. Router y montaje de cierre, cuenta corriente, ajuste, export

- [ ] 4.1 **RED**: crear `test_caja_cierre_router.py` y `test_caja_export_csv.py` con tests que fallen: 401 sin token, 403 odontólogo, 201 cierre admin, 403 cierre recepción, 409 día cerrado, 409 doble cierre, 200 cuenta corriente, 404 paciente baja, 201 ajuste admin, 403 ajuste recepción, export CSV `text/csv` con columnas y totales, export sin datos clínicos.
- [ ] 4.2 **GREEN**: implementar en `modules/caja/router.py` las rutas `POST/GET /cierres`, `GET /cuenta-corriente/{pacienteId}`, `GET /cuentas-corrientes`, `POST /ajustes`, `GET /export`; verificar verde.
- [ ] 4.3 Modificar `registrar` (movimientos) para consultar `cierres_caja` y devolver 409 si el día está cerrado; verificar que no se rompen tests de C-08.
- [ ] 4.4 Verificar que no existen `PATCH`/`DELETE` sobre movimientos ni cierres (append-only).
- [ ] 4.5 Actualizar `test_structure.py` si fuera necesario (caja ya está en `MODULOS_SIN_STUBS`/`MODULOS_CON_RUTAS`/`MODULOS_CON_MODELOS`).

## 5. Frontend: cierre y cuenta corriente

- [ ] 5.1 Extender `shared/api/caja.ts`: `cerrarCaja`, `listarCierres`, `cuentaCorriente`, `cuentasCorrientes`, `registrarAjuste`, `exportCajaCsv` (tipado, sin `any`).
- [ ] 5.2 Crear `features/caja/CierreCajaPage.tsx`: cerrar día (admin), lista de cierres con estado/balance, export CSV del cierre.
- [ ] 5.3 Crear `features/caja/CuentaCorrientePage.tsx`: buscador de paciente, saldo y detalle, lista de saldos pendientes.
- [ ] 5.4 Actualizar `features/caja/index.ts`, `app/router.tsx` y `app/layout.tsx` (rutas y links).
- [ ] 5.5 Verificar `npm test`, `npm run lint`, `npx tsc --noEmit` y `npm run build`.

## 6. Verificación y cobertura de reglas

- [ ] 6.1 Correr `python -m pytest -q` con PostgreSQL dos veces; confirmar que no queda data sucia.
- [ ] 6.2 Correr `ruff check src test` en cero.
- [ ] 6.3 Ejecutar `openspec validate "c-12-caja-cierre-cuenta-corriente"` y `openspec validate --all`; sin errores.
- [ ] 6.4 Pasar `business-rule-coverage-auditor` sobre C-12 (RN-CJ-01/02/03, R1–R13) y dejar la matriz de cobertura; cerrar gaps o documentar abiertos.

## Workflow follow-up

- Revisión humana de `design.md` (decisiones D1-D8) antes de apply — gobernanza CRÍTICO.
- Aplicar con TDD y actualizar checkboxes.
- Archivar con `openspec archive "c-12-caja-cierre-cuenta-corriente" -y` (solo con aprobación).
- Marcar C-12 `[x]` en `CHANGES.md` y `AGENTS.md` tras archivar.
