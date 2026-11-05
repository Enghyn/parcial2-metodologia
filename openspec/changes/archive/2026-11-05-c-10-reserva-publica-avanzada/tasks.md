# Tasks — C-10 reserva-publica-avanzada

> **TDD estricto.** Backend desde `backend/` con PostgreSQL migrado y sembrado para integración. Frontend con `node:test` puro (no hay harness de componentes React): la lógica de retención, cuenta regresiva, `Retry-After` y URLs de QR se prueba primero; el render se valida con `tsc`, `eslint`, `build` y Playwright.
> Cada grupo escribe sus tests antes de implementar y actualiza la documentación que su trabajo exige. No commitear ni pushear (R11).
>
> **Reglas duras en juego:** R1 (`extra="forbid"`), R2 (sin `tenant_id`), R5 (type hints, `snake_case`, migración), R6 (antisolapamiento en servicios + test de conflicto), R8 (RBAC en backend; público acotado por token), R9 (tokens opacos, sin datos de salud en logs/URLs), R10 (es-AR, ARS), R13 (sin borrado físico).
>
> **Criterio visual:** `mockups/` (revisión 1 del design system) es criterio de aceptación. Durante la verificación, comparar cada pantalla contra `mockups/previews/` a 390×844 y 1440×900 y registrar el resultado en `design.md` (`Visual verify`).

## 1. Safety net

- [x] 1.1 Correr la línea base del backend y anotar los conteos en este archivo: `cd backend; python -m pytest -m "not integration" -q; python -m pytest -q`. Verificación: ambos comandos terminan en 0 y los conteos quedan registrados.
- [x] 1.2 Correr la línea base del frontend: `cd frontend; npm test; npm run lint; npx tsc --noEmit`. Verificación: los tres comandos terminan en 0.
- [x] 1.3 Releer `backend/src/app/modules/public/{router,schemas,service}.py`, `backend/src/app/modules/agenda/{models,service,schemas}.py`, `backend/src/app/core/{config,errors,middleware}.py`, `backend/src/app/db/{base,registry}.py`, `frontend/src/features/reserva-publica/`, `frontend/src/shared/api/{public,client}.ts` y `frontend/src/app/router.tsx`. Verificación: nota breve en este archivo confirmando que `detectar_conflicto`, `solapamiento` y `require_role` no se modifican en este change.
- [x] 1.4 Registrar la última migración real: `cd backend; alembic current`. Verificación: el output confirma `0005_agenda_indice_inicio` y la nota queda en este archivo (si no coincide, renombrar `0006` antes de continuar).

## 2. Configuración nueva

- [x] 2.1 **RED**: ampliar `backend/test/test_settings.py` con defaults y validación de `public_base_url`, `pre_reserva_ttl_min` (> 0), `reprogramacion_min_horas` (≥ 0), `rate_limit_enabled`, `rate_limit_public_window_s` (> 0), `rate_limit_public_read_max` (> 0) y `rate_limit_public_write_max` (> 0). Verificación: `python -m pytest test/test_settings.py -q` falla por atributos ausentes.
- [x] 2.2 **GREEN**: agregar las siete settings a `backend/src/app/core/config.py` con `Field(...)` y type hints. Verificación: el test de 2.1 pasa.
- [x] 2.3 Documentar las claves nuevas en `.env.example` (valores de ejemplo, sin secretos) y ampliar `backend/test/test_env_examples.py` para exigirlas. Verificación: `python -m pytest test/test_env_examples.py test/test_settings.py -q` en verde.
- [x] 2.4 **TRIANGULATE**: verificar que `rate_limit_enabled=false` y `pre_reserva_ttl_min=1` se cargan desde entorno (`monkeypatch.setenv`) sin romper el arranque. Verificación: el caso nuevo pasa y `ruff check src test` no reporta hallazgos.

## 3. Migración `0006` y modelos

- [x] 3.1 **RED**: crear `backend/test/test_migration_0006.py` exigiendo `revision="0006_pre_reserva_origen"`, `down_revision="0005_agenda_indice_inicio"`, `create_table("pre_reservas")` con `token` unique y FK a `turnos`, `add_column("turnos", "origen")` con `server_default='interno'` y `nullable=False`, los `CHECK` de estado/rango/coherencia, los tres índices, y el `downgrade` con `drop_column` + `drop_table`. Verificación: el archivo falla.
- [x] 3.2 **GREEN**: crear `backend/src/app/modules/public/models.py` con `PreReserva` (`TimestampMixin`, sin `SoftDeleteMixin`, sin `deleted_at`) y agregar `origen` a `Turno` en `backend/src/app/modules/agenda/models.py`. Verificación: `test_migration_0006.py` pasa y `test_models_structure.py` se actualiza a diez tablas.
- [x] 3.3 **GREEN**: crear `backend/src/app/db/migrations/versions/0006_pre_reserva_origen.py` con `upgrade`/`downgrade` reversibles y registrar `app.modules.public.models` en `backend/src/app/db/registry.py`. Verificación: `test_migration_0006.py`, `test_migrations.py` y `test_models_structure.py` en verde.
- [x] 3.4 **TRIANGULATE**: agregar al test de migración que `alembic upgrade head --sql` contiene `CREATE TABLE pre_reservas` y `ALTER TABLE turnos ADD COLUMN origen`, y que `downgrade 0005_agenda_indice_inicio --sql` contiene `DROP TABLE pre_reservas` y `DROP COLUMN origen`. Verificación: ambas aserciones pasan.
- [x] 3.5 **APLICAR**: `cd backend; alembic upgrade head; alembic downgrade 0005_agenda_indice_inicio; alembic upgrade head`. Verificación: los tres comandos terminan en 0, `alembic current` marca `0006_pre_reserva_origen` y `\d pre_reservas` muestra los tres índices.

## 4. Origen del turno (agenda)

- [x] 4.1 **RED**: crear `backend/test/test_turno_origen.py` con: `TurnoCreate` rechaza `origen` (422 por `extra="forbid"`), `TurnoOut` incluye `origen`, `TurnoService.crear` persiste `interno` por defecto y `publico` cuando se pasa `origen="publico"`, y `crear_sobreturno` persiste `interno`. Verificación: el archivo falla.
- [x] 4.2 **GREEN**: agregar `origen: str` a `TurnoOut` y el parámetro keyword-only `origen: str = "interno"` a `TurnoService.crear` y `crear_sobreturno` (`Literal["interno", "publico"]` en la firma). Verificación: el test de 4.1 pasa.
- [x] 4.3 **TRIANGULATE**: agregar a `backend/test/test_agenda_router.py` un caso que cree un turno interno y verifique `origen="interno"` en la respuesta del `GET /turnos`. Verificación: el archivo completo pasa.
- [x] 4.4 **REGRESIÓN RN-AG-01/R6**: correr `python -m pytest test/test_agenda_service.py test/test_agenda_conflicts.py test/test_agenda_schemas.py test/test_public_service.py -q`. Verificación: todo pasa y `git diff` no muestra cambios en `detectar_conflicto` ni en `solapamiento`.

## 5. Dominio de pre-reserva y disponibilidad

- [x] 5.1 **RED**: crear `backend/test/test_pre_reserva_schemas.py` con: `PreReservaCreate` acepta los cinco campos, rechaza `duracion_min <= 0`, rechaza campo extra, normaliza `inicio` naive como ART y rechaza `paciente`/`dni` en el cuerpo. Verificación: el archivo falla.
- [x] 5.2 **GREEN**: crear `PreReservaCreate` y `PreReservaOut` (`pre_reserva_token`, `inicio`, `fin`, `duracion_min`, `expira_en`) en `backend/src/app/modules/public/schemas.py` con `extra="forbid"` (R1). Verificación: el test de 5.1 pasa.
- [x] 5.3 **RED**: crear `backend/test/test_pre_reserva_service.py` (integración) con: retención exitosa con `expira_en = ahora + ttl`, 409 si el rango está ocupado por turno, 409 si está bloqueado, 409 si hay otra retención vigente, 422 con `inicio` pasado, y `estado='vigente'` al crear. Verificación: el archivo falla por ausencia de servicio.
- [x] 5.4 **GREEN**: implementar `PublicReservaService.crear_pre_reserva` reusando `slot_libre` y `TurnoService` para resolver recursos vigentes; persistir con `expira_en` calculado desde `pre_reserva_ttl_min`. Verificación: el test de 5.3 pasa.
- [x] 5.5 **RED**: agregar a `backend/test/test_public_slots.py` (puro) que `slot_libre` devuelve `False` ante una retención vigente del mismo sillón o profesional, `True` ante retención vencida y `True` ante retención de otro recurso. Verificación: los casos nuevos fallan.
- [x] 5.6 **GREEN**: extender `slot_libre` con el parámetro `retenciones: Iterable[PreReserva] = ()` y hacer que `disponibilidad` cargue las retenciones vigentes del día (`estado='vigente' AND expira_en > ahora()`) y las descarte. Verificación: `test_public_slots.py` y `test_public_service.py` en verde.
- [x] 5.7 **TRIANGULATE**: agregar a `test_pre_reserva_service.py` que una retención vencida libera el hueco en `disponibilidad` sin ejecutar limpieza, que dos retenciones seguidas del mismo hueco dan 201 y 409, y que el token es UUID distinto en cada retención con payload idéntico. Verificación: el archivo completo pasa.
- [x] 5.8 **REFACTOR**: extraer `retencion_vigente(retencion, ahora)` como helper puro con type hints y docstring; `ruff check src test`. Verificación: `ruff` limpio y los tests de 5.1–5.7 siguen en verde.

## 6. Endpoints de retención y reserva sobre retención

- [x] 6.1 **RED**: crear `backend/test/test_public_pre_reserva_router.py` con: `POST /public/pre-reservas` 201 sin token de auth, 409 en hueco ocupado, 422 con campo extra, 422 con inicio pasado, y respuesta sin `dni`/`telefono`/`nombre`. Verificación: el archivo falla.
- [x] 6.2 **GREEN**: montar `POST /api/v1/public/pre-reservas` en `backend/src/app/modules/public/router.py` con `response_model=PreReservaOut` y status 201. Verificación: el test de 6.1 pasa.
- [x] 6.3 **RED**: ampliar `backend/test/test_public_router.py` con: reserva con `pre_reserva_token` vigente → 201, retención `consumida` con `turno_id`, turno con `origen="publico"`; token vencido → 409 sin turno; token de otro horario → 409; token reutilizado → 409; y reserva sin token → 201 (compatibilidad C-06). Verificación: los casos nuevos fallan.
- [x] 6.4 **GREEN**: agregar `pre_reserva_token: UUID | None = None` a `ReservaCreate` y la validación/consumo en `PublicReservaService.reservar`, pasando `origen="publico"` a `TurnoService.crear` y confirmando el `UPDATE` de la retención en la misma transacción (sin commit intermedio). Verificación: el test de 6.3 pasa.
- [x] 6.5 **TRIANGULATE**: agregar a `test_public_router.py` que un 409 de antisolapamiento **no** consume la retención (queda `vigente`), que la disponibilidad posterior refleja el turno y no una retención extra, y que la reserva pública aparece en `GET /api/v1/turnos` con `origen="publico"`. Verificación: el archivo completo pasa.
- [x] 6.6 **R9**: agregar un caso que capture `caplog` durante `POST /public/pre-reservas` y `POST /public/reservar` y verifique que no aparecen DNI, teléfono ni nombre completo. Verificación: el test pasa y `ruff check src test` sigue limpio.

## 7. Reprogramación pública

- [x] 7.1 **RED**: crear `backend/test/test_public_reprogramar.py` con: reprogramación exitosa conserva token, sillón, profesional y duración; 409 si choca con otro turno; 409 dentro de la ventana `reprogramacion_min_horas`; 409 con estado `atendido`/`cancelado`/`ausente`/`presente`; 422 con inicio pasado; 422 con `sillon_id`, `profesional_id` o `duracion_min`; 404 con token inexistente. Verificación: el archivo falla.
- [x] 7.2 **GREEN**: crear `ReprogramarPublico` (`inicio` only, `extra="forbid"`) y `PublicReservaService.reprogramar_por_token`, que valida token, estado, futuro y ventana, y delega en `TurnoService.reprogramar` (R6). Verificación: el test de 7.1 pasa.
- [x] 7.3 **GREEN**: montar `POST /api/v1/public/turnos/{token}/reprogramar` en el router público con `response_model=PublicTurnoOut`. Verificación: el test de 7.1 pasa también por HTTP.
- [x] 7.4 **R6 — test de conflicto obligatorio**: agregar un caso explícito de solapamiento contra un turno activo del mismo profesional en otro sillón y otro contra un bloqueo, verificando 409 y que el turno conserva `inicio`/`fin` originales. Verificación: ambos casos pasan y el mensaje distingue sillón, profesional y bloqueo.
- [x] 7.5 **TRIANGULATE**: agregar reprogramación a un hueco que deja libre el horario anterior (la disponibilidad vuelve a ofrecer el slot original), reprogramación al mismo horario (200 sin cambios) y reprogramación con la retención de otro paciente en el destino (409). Verificación: el archivo completo pasa.

## 8. Rate-limit local

- [x] 8.1 **RED**: crear `backend/test/test_rate_limit.py` (puro) con: admite hasta el máximo, rechaza el siguiente, `retry_after` en segundos > 0, la ventana se reinicia al avanzar el reloj (reloj inyectable), buckets independientes y claves distintas no se contaminan. Verificación: el archivo falla.
- [x] 8.2 **GREEN**: crear `backend/src/app/core/rate_limit.py` con `RateLimiter` (deque + `Lock` + reloj inyectable) y `limitar_publico(bucket)` como dependencia FastAPI; agregar `429: "rate_limited"` a `_STATUS_TO_CODE` en `core/errors.py`. Verificación: el test de 8.1 pasa.
- [x] 8.3 **GREEN**: aplicar la dependencia a `GET /public/disponibilidad`, `GET /public/qr/*`, `POST /public/pre-reservas`, `POST /public/reservar`, `POST /public/turnos/{token}/cancelar` y `POST /public/turnos/{token}/reprogramar`. Verificación: `python -m pytest test/test_public_router.py test/test_public_pre_reserva_router.py test/test_public_reprogramar.py -q` sigue en verde con `rate_limit_enabled=false`.
- [x] 8.4 **RED**: crear `backend/test/test_rate_limit_router.py` con: N+1 escrituras → 429 con `Retry-After` y `code="rate_limited"`, lecturas de la misma IP siguen en 200, `GET /api/v1/turnos` con JWT no se limita aunque la IP esté agotada, y el 429 no revela si un token existe. Verificación: los casos fallan.
- [x] 8.5 **GREEN**: ajustar la dependencia para leer la IP de `request.client.host` (sin `X-Forwarded-For`) y devolver `Retry-After` como entero en segundos. Verificación: el test de 8.4 pasa.
- [x] 8.6 **TRIANGULATE**: agregar que el límite se puede desactivar por setting y que el bucket de escritura no consume cupo del de lectura. Verificación: el archivo completo pasa y `ruff check src test` limpio.

## 9. QR local

- [x] 9.1 **DEPENDENCIA**: agregar `segno>=1.6` a `backend/pyproject.toml` e instalarla; verificar que no arrastra dependencias transitivas. Verificación: `python -c "import segno, importlib.metadata as m; print(m.requires('segno'))"` no muestra dependencias obligatorias y `pip install -e ".[dev]"` termina en 0.
- [x] 9.2 **RED**: crear `backend/test/test_qr_service.py` (puro) con: `url_reserva(base)` y `url_turno(base, token)` construyen las URLs esperadas; `svg_qr(url)` devuelve un SVG con `<svg`, `viewBox` y al menos un `path`; el mismo input produce el mismo SVG (determinista); el SVG no contiene DNI ni nombre. Verificación: el archivo falla.
- [x] 9.3 **GREEN**: crear `backend/src/app/modules/public/qr.py` con los helpers puros y el wrapper de `segno`. Verificación: el test de 9.2 pasa.
- [x] 9.4 **RED**: crear `backend/test/test_qr_router.py` con: `GET /public/qr/reserva.svg` → 200 + `image/svg+xml` + cuerpo no vacío; `GET /public/turnos/{token}/qr.svg` → 200 para token existente; token inexistente → 404; el QR del turno se sirve con `Cache-Control: no-store`; y un caso que parchea `socket.socket` para fallar y verifica que la generación no abre conexiones. Verificación: los casos fallan.
- [x] 9.5 **GREEN**: montar ambos endpoints en el router público devolviendo `Response(media_type="image/svg+xml")`. Verificación: el test de 9.4 pasa.
- [x] 9.6 **TRIANGULATE**: agregar que la URL del QR respeta `public_base_url` configurado (sin barra duplicada) y que un `public_base_url` con path base (`https://dominio/portal`) se conserva. Verificación: el archivo completo pasa y `ruff check src test` limpio.

## 10. Frontend: cliente API y helpers puros

- [x] 10.1 **RED**: crear `frontend/test/preReserva.test.ts` con `segundosRestantes(expiraEn, ahoraMs)` (positivo, cero, negativo → 0), `formatearCuentaRegresiva` (`09:59`, `00:05`, `00:00`) y `retencionVencida(expiraEn, ahoraMs)`. Agregar el archivo al script `test` de `frontend/package.json`. Verificación: `npm test` falla por módulo inexistente.
- [x] 10.2 **GREEN**: crear `frontend/src/features/reserva-publica/retencion.ts` con las tres funciones puras y tipos exportados. Verificación: el test de 10.1 pasa.
- [x] 10.3 **RED**: crear `frontend/test/rateLimit.test.ts` con `parseRetryAfter("12") === 12`, `parseRetryAfter(null) === null`, `parseRetryAfter("no-numero") === null` y `mensajeRateLimit(12)` en español rioplatense. Verificación: `npm test` falla.
- [x] 10.4 **GREEN**: crear `frontend/src/shared/rateLimit.ts` y extender `ApiError` en `frontend/src/shared/api/client.ts` con `retryAfterSegundos: number | null` leído de la cabecera. Verificación: el test de 10.3 pasa y `npx tsc --noEmit` en 0.
- [x] 10.5 **RED**: crear `frontend/test/publicApi.test.ts` con `rutaQrReserva()` y `rutaQrTurno(token)` (sin query string, token solo en path), y `construirPreReserva` (payload sin datos de paciente). Verificación: `npm test` falla.
- [x] 10.6 **GREEN**: agregar a `frontend/src/shared/api/public.ts` `crearPreReserva`, `reprogramarTurnoPublico`, `getDisponibilidad` reutilizable y los tipos `PreReservaOut`/`ReprogramarPublicoInput`, usando las rutas puras. Verificación: el test de 10.5 pasa.
- [x] 10.7 **REFACTOR**: sin `any`, `camelCase` en utilidades, `PascalCase` en componentes; `npm run lint` y `npx tsc --noEmit`. Verificación: ambos comandos en 0.

## 11. Frontend: retención, QR y reprogramación

- [x] 11.1 **GREEN**: en `ReservarWizard`, al entrar al paso 4 llamar `crearPreReserva` con el slot elegido y guardar `pre_reserva_token` + `expira_en`; enviar el token en `reservar`. Verificación: Playwright muestra una request a `/public/pre-reservas` al abrir el paso 4 y el payload de `/public/reservar` incluye `pre_reserva_token`.
- [x] 11.2 Crear `CuentaRegresiva.tsx` con `aria-live="polite"`, cuenta descendente de 1 s y limpieza del intervalo al desmontar; deshabilitar el envío en 0 y mostrar "Se liberó el horario" con CTA "Elegir otro horario" que vuelve al paso 3. Verificación: Playwright con TTL corto muestra la cuenta, llega a 0, deshabilita el envío y el CTA vuelve al paso de horario.
- [x] 11.3 Manejar el 409 de retención perdida y el 409 de antisolapamiento en el paso 4 con el mismo camino de recuperación (mensaje + volver al paso 3), sin perder los datos ya cargados del paciente. Verificación: Playwright con una retención consumida por otra pestaña muestra el mensaje y conserva el formulario al volver.
- [x] 11.4 Crear `QrPortal.tsx` (bloque colapsable "Compartí el portal" con `GET /public/qr/reserva.svg`) y `QrTurno.tsx` (QR del turno con leyenda "Mostrá este código en recepción"); incluirlos en `ReservarWizard` y `TurnoPublicoPage`. Verificación: Playwright muestra ambas imágenes con `alt` en español y sin requests fallidas.
- [x] 11.5 Crear `ReprogramarPublicoPage.tsx` con pasos día → horario → confirmación, reusando `getDisponibilidad`; registrar `/p/turno/:token/reprogramar` en `frontend/src/app/router.tsx` y `frontend/src/app/pages.tsx`; al éxito navegar a `/p/turno/:token` con `replace`. Verificación: Playwright completa una reprogramación y vuelve a la confirmación con el nuevo horario; la URL nunca lleva el token en query string.
- [x] 11.6 Agregar el botón "Reprogramar" en `TurnoPublicoPage` solo para estados `reservado`/`confirmado` (la UI solo oculta; el backend manda, R8). Verificación: Playwright confirma que el botón no aparece en `cancelado`, `atendido` ni `ausente`.
- [x] 11.7 Mostrar los estados 409/422/429 con el bloque `role="alert"` existente y el mensaje de `mensajeRateLimit` cuando corresponda. Verificación: Playwright con 429 simulado muestra los segundos de espera; con 404 muestra "No encontramos tu turno".
- [x] 11.8 **ACCESIBILIDAD Y R10**: textos en español rioplatense, foco visible, controles de al menos 44 px, contraste de la cuenta regresiva en alerta y navegación por teclado del flujo de reprogramación. Verificación: recorrido con Tab/Enter en Playwright y revisión visual contra `mockups/previews/`.
- [x] 11.9 `npm test; npm run lint; npx tsc --noEmit; npm run build`. Verificación: los cuatro comandos en 0.

## 12. Integración y verificación

- [x] 12.1 `cd backend; alembic upgrade head; python -m app.db.seed; python -m pytest -q` dos veces consecutivas. Verificación: ambas corridas en verde y sin datos residuales entre tests.
- [x] 12.2 `cd backend; python -m pytest -m "not integration" -q; ruff check src test`. Verificación: suite rápida en verde y `ruff` sin hallazgos.
- [x] 12.3 Playwright: `/reservar` (con retención activa, vencida y QR), `/p/turno/:token` (con QR y reprogramar) y `/p/turno/:token/reprogramar` en 390×844 y 1440×900; revisar consola y requests fallidas; guardar capturas en `mockups/verify/`. Verificación: sin errores de consola ni 4xx/5xx inesperadas, y capturas adjuntas al resumen del apply.
- [x] 12.4 Comparar cada pantalla con `mockups/previews/` y registrar `Visual verify: passed | differences` en `design.md` con las diferencias por prioridad. Verificación: el campo queda actualizado y las diferencias tienen pantalla, viewport y reproducción.
- [x] 12.5 `openspec validate "c-10-reserva-publica-avanzada" --strict` y `openspec validate --all`. Verificación: ambos comandos terminan en 0.
- [x] 12.6 Pasar `business-rule-coverage-auditor` sobre este change. Verificación: matriz con RN-AG-01, RN-AG-05, RN-AG-06, R1, R2, R6, R8, R9, R10 y R13 en ✅, y la propuesta de `RN-AG-07` registrada como pregunta abierta (no como regla vigente).

## Workflow follow-up

- Aprobar los mockups de `mockups/` (revisión 1 del design system) y actualizar `Approval`, `Preview` y `Visual verify` en `design.md` antes de aplicar UI.
- Confirmar con el grupo la redacción de `RN-AG-07` propuesta en `design.md` §Open Questions; si no se crea, corregir la cita en `CHANGES.md`.
- Registrar el desfase KB↔CHANGES de `RN-AG-09` y `RN-CJ-04/05` como deuda documental del proyecto.
- Archivar con `openspec archive "c-10-reserva-publica-avanzada" -y` y marcar `C-10` como `[x]` en `CHANGES.md`.
- Continuar con C-11 (ficha clínica avanzada) o C-15/C-18 según el orden acordado.
