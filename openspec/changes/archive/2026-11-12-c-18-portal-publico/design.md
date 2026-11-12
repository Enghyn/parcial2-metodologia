# Design

## Context

Ver `proposal.md` (Why) y los deltas de `specs/public-portal`, `specs/budgets` y `specs/simulated-payments` (qué debe hacer). Estado actual relevante:

- El backend ya tiene `app/modules/public/` con `router.py`, `schemas.py`, `service.py` (`PublicReservaService`) y `qr.py`, montado en `/api/v1/public`. Cubre disponibilidad, pre-reserva, reserva, turno por token, cancelar, reprogramar y QR (C-06/C-10).
- `Presupuesto` ya persiste `token_publico` (UUID `gen_random_uuid()`, opaco y no adivinable) y `ItemPresupuesto`. El router interno expone `POST /presupuestos/aprobar/{token}` devolviendo `PresupuestoOut` (con `id`, `paciente_id`, `token_publico`).
- `Pago` (con `estado`, `monto`, `movimiento_id`, `confirmado_en`) e `IntentoPago` existen, pero `PagoService.confirmar(pago_id)` usa el id interno, no hay entrada pública por token, y crea el `MovimientoCaja` con `usuario_id=None` (viola R4 y el `NOT NULL` de `movimientos_caja.usuario_id`).
- El frontend ya tiene las rutas `/p/presupuesto/:token` y `/p/pagar/:token` en `app/router.tsx`, pero apuntan a stubs en `app/pages.tsx`.
- No hay cambio de schema en este change: **sin migración** (R5).

## Goals / Non-Goals

**Goals:**

- Superficie pública unificada (marca única) para presupuesto y pago simulado, reusando los tokens opacos existentes.
- Endpoints públicos nuevos con contrato tipado y mínimo, sin IDs internos ni PII (R9).
- Confirmación de pago desde el portal idempotente y a prueba de concurrencia, creando exactamente un `MovimientoCaja` con usuario responsable (R3/R4).
- Páginas React reales que reemplazan los stubs, en es-AR y montos en ARS (R10).

**Non-Goals:**

- Multi-tenant o `slug` por consultorio (R2).
- Pasarela de pago real (Mercado Pago u otra) y webhooks externos.
- Facturación fiscal (ARCA/AFIP).
- Migración de base de datos o cambios de schema.
- Cambiar el contrato de los endpoints internos `/api/v1/presupuestos` y `/api/v1/pagos`.

## Decisions

### D1 — Extender el módulo público existente, no crear un módulo nuevo

Los endpoints del portal viven en `app/modules/public/router.py` (prefix `/public`) y se apoyan en un `PortalPublicoService` nuevo en `app/modules/public/service.py` (o `portal_service.py`), siguiendo el patrón de `PublicReservaService`.

- **Por qué:** es una superficie pública más, ya cubierta por el rate-limit (`limitar_publico("lectura"/"escritura")`) y por la convención de schemas `extra="forbid"` (R1).
- **Alternativa descartada:** un módulo `portal` aparte; duplicaría montaje, rate-limit y convenciones sin beneficio.

### D2 — Token de las páginas = `Presupuesto.token_publico`

`/p/presupuesto/:token` y `/p/pagar/:token` resuelven el presupuesto por `token_publico`. El pago no necesita token propio: se identifica a través del presupuesto.

- **Por qué:** `Pago` no tiene columna de token y agregarla requeriría migración (prohibida en C-18). `token_publico` es un UUID aleatorio opaco, apto para URL (R9).
- **Alternativa descartada:** agregar `Pago.token_publico` (migración) o usar `pago_id` en la URL (expone un ID interno y permite enumeración).

### D3 — Idempotencia y concurrencia sin migración: lock pesimista por fila

`POST /api/v1/public/pagos/{token}/confirmar` ejecuta, en una transacción:

1. `SELECT ... FOR UPDATE` sobre la fila de `presupuestos` por `token_publico` (reclamo atómico).
2. Si no existe → 404 genérico.
3. Si `estado != 'aprobado'` → 409.
4. Busca el `Pago` del presupuesto. Si ya hay uno `aprobado` → devuelve el resultado (idempotente, sin nuevo movimiento).
5. Si hay un `Pago` `pendiente` → lo confirma; si no hay ninguno → crea el `Pago` por el monto adeudado y lo confirma.
6. La confirmación procesa con `CobradorSimulado`, registra `IntentoPago` y crea **un** `MovimientoCaja` (R3/R4), actualizando `Pago.estado`, `Pago.movimiento_id` y `Pago.confirmado_en`.

- **Por qué:** el `FOR UPDATE` serializa confirmaciones concurrentes sin `unique` ni tabla de idempotency-key (que exigirían migración), cumpliendo el objetivo de "reclamar atómicamente".
- **Alternativa descartada:** idempotency-key persistida (migración) o `check-then-insert` sin lock (carrera → doble movimiento).

### D4 — Usuario responsable del canal portal (R4)

El `MovimientoCaja` debe tener `usuario_id` (columna `NOT NULL`) y R4 exige usuario responsable. Como el portal es anónimo, se resuelve un usuario de sistema configurable: `settings.portal_usuario_email` (nuevo campo en `Settings`, default `admin@consultorio.com`, que ya viene del seed). Si el usuario no existe/está inactivo → 409 con mensaje genérico.

- **Por qué:** mantiene trazabilidad sin login y sin migración; el consultorio puede apuntar a otro usuario en producción vía entorno.
- **Alternativa descartada:** `usuario_id=None` (como hoy en C-17) → viola R4 y el `NOT NULL`. También se corrige ese punto al tocar `PagoService`.

### D5 — Contratos de los endpoints públicos

Todos los schemas Pydantic de entrada usan `extra="forbid"` (R1) y los de salida solo exponen campos públicos (R9). Forma de error única `{error:{code,message,details?}}` (handler existente).

| Método y ruta | Entrada | Salida | Errores |
|---|---|---|---|
| `GET /api/v1/public/presupuestos/{token}` | `token` (path, UUID) | `PresupuestoPublicoOut` | 404, 422 |
| `POST /api/v1/public/presupuestos/{token}/aprobar` | `AprobacionPublicaIn{firma}` | `PresupuestoPublicoOut` | 404, 409, 422 |
| `POST /api/v1/public/presupuestos/{token}/rechazar` | `RechazoPublicoIn{motivo?}` | `PresupuestoPublicoOut` | 404, 409, 422 |
| `GET /api/v1/public/pagos/{token}` | `token` (path, UUID) | `PagoPublicoOut` | 404, 409, 422 |
| `POST /api/v1/public/pagos/{token}/confirmar` | sin cuerpo | `PagoPublicoOut` | 404, 409, 422 |

Contratos de salida (sin `id`, `paciente_id`, `presupuesto_id`, `movimiento_id` ni `token_publico`):

- `ItemPresupuestoPublicoOut`: `descripcion`, `cantidad`, `arancel`, `copago`.
- `PresupuestoPublicoOut`: `estado`, `total`, `items: list[ItemPresupuestoPublicoOut]`.
- `PagoPublicoOut`: `estado`, `monto`, `confirmado_en`.

`aprobar`/`rechazar` solo actúan sobre `estado == 'enviado'`; `aprobar` sobre `'aprobado'` es idempotente (200); cualquier otra transición → 409.

- **Por qué:** una sola forma de error y contratos mínimos; el frontend valida solo en el borde y confía en los tipos.
- **Alternativa descartada:** reusar `PresupuestoOut`/`PagoOut` internos → filtrarían IDs internos (viola R9).

### D6 — R9: tokens opacos, 404 genérico y sin PII

- El token es un UUID aleatorio no adivinable; no se aceptan IDs internos en ninguna ruta pública.
- Token inexistente → 404 genérico (`not_found`), sin distinguir "no existe" de "no corresponde".
- Los schemas públicos omiten PII (nombre/DNI/teléfono del paciente) y datos clínicos.
- No se loguean tokens con PII ni cuerpos con datos sensibles; el logging existente no registra payloads de salud.
- Reuso de `limitar_publico("lectura"/"escritura")` para que el portal no sea un vector de abuso.

### D7 — Frontend: páginas reales en `features/portal-publico/`

Se reemplazan los stubs de `app/pages.tsx` por componentes reales, importados **directamente** (sin barrel nuevo) desde `app/router.tsx`:

- `features/portal-publico/PresupuestoPublicoPage.tsx`: resuelve `token` de `useParams`, hace fetch del presupuesto y del pago **en paralelo** (`Promise.all`) y renderiza `ResumenPresupuesto` + `FirmaSimple`.
- `features/portal-publico/PagarPage.tsx`: fetch del pago, muestra monto en ARS y `ResultadoPago`; el botón "Confirmar pago" queda `disabled` mientras la request está en curso (evita doble clic).
- `features/portal-publico/ResumenPresupuesto.tsx`, `FirmaSimple.tsx`, `ResultadoPago.tsx`, `MarcaConsultorio.tsx` (memoizados donde el subárbol sea costoso).
- Tipos y llamadas tipadas en `shared/api/public.ts` (mismo patrón `request<T>` con import diferido): `getPresupuestoPublico`, `aprobarPresupuestoPublico`, `rechazarPresupuestoPublico`, `getPagoPublico`, `confirmarPagoPublico`.
- `MarcaConsultorio` se muestra en `PublicLayout` para unificar la marca de `/reservar`, `/p/turno/:token`, `/p/presupuesto/:token` y `/p/pagar/:token` (sin slug ni selector de sucursal).
- `React.lazy` + `<Suspense>` para las páginas públicas, de modo que `/app` no cargue el bundle del portal.
- Estado derivado en render (no `useEffect` para derivar), `setState` funcional en callbacks, ternario en vez de `&&`, sin componentes anidados (estándar React/Vite del proyecto).
- Estilos con Tailwind v4 CSS-first (`@import "tailwindcss"` + `@theme`), sin `tailwind.config.ts`; tokens semánticos y overrides en `.dark`.

- **Por qué:** consistencia con `features/reserva-publica/` y con las rutas ya declaradas; mantiene el bundle público liviano.
- **Alternativa descartada:** dejar los stubs (no cumplen las specs) o crear un barrel nuevo (contra el estándar "sin imports de barrel").

## Risks / Trade-offs

- **[R9 — fuga de datos entre pacientes]** → Los endpoints públicos solo aceptan token opaco y devuelven un DTO mínimo; no hay endpoint que liste presupuestos/pagos por ID. Mitigación extra: 404 genérico y tests de "sin IDs internos" y "token inexistente".
- **[Idempotencia bajo concurrencia]** → Sin `unique`/idempotency-key (no hay migración), el `SELECT ... FOR UPDATE` es la única garantía. Mitigación: test de dos confirmaciones concurrentes que verifica exactamente un `MovimientoCaja`; documentar que el lock requiere que la sesión transaccional sea la misma.
- **[R4 — usuario responsable]** → Depende de `portal_usuario_email`; si el usuario no existe el pago falla con 409. Mitigación: default = admin del seed, validación explícita y test del caso "usuario inexistente".
- **[Deuda de C-17]** → `PagoService.confirmar` crea el movimiento con `usuario_id=None`. Mitigación: al tocar el servicio en este change, exigir `usuario_id` y ajustar su firma/test.
- **[Aprobación pública de presupuesto]** → El endpoint de aprobación es anónimo por diseño (firma simple, no legal). Mitigación: registrar `aprobado_en` y limitar transiciones; la firma simple no reemplaza consentimiento clínico.

## Migration Plan

- **Sin migración de base de datos** (no hay cambio de schema; R5). `alembic upgrade head` no aporta revisiones nuevas para C-18.
- Cambios de configuración: nuevo setting `portal_usuario_email` (default `admin@consultorio.com`); documentarlo en los `.env.example` correspondientes.
- Rollback: revertir los archivos de `app/modules/public/*`, el setting, los componentes del portal y las rutas; al no haber migración, no hay paso de base que deshacer.

## Open Questions

- ¿La firma simple debe incluir también el DNI del paciente para mayor trazabilidad, o alcanza con el nombre? (Se puede responder durante la implementación sin cambiar specs ni tasks; hoy el spec solo exige "firma simple".)
- ¿Conviene exponer `GET /api/v1/public/presupuestos/{token}` también para presupuestos `borrador`? (Se decide con el usuario; por ahora solo `enviado`/`aprobado`/`rechazado`/`cobrado` son consultables y la acción se restringe a `enviado`.)
