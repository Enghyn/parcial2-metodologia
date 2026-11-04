# Tasks — chore-test-traceability

## 1. R9 backend

- [x] 1.1 Agregar a `test_auth_router.py` un test con `caplog` que verifique que un login fallido no loguea email ni password en `app.*`.
- [x] 1.2 Agregar a `test_agenda_router.py` un test con `caplog` que verifique que `notas`/prestación no aparecen en logs de `app.*`.
- [x] 1.3 Agregar a `test_public_service.py` un test con `caplog` que verifique que nombre/teléfono del paciente no aparecen en logs de `app.*`.
- [x] 1.4 Verificar los tres tests con PostgreSQL.

## 2. Frontend: helpers y tests

- [x] 2.1 Crear `frontend/src/shared/utils/whatsapp.ts` con `construirUrlWhatsapp`; usarlo en `WhatsappButton.tsx`.
- [x] 2.2 Crear `frontend/src/features/clinica/piezas.ts` con `CUADRANTES_FDI`/`PIEZAS_FDI`; usarlo en `OdontogramaPage.tsx`.
- [x] 2.3 Agregar `"test": "node --test test/whatsapp.test.ts test/fdi.test.ts"` en `frontend/package.json`.
- [x] 2.4 Crear `frontend/test/whatsapp.test.ts` y `frontend/test/fdi.test.ts`; verificar `npm test`.
- [x] 2.5 Verificar `npm run lint`, `npx tsc --noEmit` y `npm run build`.

## 3. Trazabilidad

- [x] 3.1 Crear `docs/auditorias/matriz-reglas-tests.md` con la matriz RN/R → test y los estados ✅/⚠️/❌/➖.
- [x] 3.2 Agregar a `knowledge-base/10_preguntas_abiertas.md` la ambigüedad de transiciones RN-AG-05 y el pendiente de tests de componentes.

## 4. Verificación

- [x] 4.1 Correr `pytest -q` con PostgreSQL y `pytest -m "not integration" -q` sin base.
- [x] 4.2 Correr `ruff check src test` y `npm test`, `npm run lint`, `build`.
- [x] 4.3 `openspec validate "chore-test-traceability" --strict` (skip_specs).

## Workflow follow-up

- Revisión humana del design.
- Aplicar y actualizar checkboxes.
- Archivar con `openspec archive "chore-test-traceability" -y` cuando el usuario lo pida.
