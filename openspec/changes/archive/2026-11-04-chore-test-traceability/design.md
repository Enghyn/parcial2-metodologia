# Design — chore-test-traceability

## Context

Ver `proposal.md` — Why. Node 24 ejecuta TypeScript con type stripping y trae `node:test`; no hace falta sumar Vitest ni jsdom para helpers puros. Los tests de backend ya usan `caplog` en C-07 y el marker `integration`.

## Goals / Non-Goals

**Goals:**

- Cerrar R9 en auth/agenda/público.
- Dar un runner mínimo de frontend y tests de RN-G-01/FDI.
- Dejar la matriz regla → test versionada.

**Non-Goals:**

- Tests de componentes React o E2E con navegador.
- Cambiar comportamiento de producto.
- Testear C-08 antes de implementarlo.

## Decisions

### D1 — Node nativo para tests de helpers

`node --test test/*.test.ts` con `node:test` y `node:assert/strict`. Los helpers son TS con sintaxis erasable; no se agregan dependencias.

- **Por qué**: cero deps, rápido, compatible con Node 24.
- **Alternativa descartada**: Vitest/jsdom (más peso; se reserva para tests de componentes).

### D2 — R9 con caplog filtrado por `app.*`

Cada test captura `DEBUG` y solo inspecciona registros cuyo logger empieza con `app`; así no se mezclan logs de SQLAlchemy.

- **Por qué**: evita falsos positivos por SQL y verifica la superficie propia.
- **Alternativa descartada**: revisar todo el log (incluye queries).

### D3 — Helpers puros

- `construirUrlWhatsapp(telefono, mensaje)` normaliza dígitos, codifica el mensaje y devuelve `""` si no hay teléfono.
- `CUADRANTES_FDI`/`PIEZAS_FDI` centralizan las 32 piezas.
- `WhatsappButton` y `OdontogramaPage` consumen los helpers; el comportamiento visible no cambia.

### D4 — Matriz persistente

`docs/auditorias/matriz-reglas-tests.md` lista RN/R, evidencia y estado; se actualiza antes de archivar changes.

## Risks / Trade-offs

- [Node type stripping] → los tests usan imports relativos con `.ts`; si una versión de Node no lo soporta, se ejecuta con `--experimental-strip-types`.
- [Solo helpers, no componentes] → el gap de UI E2E sigue abierto; se documenta y se propone Playwright para un change futuro.
- [R9 puede quedar trivial] → los tests pasan porque no hay logs; sirven como regresión si alguien agrega logging con PHI.

## Migration Plan

Sin migración. Solo tests, helpers y documentación.

## Open Questions

- ¿Se incorpora Playwright para C-05/C-06/C-07 en un change posterior? Recomendado, fuera de este.
