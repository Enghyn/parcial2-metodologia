# Proposal — chore-test-traceability

## Why

La auditoría de reglas encontró tres huecos: R9 solo estaba testeado en C-07, RN-G-01 no tenía test, y el frontend no tenía runner ni tests. Además, la trazabilidad regla → test no estaba escrita en ningún artefacto.

## What Changes

- Tests `caplog` de R9 en auth, agenda y reserva pública: credenciales, notas clínicas y datos de paciente no deben aparecer en logs de `app`.
- Extraer `construirUrlWhatsapp` a `shared/utils/whatsapp.ts` y testearlo con `node:test` (Node 24, sin dependencias nuevas).
- Extraer `CUADRANTES_FDI`/`PIEZAS_FDI` a `features/clinica/piezas.ts` y testear que sean 32 piezas únicas y válidas.
- Script `npm test` en `frontend/package.json`.
- Matriz persistente `docs/auditorias/matriz-reglas-tests.md` con regla → test.
- Aclarar en `knowledge-base/10_preguntas_abiertas.md` la ambigüedad de transiciones de estado (RN-AG-05).

## Capabilities

### New Capabilities

- Ninguna.

### Modified Capabilities

- Ninguna: son tests y documentación. El change usa `skip_specs: true`.

## Impact

- **Backend tests**: `test_auth_router.py`, `test_agenda_router.py`, `test_public_service.py`.
- **Frontend**: helpers `whatsapp.ts`, `piezas.ts`, test runner Node, `WhatsappButton.tsx` y `OdontogramaPage.tsx`.
- **Docs**: `docs/auditorias/` y KB 10.
- **Sin cambios de API, modelos, migraciones ni comportamiento de producto.**
- **Fuera de alcance**: tests de componentes React con DOM/Playwright y C-08 (aún no implementado).
