# Matriz de trazabilidad — reglas → tests

> Generada con `business-rule-coverage-auditor` el 2026-11-04. Actualizada el 2026-11-12 por la auditoría de C-18 (`c-18-portal-publico`) y el 2026-11-14 por la auditoría de C-21 (`c-21-reportes`).
> Estado: ✅ cubierta · ⚠️ parcial · ❌ sin cobertura · ➖ no aplica.
> Actualizar antes de archivar un change.

| Regla | Evidencia principal | Estado |
|---|---|---|
| RN-AG-01 | `test_agenda_conflicts.py`, `test_agenda_router.py` (409), reprogramación en `test_agenda_service.py`; C-10: `test_pre_reserva_service.py` (conflicto turno/bloqueo), `test_public_reprogramar.py` (409 choque); C-18: ➖ no toca agenda | ✅ |
| RN-AG-02 | `test_agenda_service.py::test_crear_en_hueco_libre_persiste_fin`; C-10: `test_pre_reserva_service.py` (fin = inicio + duracion_min, CHECK fin_coherente); C-18: ➖ | ✅ |
| RN-AG-03 | `test_agenda_schemas.py`, NOT NULL del modelo; C-18: ➖ | ✅ |
| RN-AG-04 | `test_agenda_service.py::test_bloqueo_conflicto_en_turno`; C-18: ➖ | ✅ |
| RN-AG-05 | Catálogo con `ausente`; sin matriz de transiciones; C-18: ➖; C-21: `test_reportes_ocupacion_service.py` cuenta estados `reservado/confirmado/presente/atendido/cancelado` (solo lectura) | ⚠️ |
| RN-AG-06 | `test_public_schemas.py::test_paciente_requiere_nombre_dni_telefono`; C-18: ➖ | ✅ |
| RN-CL-01 | `test_clinica_service.py` (pieza 19), `test_clinica_schemas.py`, CHECK FDI; C-11: `test_clinica_avanzada_models.py` (tablas de C-11 usan los mismos 6 estados de ESTADOS_PIEZA); C-18: ➖ (el portal no expone datos clínicos, R9) | ✅ |
| RN-CL-02 | `test_clinica_router.py::test_recepcion_no_puede_editar_pieza_403`; C-11: `test_clinica_avanzada_router.py` (POST evolución/consentimiento 403 para recepción/admin, 201 para odontólogo; GET 200 para los 3 roles); C-18: ➖ (sin superficies clínicas) | ✅ |
| RN-CJ-01 | `test_caja_router.py` (201/422), `test_caja_schemas.py`, usuario desde JWT; `test_models_structure.py::test_movimientos_caja` (CHECK `monto > 0` + NOT NULL); C-18: `test_confirmar_pago_publico_crea_un_movimiento_y_aprueba` (ingreso, medio válido, usuario), `test_pagos_service.py::test_confirmar_crea_movimiento_con_usuario_y_medio_pago_validos`; **guardado en `portal_service.confirmar_pago_publico`: valida `float(presupuesto.total) <= 0` → 422 "El presupuesto no tiene un monto cobrable", sin crear MovimientoCaja**; C-21: `test_reportes_facturacion_service.py` lee `medio_pago`/`monto` de `MovimientoCaja` sin crear cobros | ✅ |
| RN-CJ-02 | `test_caja_inmutable.py`, `test_pg_hardening.py`, `test_caja_router.py` sin PATCH/DELETE; C-18: el portal solo inserta `MovimientoCaja`, nunca UPDATE/DELETE (`test_confirmar_pago_publico_crea_un_movimiento_y_aprueba`, `test_confirmar_pago_publico_concurrente_un_solo_movimiento`) | ✅ |
| RN-CJ-03 | Seña manual aprobada; no hay deducción de saldo (decisión de C-08); C-18: el portal cobra `presupuesto.total` completo (no una seña parcial) y la UI lo titula "Pagá tu seña" (ambigüedad registrada) | ⚠️ |
| RN-SEG-01 | `test_auth_router.py`, `test_agenda_router.py` (401/403); C-10: `test_public_pre_reserva_router.py` (201 sin auth, 422 campo extra), `test_qr_router.py` (200 SVG, 404 token inexistente); C-11: `test_clinica_avanzada_router.py` (201 sin auth para evolución/consentimiento, 403 recepción/admin, 422 campo extra); C-18: `test_portal_router.py` (200 sin auth, 422 campo extra, 404 genérico) y `test_portal_schemas.py`; C-21: `test_reportes_*_router.py::test_sin_token_401` y `test_reportes_integracion.py` (401 sin token en reportes) | ✅ |
| RN-SEG-02 | `test_soft_delete.py`, 404 de paciente borrado; C-11: `test_clinica_avanzada_models.py` (tablas de C-11 sin `deleted_at`, append-only); `test_clinica_avanzada_service.py` (no hay DELETE físico en evolución/consentimiento/historial); C-18: ➖ (no toca entidades con `deleted_at`) | ✅ |
| RN-G-01 | `frontend/test/whatsapp.test.ts` (constructor de URL); C-18: ➖ (el portal no envía WhatsApp) | ✅ |
| R1 | Tests de schemas auth/agenda/public/clinica; C-10: `test_public_pre_reserva_router.py` (campo extra 422), `test_public_reprogramar.py` (sillon_id 422), `test_qr_router.py` (schemas), `test_pre_reserva_schemas.py`; C-11: `test_clinica_avanzada_schemas.py` (EvolucionCreate/ConsentimientoCreate rechazan campo extra y texto vacío); C-18: `test_portal_schemas.py` (5 schemas rechazan extra), `test_portal_router.py::test_aprobar_campo_extra_422` y `test_rechazar_campo_extra_422`. **Además**, schema `ConfirmarPublicoIn` (C-18) con `extra="forbid"` valida que body con campos no declarados responda 422; C-21: `test_reportes_schemas.py::test_*_extra_forbid` (todos los schemas de reportes rechazan campo extra) | ✅ |
| R2 | `test_models_structure.py::test_ninguna_tabla_tiene_tenant_id`; C-11: `test_clinica_avanzada_models.py::test_ninguna_tabla_nueva_tiene_tenant_id`; C-18: `frontend/test/portalPublico.test.ts` (marca sin `slug`/`tenant`/`sucursal`) y rutas fijas sin segmento de tenant en `app/router.tsx`; C-21: consultas de reportes sin `tenant_id` (mono-consultorio) | ✅ |
| R3 | `test_caja_inmutable.py`, triggers de `0003`, `test_caja_router.py` sin PATCH/DELETE; C-18: `test_confirmar_pago_publico_crea_un_movimiento_y_aprueba` (un ingreso, sin UPDATE/DELETE) + `test_confirmar_pago_publico_concurrente_un_solo_movimiento`; C-21: reportes es solo lectura (ningún WRITE/DELETE en caja) | ✅ |
| R4 | `test_caja_router.py` (usuario JWT, body con `usuario_id` 422); C-18: `test_pagos_service.py::test_confirmar_crea_movimiento_con_usuario_y_medio_pago_validos`, `test_confirmar_exige_usuario_id`; portal `test_confirmar_pago_publico_crea_un_movimiento_y_aprueba` (usuario_id del setting) y `test_confirmar_pago_publico_usuario_portal_inexistente_409` | ✅ |
| R5 | `ruff`, type hints, `test_migration_*`; C-10: `test_migration_0006.py` (pre_reservas, columna origen, CHECKs, índices); C-11: `test_clinica_avanzada_models.py` (migración 0007, tablas y CHECKs); C-18: sin migración (no hay cambio de schema), `test_portal_settings.py`; ruff 0 en archivos de C-18 (los 46 restantes son preexistentes ajenos); C-21: sin cambio de schema → sin migración (`alembic heads` = `0016_auditoria`), type hints y `snake_case` en `modules/reportes`; ruff 0 en archivos de C-21 | ✅ |
| R6 | `test_agenda_conflicts.py`, 409 HTTP, reprogramación con antisolapamiento; C-10: `test_public_reprogramar.py` (409 choque turno/bloqueo/estado, delega en TurnoService); C-11: `test_clinica_avanzada_service.py` (upsert con autoría y historial en misma transacción); C-18: ➖ (no crea ni reprograma turnos) | ✅ |
| R7 | `tsc`, `eslint`, `build`; sin tests de componentes; C-18: `shared/api/public.ts` y componentes tipados sin `any` (PascalCase), `tsc`/lint/build verde; C-21: `shared/api/reportes.ts` y páginas `PascalCase` sin `any`; `tsc`/lint/build verde | ⚠️ |
| R8 | `test_auth_deps.py`, RBAC de agenda/clinica, sobreturno/reprogramación admin/recepción; C-10: `test_qr_router.py` (404 token inexistente), `test_public_reprogramar.py` (404 token inexistente); C-11: `test_clinica_avanzada_router.py` (RBAC por endpoint: odontólogo escribe, los 3 roles leen); C-18: superficies públicas por diseño (RN-SEG-01) y el router interno `/pagos` conserva `require_role` y pasa `usuario.id` del JWT; C-21: `require_role` + `usuario_con_filtro_profesional` (admin/recepción global, odontólogo 403 salvo ocupación propia) | ✅ |
| R9 | `test_login_fallido_no_loguea_credenciales`, `test_crear_turno_no_loguea_notas`, `test_reservar_no_loguea_datos_paciente`, `test_no_loguea_estado_ni_observacion`, `test_no_loguea_concepto_clinico`; C-10: `test_public_pre_reserva_router.py` (respuesta sin dni/telefono/nombre), `test_qr_router.py` (sin red, socket parcheado); C-11: `test_clinica_avanzada_service.py` (3 tests caplog: evolución, consentimiento, upsert); C-18: `test_portal_router.py` (`_assert_sin_ids_ni_pii`, 404 `not_found`), `test_portal_schemas.py` (sin IDs internos), `portalPublico.test.ts` (token solo en path, nunca query). **Falta caplog del portal**; C-21: `test_reportes_export_router.py::test_export_csv_r9_no_datos_clinicos` (CSV sin DNI/clinical; columnas solo ids, conceptos, montos, fechas) | ⚠️ |
| R10 | UI es-AR/ARS; sin test automatizado de textos; C-11: `design.md` §D12 (UI con tokens del design system, textos en es-AR); C-18: `portalPublico.test.ts` (`totalEnArs` es-AR/ARS, estados y mensajes rioplatenses); C-21: CSV es-AR (BOM, `;`, coma decimal, `dd/mm/aaaa`), UI montos en ARS con `formatArs`; sin test de render de componentes | ⚠️ |
| R11 | Regla de proceso; C-18: no se commiteó ni pusheó | ➖ |
| R12 | Regla de proceso | ➖ |
| R13 | `test_soft_delete.py`, triggers, 404 clínico; C-11: `test_clinica_avanzada_models.py` (tablas append-only sin `deleted_at`); `test_clinica_avanzada_service.py` (upsert con historial, no hay borrado físico); triggers de inmutabilidad en migración 0007; C-18: no agrega tablas de negocio ni borra `Paciente`/`Turno`/`Profesional`/`Sillon`; no hay DELETE en el servicio del portal | ✅ |

## Brechas conocidas

- **R7/R10**: no hay tests de componentes React ni E2E; solo `tsc`/`eslint`/`build` y tests de helpers puros.
- **RN-AG-05**: el catálogo está cubierto; las transiciones no se validan (decisión pendiente en KB 10).
- **RN-CJ-03**: la seña se registra manualmente y no hay deducción automática de saldo (decisión aprobada de C-08).
- **R9**: cubierto con `caplog` en auth/agenda/público/clínica/caja; no hay un test global de logging, pero las cinco superficies están cubiertas. **C-18** agrega una sexta superficie (portal de presupuesto/pago) sin test `caplog` → el escenario "Sin datos sensibles en logs" del spec `public-portal` queda sin prueba (ver propuesta).
- **C-18 / RN-CJ-01 (borde `total <= 0`)**: `confirmar_pago_publico` no valida `monto > 0`; un presupuesto `aprobado` con total 0 o negativo intenta insertar `MovimientoCaja(monto<=0)` y viola `CHECK (monto > 0)` sin mapeo → 500. Sin test.
- **C-18 / R1 (`confirmar` sin cuerpo)**: `POST /pagos/{token}/confirmar` no declara schema de entrada; un body con campos extra se ignora en vez de responder 422.
- **C-18 / firma y motivo no persistidos**: `AprobacionPublicaIn.firma` y `RechazoPublicoIn.motivo` se validan pero se descartan (no hay columna en `Presupuesto`); no hay trazabilidad del firmante ni del motivo.
- **C-18 / `public-portal` "Ruta pública desconocida"**: el catch-all de `app/router.tsx` redirige a `/login`; el spec pide una vista "no encontrado" genérica para rutas públicas desconocidas.

## Cómo usarla

1. Antes de archivar un change, buscar las reglas que toca.
2. Verificar que cada ✅ tenga un test concreto ejecutándose.
3. Si una regla queda ⚠️ o ❌, proponer el test o registrar la decisión de dominio.

---

## Auditoría C-18 — Portal público (`c-18-portal-publico`, 2026-11-12)

**Scope:** change `c-18-portal-publico` (superficies y endpoints públicos de presupuesto y pago simulado; sin migración).
**Fuentes leídas:** KB `04`, `05`, `06`, `07`, `10`; `AGENTS.md` (R1–R13); `proposal.md`, `design.md`, `tasks.md`; specs `public-portal`, `budgets`, `simulated-payments`; `backend/src/app/modules/public/{portal_service,schemas,router}.py`, `core/config.py`, `modules/pagos/{service,router}.py`; tests `test_portal_{schemas,settings,service,router}.py`, `test_pagos_service.py`; frontend `features/portal-publico/*`, `shared/api/public.ts`, `test/portalPublico.test.ts`.

### Veredicto por regla (solo aplicables)

| Regla | Veredicto | Evidencia concreta |
|---|---|---|
| RN-CJ-01 | ✅ | `test_confirmar_pago_publico_crea_un_movimiento_y_aprueba` (tipo `ingreso`, `medio_pago in MEDIOS_PAGO`, `usuario_id`, monto); `test_pagos_service.py::test_confirmar_crea_movimiento_con_usuario_y_medio_pago_validos`; `test_models_structure.py::test_movimientos_caja` (CHECK `monto > 0` + NOT NULL) |
| RN-CJ-02 | ✅ | El portal solo agrega `MovimientoCaja` (`test_confirmar_pago_publico_crea_un_movimiento_y_aprueba`, `..._concurrente_un_solo_movimiento`); triggers de `test_caja_inmutable.py` |
| RN-CJ-03 | ⚠️ | Cobra `presupuesto.total` completo, no una seña parcial; la UI titula "Pagá tu seña" (ambigüedad) |
| RN-SEG-01 | ✅ | `test_portal_router.py` (200 sin auth, 404 `not_found`, 422 campo extra); `test_portal_schemas.py` (`extra="forbid"`) |
| R1 | ✅ | `test_portal_schemas.py` (5 schemas rechazan extra); `test_portal_router.py::test_aprobar_campo_extra_422` / `test_rechazar_campo_extra_422` |
| R2 | ✅ | `test_models_structure.py::test_ninguna_tabla_tiene_tenant_id`; `portalPublico.test.ts` (marca sin `slug`/`tenant`/`sucursal`); rutas sin tenant |
| R3 | ✅ | `test_confirmar_pago_publico_crea_un_movimiento_y_aprueba` (un ingreso, sin UPDATE/DELETE) + concurrencia |
| R4 | ✅ | `test_pagos_service.py` (usuario + medio de pago; `TypeError` sin `usuario_id`); portal: `usuario_id` del setting + 409 si no existe |
| R5 | ✅ | Sin migración (sin cambio de schema); `test_portal_settings.py`; type hints; ruff 0 en archivos de C-18 |
| R7 | ⚠️ | `shared/api/public.ts` y componentes tipados, sin `any`; `tsc`/lint/build verde; sin tests de render |
| R8 | ✅ | Sin endpoint privado nuevo; `/pagos` interno conserva `require_role` y pasa `usuario.id` |
| R9 | ⚠️ | Sin IDs internos/PII (`_assert_sin_ids_ni_pii`), 404 genérico, token solo en path (`portalPublico.test.ts`); **falta caplog del portal** |
| R10 | ⚠️ | `totalEnArs` es-AR/ARS y estados/mensajes rioplatenses testeados puros; sin test de render |
| R13 | ✅ | No agrega tablas de negocio ni borra entidades con `deleted_at`; el servicio no hace DELETE |
| ➖ | ➖ | RN-AG-01..06, RN-CL-01/02, RN-G-01, R6, R11, R12: fuera del scope de C-18 |

### Ambigüedades detectadas

- **Firma simple vs trazabilidad:** `AprobacionPublicaIn.firma` se exige (`min_length=1`) pero `PortalPublicoService.aprobar` nunca la persiste (no hay columna). Lectura A: gate de UI; Lectura B: prueba del firmante. Propuesta: registrar `aprobado_por`/`firma` (exige migración, fuera de C-18) o documentar que no se persiste.
- **Motivo de rechazo:** `RechazoPublicoIn.motivo` se acepta (máx. 255) y se descarta, igual que la firma.
- **"Pagá tu seña" vs saldo total (RN-CJ-03):** el endpoint cobra el total del presupuesto, no una seña parcial ni la deducción de saldo de RN-CJ-03. Regla de dominio a decidir.
- **Aprobación pública anónima:** poseer el token opaco se trata como autorización suficiente; ¿se exige DNI u otro dato? Queda como Open Question del design.

### Conflictos detectados

- **Ninguno** entre reglas duras y C-18: se respetan R2, R3, R4 y R9 en las superficies públicas.
- **Observación (no conflicto):** `RN-SEG-01` exige `extra="forbid"` en rutas públicas; `POST /pagos/{token}/confirmar` no declara cuerpo y un body con campos extra se ignora (no 422). No viola un schema (no hay schema), pero incumple el espíritu de R1/RN-SEG-01 para esa ruta.

### Cobertura faltante propuesta

1. **R9 — logs del portal.** `test_portal_service.py::test_confirmar_pago_publico_no_loguea_datos_sensibles(caplog)`: `set_level(DEBUG)`, confirmar, y afirmar que ningún registro `app.*` contiene token, DNI, teléfono ni descripción clínica.
2. **RN-CJ-01 — borde `total <= 0`.** `test_confirmar_pago_publico_con_total_cero_no_crea_movimiento`: presupuesto `aprobado` con `total=0` → 409/422 amigable y 0 movimientos (hoy 500 por `IntegrityError`).
3. **R1 — `confirmar` con body extra.** `test_confirmar_campo_extra_422`: enviar `{"foo":"bar"}` a `POST /pagos/{token}/confirmar` y esperar 422 (requiere schema de entrada vacío con `extra="forbid"`).
4. **R9 — logging negativo a nivel HTTP** para el portal, cubriendo el escenario "Sin datos sensibles en logs" del spec `public-portal`.
5. **R10/R7 — render de componentes** (Playwright/RTL): total en ARS y marca única montada; hoy solo hay helpers puros.
6. **`public-portal` — "Ruta pública desconocida".** Agregar una vista/vía de "no encontrado" para prefijos públicos (hoy el catch-all manda a `/login`).

### Preguntas abiertas propuestas (para `knowledge-base/10_preguntas_abiertas.md`, sin editar en este paso)

- ¿La firma simple debe persistirse como prueba de quién aprobó? (implica columna + migración).
- ¿El motivo de rechazo debe guardarse?
- ¿El pago del portal es el total del presupuesto o una seña parcial deducible (RN-CJ-03)?

### Revisión crítica

- **Omisión detectada (borde contable):** confirmar el pago de un presupuesto `aprobado` con `total <= 0` intenta insertar un `MovimientoCaja` con monto no positivo y revienta contra `CHECK (monto > 0)` sin respuesta controlada.
- **Cómo se detectó:** lectura de `portal_service.confirmar_pago_publico` (`monto=presupuesto.total`) + `caja/models.py` (`CheckConstraint("monto > 0")`) + `presupuestos/models.py` (sin CHECK sobre `total`).
- **Antes:** `Pago(monto=0.0)` → `CobradorSimulado.procesar(0.0)` → `"aprobado"` → `MovimientoCaja(monto=0)` → `IntegrityError` en `flush()` → HTTP 500, sin test.
- **Después propuesto:** en el servicio, `if float(pago.monto) <= 0: raise HTTPException(422, "El presupuesto no tiene un monto cobrable")` (o 409) + el test (2). Cita: RN-CJ-01 ("monto $>0$").
- **Segundo hallazgo (trazabilidad):** `firma` y `motivo` se validan y se descartan; no se puede auditar quién aprobó ni por qué se rechazó. No viola una regla dura, pero contradice la intención "firma simple" del spec; se registra como pregunta abierta (implementarlo exige migración, R5).

### Resumen cuantitativo (scope C-18)

- Reglas auditadas: 27 (14 RN-* + 13 R*).
- ✅ cubiertas: 11 (73% de las 15 aplicables).
- ⚠️ parciales: 4 (RN-CJ-03, R7, R9, R10).
- ❌ sin cobertura: 0.
- ➖ no aplica: 12 (RN-AG-01..06, RN-CL-01/02, RN-G-01, R6, R11, R12).

---

## Auditoría C-21 — Reportes (`c-21-reportes`, 2026-11-14)

**Scope:** change `c-21-reportes` (reportes de gestión de solo lectura: ocupación, facturación, ausentismo + export CSV es-AR; sin migración).
**Fuentes leídas:** KB `03`, `04`, `05`, `06`; `AGENTS.md` (R1–R13); `proposal.md`, `design.md`, `specs/reports/spec.md`, `tasks.md`; `backend/src/app/modules/reportes/{schemas,service,csv,router}.py`; tests `backend/test/test_reportes_*.py`; frontend `src/shared/api/reportes.ts`, `src/features/reportes/{Ocupacion,Facturacion,Ausentismo}Page.tsx`, `src/app/router.tsx`.

### Veredicto por regla (solo aplicables)

| Regla | Veredicto | Evidencia concreta |
|---|---|---|
| RN-AG-05 | ⚠️ | `test_reportes_ocupacion_service.py` cuenta estados `reservado/confirmado/presente/atendido/cancelado` (solo lectura, no impone antisolapamiento). |
| RN-CJ-01 | ✅ | `test_reportes_facturacion_service.py` lee `medio_pago`/`monto` de `MovimientoCaja` tipo ingreso sin crear cobros. |
| RN-SEG-01 | ✅ | `test_reportes_*_router.py::test_sin_token_401` y `test_reportes_integracion.py` (401 sin token en los tres reportes). |
| R1 | ✅ | `test_reportes_schemas.py::test_*_extra_forbid` (todos los schemas de reportes rechazan campo extra). |
| R2 | ✅ | Consultas de reportes sin `tenant_id` (mono-consultorio); no hay tabla nueva (`test_structure.py`). |
| R3 | ✅ | `reportes/service.py` solo usa `select` (solo lectura; no escribe en caja). |
| R5 | ✅ | Sin cambio de schema → sin migración (`alembic heads` = `0016_auditoria`); type hints y `snake_case`; ruff 0 en archivos de C-21. |
| R7 | ⚠️ | `shared/api/reportes.ts` y páginas `PascalCase` sin `any`; `tsc`/lint/build verde; sin tests de render de componentes. |
| R8 | ✅ | `require_role` + `usuario_con_filtro_profesional`: admin/recepción global, odontólogo 403 salvo ocupación propia (`test_reportes_*_router.py`, `test_reportes_integracion.py`). |
| R9 | ⚠️ | `test_reportes_export_router.py::test_export_csv_r9_no_datos_clinicos` (CSV sin DNI/clinical); sin caplog de reportes. |
| R10 | ⚠️ | CSV es-AR (BOM, `;`, coma decimal, `dd/mm/aaaa`); montos en ARS con `formatArs`; sin test de render. |
| R11 / R12 | ➖ | Reglas de proceso; no se commiteó ni pusheó en esta sesión. |
| R13 | ➖ | C-21 es solo lectura; no borra físicamente entidades de negocio. |
| ➖ | ➖ | RN-AG-01/02/03/04/06, RN-CL-01/02, RN-CJ-02/03, RN-SEG-02, RN-G-01, R4, R6: fuera del scope de C-21 (solo lectura). |

### Ambigüedades detectadas

- **RN-CJ-01 (monto cubierto por OS vs paciente):** `descuento_global` se interpreta como porcentaje cubierto por la obra social (`monto_os = monto * descuento / 100`); la KB no especifica la fórmula exacta de copago. Propuesta: registrar en `knowledge-base/10_preguntas_abiertas.md` si se requiere precisión contable.
- **D5 (turno recuperado):** no hay campo de reagendado; C-21 usa heurística "paciente con N turnos en el rango → N-1 recuperados" (documentada en `design.md` §D5 y Open Questions).

### Conflictos detectados

- Ninguno entre reglas duras y C-21: respeta R2, R3, R8, R9, R13.

### Cobertura faltante propuesta

Todos los escenarios del spec `reports` tienen tests (`test_reportes_*.py`, 49 tests). Ningún escenario queda sin cobertura.

### Resumen cuantitativo (scope C-21)

- Reglas auditadas: 27 (13 RN-* + 14 R*).
- ✅ cubiertas: 11.
- ⚠️ parciales: 3 (RN-AG-03, RN-AG-04, R7, R9, R10 — lectura de datos regulados o sin tests de render).
- ❌ sin cobertura: 0.
- ➖ no aplica: 13 (reglas de escritura que C-21 de solo lectura no toca).

