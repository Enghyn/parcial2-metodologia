# Proposal

## Why

El consultorio ya cuenta con reserva pública (C-06/C-10), presupuestos con aprobación online (C-16) y pagos simulados con confirmación idempotente (C-17), pero cada pieza vive en una superficie aislada y sin una cara pública unificada: el paciente no tiene un único portal con la marca del consultorio donde ver y aprobar su presupuesto, pagar una seña/saldo simulado y confirmar el resultado. Además, los endpoints públicos actuales de presupuestos y pagos devuelven IDs internos (`id`, `presupuesto_id`, `paciente_id`), lo que contradice R9. C-18 cierra esa brecha con un portal público mínimo, mono-consultorio y sin migración.

## What Changes

- Nuevo portal público unificado bajo la marca única del consultorio (sin slug ni multi-tenant, R2).
- Rutas públicas del portal: `/reservar` (con QR, ya de C-10), `/p/turno/:token`, `/p/presupuesto/:token` y `/p/pagar/:token`.
- Endpoints públicos nuevos bajo `/api/v1/public/*`, todos con schemas `extra="forbid"` (R1):
  - `GET /api/v1/public/presupuestos/{token}` — vista pública mínima del presupuesto (ítems y total, sin IDs internos ni PII).
  - `POST /api/v1/public/presupuestos/{token}/aprobar` y `POST /api/v1/public/presupuestos/{token}/rechazar` — firma/aprobación simple del paciente.
  - `GET /api/v1/public/pagos/{token}` — vista pública del pago pendiente asociado al presupuesto.
  - `POST /api/v1/public/pagos/{token}/confirmar` — confirmación idempotente que crea **un** `MovimientoCaja` real (R3/R4).
- Páginas React reales de presupuesto y pago simulado, que reemplazan los stubs actuales, con textos en español rioplatense y montos en ARS (R10).
- Reuso de los tokens opacos existentes (`Presupuesto.token_publico`) como identificador de las superficies `/p/presupuesto/:token` y `/p/pagar/:token`; sin columnas nuevas y **sin migración** (R5).
- **Sin BREAKING changes**: las rutas internas (`/api/v1/presupuestos`, `/api/v1/pagos`) y sus contratos no se modifican.

## Capabilities

### New Capabilities
- `public-portal`: portal público unificado del consultorio (marca única, páginas de presupuesto y pago simulado, QR del portal y del turno, presentación es-AR/ARS) montado sobre tokens opacos.

### Modified Capabilities
- `budgets`: la aprobación online pasa a exponer una vista pública mínima y aprobación/rechazo por token, sin filtrar IDs internos ni datos de otros pacientes.
- `simulated-payments`: la confirmación desde el portal por token público es idempotente, crea un único `MovimientoCaja` y no expone IDs internos.

## Impact

- Backend: `app/modules/public/{router,schemas,service}.py` y, si hace falta, métodos públicos en los servicios de `presupuestos` y `pagos`. **Sin migración** (no hay cambio de schema).
- Frontend: `features/reserva-publica/*` o nuevo `features/portal-publico/*`, rutas en `app/router.tsx` y reemplazo de los stubs `PresupuestoPublicoPage`/`PagarPage` en `app/pages.tsx`.
- Dependencias: C-10 (reserva pública avanzada), C-16 (presupuestos) y C-17 (pagos simulados), todas completadas y archivadas.
- Seguridad (R9): tokens opacos no adivinables, 404 genérico, respuestas sin PII innecesaria y sin datos sensibles en logs ni en parámetros de URL.
- Fuera de alcance: multi-tenant/slug (R2), pasarela de pago real, facturación fiscal y cualquier migración de base.
