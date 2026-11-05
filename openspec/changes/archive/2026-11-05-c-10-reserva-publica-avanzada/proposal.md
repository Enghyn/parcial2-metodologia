# Proposal — C-10 reserva-publica-avanzada

## Why

El portal de C-06 no retiene el hueco mientras el paciente completa sus datos: dos personas pueden elegir el mismo horario y la segunda recibe 409 recién al final del formulario, después de cargar nombre, DNI y teléfono. Tampoco existe autogestión del turno (reprogramar sin llamar), ni una forma de llegar al portal desde el mostrador, ni ninguna defensa contra abuso automatizado de los endpoints públicos. C-09a ya resolvió reprogramación, ventana mínima y `ausente` del lado interno, así que el portal puede reusar esa lógica en lugar de duplicarla.

## What Changes

- **Pre-reserva (retención) con expiración**: nuevo `POST /api/v1/public/pre-reservas` que retiene un hueco concreto por un TTL configurable (default 10 min) y devuelve un `pre_reserva_token` opaco. Al vencer, el hueco vuelve a ofrecerse sin intervención manual.
- **Reserva sobre una pre-reserva**: `POST /api/v1/public/reservar` acepta un `pre_reserva_token` **opcional**. Con token, valida que el hueco retenido coincida con el payload, crea el turno y consume la retención en la misma transacción. Sin token, el contrato de C-06 sigue funcionando igual (aditivo).
- **Disponibilidad consciente de retenciones**: `GET /api/v1/public/disponibilidad` deja de ofrecer huecos con una retención vigente, para que dos pacientes no elijan el mismo horario.
- **Reprogramación pública por token**: nuevo `POST /api/v1/public/turnos/{token}/reprogramar` que mueve el turno a otro hueco libre conservando sillón, profesional y duración, con la misma ventana mínima de autogestión que la cancelación y el antisolapamiento de `TurnoService` (R6).
- **Rate-limit local**: límite en memoria por IP y por bucket (lectura/escritura) sobre las superficies públicas, con `429` + `Retry-After`. Sin captcha ni servicio externo.
- **QR local**: `GET /api/v1/public/qr/reserva.svg` y `GET /api/v1/public/turnos/{token}/qr.svg` devuelven el SVG del portal y del turno, generado en el backend sin red ni proveedor externo.
- **Origen del turno**: `turnos.origen` (`interno` | `publico`) para distinguir una reserva autogestionada de una cargada por recepción.
- **Migración `0006`**: tabla `pre_reservas` + columnas `turnos.origen`. La última migración real es `0005_agenda_indice_inicio`.
- **Frontend**: el wizard retiene el hueco al entrar al paso de datos, muestra la cuenta regresiva y recupera el flujo si la retención vence; `/p/turno/:token` suma QR y acceso a reprogramar; nueva página `/p/turno/:token/reprogramar`; estados de error de rate-limit y de conflicto en es-AR.

**BREAKING:** ninguna. `pre_reserva_token` es opcional, `origen` tiene default `interno`, los endpoints nuevos son aditivos y las retenciones no bloquean la agenda interna.

## Capabilities

### New Capabilities

Ninguna. El rate-limit y el QR son comportamiento observable del portal público, no una plataforma aparte: `local-platform` describe entorno y puertas de calidad (Compose, CI, layout), no contratos de la API pública, y una capability `public-rate-limit` duplicaría el dueño del mismo borde HTTP. Ambos quedan en `public-reservation`, que ya es dueña de `/api/v1/public/*` y de sus reglas de exposición.

### Modified Capabilities

- `public-reservation`: la enumeración de endpoints públicos suma pre-reserva, reprogramación y QR; se agregan requisitos de retención temporal, expiración, reserva sobre retención, disponibilidad sin huecos retenidos, reprogramación autónoma, rate-limit local y QR, más la presentación en el portal.
- `agenda`: el contrato interno del turno expone `origen` (`interno` | `publico`) y se declara explícitamente que las pre-reservas públicas no bloquean la creación interna ni cambian la validación de antisolapamiento (RN-AG-01/R6).

## Impact

- **Backend**: `modules/public/{router,schemas,service}.py` (pre-reserva, reprogramación, QR), `modules/agenda/{models,service,schemas}.py` (`origen`, `crear(..., origen=...)`, `TurnoOut`), `modules/public/models.py` (nuevo `PreReserva`), `core/rate_limit.py` (nuevo), `core/errors.py` (`429`), `core/config.py` (`public_base_url`, TTL, ventanas y límites), `api/v1/router.py`, migración `0006_pre_reserva_origen`, `db/registry.py`, `db/seed.py` (sin datos de retención).
- **Frontend**: `features/reserva-publica/` (retención y cuenta regresiva en el wizard, QR, reprogramación, estados de error), `shared/api/public.ts`, `shared/api/client.ts` (`Retry-After` en `ApiError`), `shared/rateLimit.ts` (helper puro), `app/router.tsx` y `app/pages.tsx`.
- **Datos**: tabla nueva `pre_reservas` (sin borrado físico: estados `vigente`/`consumida`/`expirada`/`cancelada`) y dos columnas aditivas en `turnos`. Sin `tenant_id` (R2).
- **Dependencia nueva**: generador de QR en Python puro, sin Pillow ni servicio externo (ver `design.md` D7). No se agrega Redis, Celery ni captcha.
- **Contratos**: `/api/v1/public/*` suma tres endpoints y un campo opcional; `TurnoOut` suma `origen`. Los consumidores actuales siguen funcionando.
- **Dependencias**: C-06 (`public-reservation`) y C-09a (reprogramación y ventana) archivados. Habilita C-15 (lista de espera con oferta y expiración) y C-18 (portal con `/p/turno/:token` y QR).
- **Fuera de alcance**: reprogramación que cambie sillón o profesional, reprogramación de sobreturnos, pago de señas (C-17), notificaciones (C-14), captcha, Redis, QR de presupuestos (C-16/C-18) y persistencia del rate-limit entre procesos.
- **Discrepancia de KB (no se inventa la regla)**: `CHANGES.md` cita `RN-AG-07` para este change, pero `knowledge-base/05_reglas_de_negocio.md` solo define `RN-AG-01` a `RN-AG-06`. Este propose **no** crea ni cita `RN-AG-07` como existente: registra la propuesta de redacción en `design.md` §Open Questions y en §Risks para que el grupo la confirme antes de archivar. Mientras tanto, el comportamiento se especifica en los delta specs y se apoya en `RN-AG-06` (datos obligatorios de la reserva pública) y en la ventana de cancelación ya implementada por C-09a.
