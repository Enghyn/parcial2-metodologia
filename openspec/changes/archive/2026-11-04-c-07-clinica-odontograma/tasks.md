# Tasks — C-07 clinica-odontograma

> **TDD estricto.** Backend desde `backend/`; integración con PostgreSQL migrado y sembrado.

## 1. Safety net y RED de schemas

- [x] 1.1 Correr `python -m pytest -m "not integration" -q` y `python -m pytest -q` con base; registrar la línea base (esperado: 161/8/64 y 226/7).
- [x] 1.2 Crear `backend/test/test_clinica_schemas.py` con tests que fallen: `extra="forbid"`, `PacienteCreate` exige nombre/DNI/teléfono, `HallazgoIn` rechaza `conducto` y acepta `tratamiento_conducto`.
- [x] 1.3 **GREEN**: implementar `clinica/schemas.py`; verificar los tests.

## 2. Servicio y router (integración)

- [x] 2.1 **RED**: crear `test_clinica_service.py` con casos que fallen: listado sin borrados, alta con DNI duplicado 409, GET crea odontograma, GET de paciente borrado 404, upsert inserta y actualiza, pieza 19 → 422.
- [x] 2.2 **GREEN**: implementar `clinica/service.py` (`PacienteService`, `OdontogramaService`) con filtros `deleted_at IS NULL`; verificar verde.
- [x] 2.3 **RED**: crear `test_clinica_router.py` con casos HTTP: 401 sin token, 403 de recepción en PUT, GET/POST listado/alta, GET odontograma, PUT pieza.
- [x] 2.4 **GREEN**: implementar `clinica/router.py`, montar en `api/v1/router.py` y actualizar `test_structure.py` (`MODULOS_SIN_STUBS` y `MODULOS_CON_RUTAS` con `clinica`).
- [x] 2.5 **TRIANGULATE**: agregar caso de búsqueda por nombre/DNI, pieza existente actualizada y paciente borrado; verificar.
- [x] 2.6 **REFACTOR**: extraer validación FDI y evitar duplicar queries; correr `ruff`.

## 3. Frontend

- [x] 3.1 Crear `frontend/src/shared/api/clinica.ts` tipado (sin `any`) con `listarPacientes`, `crearPaciente`, `getOdontograma`, `upsertPieza`.
- [x] 3.2 Crear `features/clinica/PacientesPage.tsx` (directorio, buscador, alta para admin/recepción, link al odontograma) y `OdontogramaPage.tsx` (4 cuadrantes, 32 piezas, selector de estado/observación, guardado y gating por rol).
- [x] 3.3 Actualizar `features/clinica/index.ts`, `app/router.tsx` y `app/layout.tsx` (navegación Agenda/Pacientes).
- [x] 3.4 Verificar `npm run lint`, `npx tsc --noEmit` y `npm run build`.

## 4. Documentación

- [x] 4.1 Corregir `CHANGES.md` C-07: `conducto` → `tratamiento_conducto` y aclarar que el filtro de odontogramas es por paciente activo.
- [x] 4.2 Verificar `openspec validate "c-07-clinica-odontograma" --strict`.

## 5. Verificación integral

- [x] 5.1 Correr `python -m pytest -q` con PostgreSQL **dos veces seguidas** y confirmar que no queda data sucia.
- [x] 5.2 Correr `ruff check src test` en cero.
- [x] 5.3 Correr `openspec validate --all` y confirmar 0 fallos.
- [x] 5.4 Pasar `business-rule-coverage-auditor` sobre C-07 (RN-CL-01/02, R1, R8, R9, R13).

## 6. Endurecimiento post-auditoría

- [x] 6.1 R9: `test_no_loguea_estado_ni_observacion` con `caplog` sobre logs de `app`.
- [x] 6.2 Odontograma: creación atómica con `INSERT ... ON CONFLICT DO NOTHING` para GET concurrentes.
- [x] 6.3 Paciente: `IntegrityError` por DNI duplicado en carrera → 409 con rollback.
- [x] 6.4 Verificar suite completa dos veces, `ruff` y `openspec validate`.

## Workflow follow-up

- Revisión humana del design (decisión D1: sin `deleted_at` en odontogramas).
- Aplicar con TDD y actualizar checkboxes.
- Archivar con `openspec archive "c-07-clinica-odontograma" -y`.
- Marcar C-07 `[x]` en `CHANGES.md` y `AGENTS.md`.
