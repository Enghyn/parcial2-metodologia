# Design — C-10 reserva-publica-avanzada

## Context

Ver `proposal.md` — Why. Estado real del repo al momento de este propose:

- **Portal (C-06)**: `modules/public/{router,schemas,service}.py` expone `GET /public/profesionales`, `GET /public/disponibilidad`, `POST /public/reservar`, `GET /public/turnos/{token}` y `POST /public/turnos/{token}/cancelar`. `PublicReservaService` reusa `TurnoService.crear` (R6) y ya aplica la ventana `cancelacion_min_horas` (default 12) sobre `turno.inicio`.
- **Disponibilidad**: `generar_inicios` (puro) + `slot_libre` (puro) recorren profesionales × grilla × sillones y descartan turnos activos y bloqueos. `SlotOut` no expone capacidad sobrante: devuelve un slot por (inicio, profesional) con el primer sillón libre.
- **Agenda (C-09a/C-09b)**: `TurnoService.reprogramar` valida estados `reservado`/`confirmado`, recalcula `fin`, excluye el propio turno del solapamiento y responde 409 por sillón, profesional o bloqueo. `Turno` no tiene `origen`. Última migración: `0005_agenda_indice_inicio`.
- **Token público**: `Turno.token_publico` es `UUID` con `gen_random_uuid()` y unique; las rutas públicas ya lo usan en el path (`/public/turnos/{token}`) y `/p/turno/:token`. Es el precedente aceptado de "token opaco en URL".
- **Errores**: forma única `{error:{code,message,details?}}`; `_STATUS_TO_CODE` no mapea 429. `CorrelationIdMiddleware` y headers de seguridad ya existen.
- **Config**: `Settings` (pydantic-settings) ya tiene `public_slot_start/end/grid_min` y `cancelacion_min_horas`.
- **Frontend**: `ReservarWizard` (4 pasos, estado local, `reservar()` sin retención), `TurnoPublicoPage` (detalle + WhatsApp + cancelar), `shared/api/client.ts` con `ApiError(status, code, message)` y sin `Retry-After`. Tests de frontend son `node:test` puros (sin DOM).
- **Sin librería de QR** en backend ni frontend. `pyproject.toml` no incluye generador de QR.

## Goals / Non-Goals

**Goals:**

- Que elegir un horario lo reserve de hecho por unos minutos, sin convertirlo en un turno ni tocar la máquina de estados de RN-AG-05.
- Que la autogestión pública (cancelar y reprogramar) use exactamente la misma validación de antisolapamiento que la agenda interna (R6), sin duplicar la fórmula.
- Que el portal tenga defensas básicas de abuso y llegada (rate-limit y QR) sin captcha, sin servicio externo y sin Redis.
- Cambios de esquema aditivos, reversibles y con default, sin `tenant_id` (R2) y sin borrado físico (R13).
- Mantener compatibilidad total con el contrato de C-06 y con los consumidores actuales.

**Non-Goals:**

- Cambiar sillón, profesional o duración desde el portal (solo se mueve el horario).
- Reprogramar sobreturnos, turnos `presente`/`atendido`/`ausente`/`cancelado`.
- Pago de señas, presupuestos o notificaciones (C-16/C-17/C-14).
- Persistir el rate-limit entre procesos o sobrevivir a un reinicio.
- Captcha, WAF, CDN o `slowapi`/`limits`.
- QR de presupuestos ni cartelería imprimible desde la agenda interna (C-18).
- Tests de componentes React con DOM (el harness no los tiene).

## Decisions

### D1 — La pre-reserva es una entidad propia, no un estado del turno

Se crea la tabla `pre_reservas` (retención) con `id`, `token` (UUID unique), `sillon_id`, `profesional_id`, `prestacion`, `inicio`, `fin`, `duracion_min`, `expira_en`, `estado` (`vigente`|`consumida`|`expirada`|`cancelada`), `turno_id` (FK nullable y unique a `turnos.id`) y `created_at`/`updated_at`.

- **Por qué**: una retención no es una cita: no tiene paciente, no tiene estado clínico, no se atiende ni se cobra. Modelarla como `Turno.estado='pre_reserva'` obligaría a ampliar el `CHECK` de estados y el catálogo de RN-AG-05, a filtrar el séptimo estado en agenda, caja, reportes y tests, y a inventar transiciones que la KB no define. La tabla aparte deja `Turno` intacto.
- **Alternativas descartadas**: (a) séptimo estado `pre_reserva` en `turnos` — rompe RN-AG-05 y ensucia todos los consumidores; (b) turno `reservado` con `expira_en` y borrado lógico al vencer — usa R13 para algo que no es una baja de negocio y ensucia la agenda con filas fantasma; (c) no retener y solo mostrar el 409 al final — es el problema actual.
- **No borrado físico**: `pre_reservas` no hereda `SoftDeleteMixin` (R13 nombra Paciente/Turno/Profesional/Sillón), pero la aplicación **nunca** hace `DELETE`: los estados cubren el ciclo completo. El test de estructura verifica que no haya `delete()` sobre la tabla.
- **Sin FK circular**: la relación se guarda solo en `pre_reservas.turno_id`. No se agrega `turnos.pre_reserva_id`, que obligaría a `use_alter` en Alembic.

### D2 — Token de retención opaco y confirmación en una sola transacción

`pre_reservas.token` es un `UUID` generado por la base (`gen_random_uuid()`), sin relación con DNI, nombre, teléfono ni con el horario. La confirmación (`POST /public/reservar` con `pre_reserva_token`) valida en este orden: token existente → `estado='vigente'` → `expira_en > ahora()` → coincidencia exacta de `inicio`, `profesional_id`, `sillon_id`, `prestacion` y `duracion_min` → `TurnoService.crear`. Todo en la misma sesión/transacción: si `crear` falla (409 por antisolapamiento), la retención **no** se consume.

- **Por qué**: R9 exige tokens opacos y prohíbe datos sensibles en URLs. Reusar el patrón `token_publico` mantiene una sola convención y permite invalidar la retención con un `UPDATE` de estado.
- **Alternativa descartada**: token firmado (JWT corto) — agrega secreto, rotación y un modo de fallo nuevo sin beneficio académico; además un JWT típico filtra `exp` y claims en la URL.
- **Código HTTP**: 409 para vencida, consumida o no coincidente; **no** 410. `_STATUS_TO_CODE` no mapea 410 y agregar un estado nuevo al contrato de errores por un caso que 409 describe bien es deuda innecesaria.

### D3 — Las retenciones son asesorativas: la agenda interna siempre gana

`TurnoService.detectar_conflicto` **no cambia**: sigue considerando solo turnos activos y bloqueos. Una pre-reserva vigente **no** impide que recepción cree un turno en ese hueco; si eso pasa, la confirmación del paciente falla con 409 y la SPA lo devuelve al paso de horario.

- **Por qué**: el mostrador tiene prioridad operativa sobre un paciente anónimo que abandonó el formulario. Además evita tocar la validación de RN-AG-01 (R6) y su suite de conflictos, que es el activo más sensible de C-04/C-09a.
- **Alternativa descartada**: sumar retenciones a `detectar_conflicto` — acopla la agenda interna a una tabla efímera del portal y obliga a revisar todos los tests de antisolapamiento.
- **Consecuencia asumida**: una retención puede "perder" su hueco. Es exactamente el mismo 409 que el paciente ya conoce, con mejor momento para comunicarlo.

### D4 — Expiración perezosa, sin job ni Redis

La vigencia se evalúa en consulta (`estado='vigente' AND expira_en > now()`). No hay scheduler: un `BackgroundTasks` opcional, disparado al crear una retención, marca `expirada` las retenciones vencidas del mismo recurso (higiene de datos, no corrección funcional).

- **Por qué**: la liberación del hueco es una condición de lectura, no un evento. Con 2–3 sillones y TTL de minutos, el volumen de filas es trivial.
- **Alternativa descartada**: RQ/Redis o `pg_cron` — la KB y CHANGES lo excluyen explícitamente; además agrega un modo de fallo (worker caído) para un comportamiento que debe ser correcto igual.
- **Reloj**: se usa `app.core.timezone.ahora()` (ART) para comparar con columnas `timestamptz`; la comparación es absoluta, así que no hay ambigüedad de zona.

### D5 — La disponibilidad pública descuenta retenciones vigentes

`PublicReservaService.disponibilidad` carga las retenciones vigentes del día que solapan la jornada y las pasa a `slot_libre` (que gana un parámetro `retenciones: Iterable[PreReserva] = ()`). El helper sigue siendo puro y testeable sin DB.

- **Por qué**: es el punto donde el paciente percibe la retención. Sin esto, dos pestañas ofrecen el mismo horario y la retención no sirve para nada.
- **Alternativa descartada**: filtrar en el frontend — no hay forma de saber qué está retenido sin exponerlo, y sería una carrera entre pestañas.
- **Privacidad**: el slot no expone el token ni la identidad de quien retuvo; solo desaparece de la lista.

### D6 — Reprogramación pública delega en `TurnoService.reprogramar`

`POST /public/turnos/{token}/reprogramar` acepta solo `{inicio}`. El servicio público valida token, estado (`reservado`/`confirmado`), `inicio` futuro y la ventana `reprogramacion_min_horas` (default 12) medida contra el `inicio` actual; luego llama a `TurnoService.reprogramar(turno.id, ReprogramarTurno(inicio=...))`, que hace el antisolapamiento excluyendo el propio turno y responde 409.

- **Por qué**: R6 exige una sola implementación de antisolapamiento; duplicar la consulta de solapamiento en el módulo público crearía dos verdades.
- **Alternativa descartada**: copiar la lógica en `PublicReservaService` — duplica la fórmula y el mensaje de error.
- **Sin cambio de recurso ni duración**: el cuerpo con `sillon_id`, `profesional_id` o `duracion_min` responde 422 por `extra="forbid"` (R1). Mover a otro sillón/profesional es una decisión operativa de recepción, no del paciente.
- **Ventana propia**: `reprogramacion_min_horas` separada de `cancelacion_min_horas` porque cancelar y reprogramar tienen costos operativos distintos; ambas quedan configurables y con el mismo default 12 para no sorprender.

### D7 — QR generado en el backend con una dependencia pura

Se agrega `segno>=1.6` (Python puro, sin Pillow, salida SVG) y dos endpoints que devuelven `image/svg+xml`:

- `GET /api/v1/public/qr/reserva.svg` → `{public_base_url}/reservar`.
- `GET /api/v1/public/turnos/{token}/qr.svg` → `{public_base_url}/p/turno/{token}`; 404 si el token no existe.

`public_base_url` es una setting nueva (default `http://localhost:5173`). El QR del turno se sirve con `Cache-Control: no-store`; el del portal puede cachearse. La generación no hace red: se testea con `socket.socket` parcheado para fallar si algo intenta conectarse.

- **Por qué**: un solo generador para el QR del portal (cartel/mostrador) y el del turno (confirmación), sin JS extra en la SPA y sin depender del navegador del paciente.
- **Alternativas descartadas**: (a) `qrcode` + Pillow — dependencia pesada y salida raster para un caso donde SVG alcanza; (b) `qrcode.react` en el frontend — obliga a un bundle nuevo y no sirve para un cartel impreso servido por la API; (c) encoder propio — cientos de líneas de corrección de errores Reed-Solomon, riesgo alto sin beneficio; (d) servicio externo de QR — viola "sin integraciones externas".
- **Test de contenido**: golden test del SVG para una URL fija (determinista) + asserts de `<svg`, `viewBox` y módulos no vacíos; no se intenta decodificar la imagen en el test.

### D8 — Rate-limit en memoria por IP y bucket

`app/core/rate_limit.py` implementa `RateLimiter` (ventana deslizante con `deque` de timestamps y `threading.Lock`) y una dependencia `limitar_publico(bucket)` que se aplica por endpoint. Buckets: `lectura` (disponibilidad, QR) y `escritura` (pre-reservas, reservar, cancelar, reprogramar). Clave: `bucket + IP del socket` (`request.client.host`), **sin** confiar en `X-Forwarded-For` por defecto. Al exceder: 429 con `Retry-After` (segundos hasta liberar el cupo) y `{error:{code:"rate_limited",message:...}}`.

Settings nuevas: `rate_limit_public_window_s` (60), `rate_limit_public_read_max` (120), `rate_limit_public_write_max` (10), `rate_limit_enabled` (true; false en tests de integración que hacen ráfagas legítimas).

- **Por qué**: "local" en CHANGES significa exactamente esto: sin Redis ni captcha. La dependencia por endpoint es explícita, testeable y no intercepta rutas internas (R8 no se toca).
- **Alternativas descartadas**: (a) `slowapi`/`limits` — agrega dependencia y una capa de configuración para 40 líneas de lógica; (b) Redis — excluido por CHANGES; (c) middleware global por path — más difícil de testear y de excluir; (d) captcha — descartado por requisito.
- **`_STATUS_TO_CODE`**: se agrega `429: "rate_limited"` para mantener la forma única de error.
- **Limitación declarada**: el contador vive en el proceso; con varios workers el límite efectivo se multiplica. Se documenta y se deja la interfaz lista para un backend compartido (misma firma).
- **Logs**: se registra bucket y cantidad, nunca la IP junto a datos del paciente (R9).

### D9 — `turnos.origen` como columna aditiva con default

`Turno.origen` (`String(20)`, `NOT NULL`, `server_default='interno'`, `CHECK origen IN ('interno','publico')`) y `TurnoOut.origen`. `TurnoService.crear` y `crear_sobreturno` ganan un parámetro keyword-only `origen: str = "interno"`; el portal pasa `"publico"`. `TurnoCreate` **no** expone `origen`, así un cliente interno no puede falsificarlo (el test lo cubre con 422 por `extra="forbid"`).

- **Por qué**: sin esto no se puede distinguir una reserva autogestionada de una cargada por recepción, dato que C-18/C-21 necesitan para el portal y los reportes.
- **Alternativa descartada**: inferir el origen por `pre_reserva_id` — las reservas de C-06 no tienen retención y quedarían sin origen.
- **Backfill**: las filas existentes quedan `interno` porque no hay forma determinista de saber cuáles vinieron del portal. Se acepta y se documenta (datos de demo, no producción).

### D10 — Migración `0006_pre_reserva_origen`

`down_revision = "0005_agenda_indice_inicio"`.

1. `create_table("pre_reservas")` con PK UUID, `token` unique, FKs a `sillones`, `profesionales` y `turnos` (nullable, unique), `expira_en`, `estado` con `CHECK`, `CHECK` de rango y de coherencia `fin = inicio + duracion_min`, `created_at`/`updated_at` con `server_default=now()`.
2. Índices `ix_pre_reservas_sillon_inicio_fin`, `ix_pre_reservas_profesional_inicio_fin`, `ix_pre_reservas_expira_en`.
3. `add_column("turnos", "origen")` con `server_default='interno'`, `nullable=False` + `CHECK ck_turnos_origen`.
4. `downgrade`: `drop_constraint` del CHECK, `drop_column` de `origen`, `drop_table` de `pre_reservas` (los índices caen con la tabla).

- **Por qué**: todo aditivo y reversible; no se reescriben tablas ni se tocan constraints existentes. `server_default` evita un `UPDATE` de backfill y hace el `ALTER` seguro con filas vivas.
- **Registro**: `db/registry.py` suma `from app.modules.public import models as _public_models`; `test_models_structure.py` y `test_migrations.py` se actualizan al inventario nuevo (diez tablas).
- **Seed**: no crea retenciones; `python -m app.db.seed` sigue siendo idempotente.

### D11 — Configuración nueva (sin secretos)

| Setting | Default | Uso |
|---|---|---|
| `public_base_url` | `http://localhost:5173` | URL absoluta que codifica el QR |
| `pre_reserva_ttl_min` | `10` | Vigencia de la retención |
| `reprogramacion_min_horas` | `12` | Ventana mínima de autogestión |
| `rate_limit_enabled` | `true` | Interruptor para tests/suite |
| `rate_limit_public_window_s` | `60` | Ventana deslizante |
| `rate_limit_public_read_max` | `120` | Máximo de lecturas por ventana |
| `rate_limit_public_write_max` | `10` | Máximo de escrituras por ventana |

Todas con `Field(...)` y validación (`gt=0` donde corresponde). Se documentan en `.env.example` (sin valores sensibles).

### D12 — Frontend: retención visible, QR y reprogramación

- **Wizard**: al entrar al paso 4 se llama `crearPreReserva`; se guarda `pre_reserva_token` + `expira_en`. Un helper puro `segundosRestantes(expiraEn, ahoraMs)` alimenta la cuenta regresiva (un `setInterval` de 1 s que se limpia al desmontar). Al llegar a 0 se deshabilita el envío y se muestra "Se liberó el horario" con acción "Elegir otro horario" (vuelve al paso 3). Si `reservar` responde 409 por retención perdida, mismo camino.
- **Página de reprogramación**: `/p/turno/:token/reprogramar` (token en path, nunca en query — R9) con los pasos día → horario → confirmación, reusando `getDisponibilidad`. Al confirmar, `reprogramarTurnoPublico` y `navigate('/p/turno/:token', { replace: true })`.
- **QR**: `/reservar` muestra un bloque colapsable "Compartí el portal" con `GET /public/qr/reserva.svg`; `/p/turno/:token` muestra el QR del turno con la leyenda "Mostrá este código en recepción".
- **Errores**: `ApiError` gana `retryAfterSegundos: number | null` leído de `Retry-After`. Un helper puro `mensajeRateLimit(segundos)` arma el texto es-AR. Los estados 409/422/429 se renderizan con el mismo bloque `role="alert"` que ya usa el portal.
- **Por qué**: la retención sin cuenta regresiva es invisible y el paciente no entiende el 409; el token en query rompería R9 y ensuciaría logs/historial.
- **Alternativa descartada**: modal de reprogramación en la misma página — el wizard de disponibilidad ya existe como flujo de pasos y un modal con selector de fecha duplicaría estado.

### D13 — Seguridad, RBAC y privacidad

- Las rutas nuevas siguen siendo públicas por diseño (R8: excepción explícita) pero **acotadas por token**: sin token válido → 404, nunca 403 con existencia del recurso.
- No se agrega ningún endpoint interno nuevo: la agenda no gana acciones ni permisos.
- El token no se loguea completo en logs de aplicación (solo prefijo corto si hace falta correlacionar) y nunca se agrega a la query string.
- La respuesta de pre-reserva no incluye datos del paciente porque no los pide.
- Los 429 no revelan si un token existe.

### D14 — Compatibilidad y errores

- `POST /public/reservar` sin `pre_reserva_token` se comporta exactamente como C-06 (test de regresión).
- `GET /public/disponibilidad` conserva su forma (`SlotOut`); solo puede devolver menos slots.
- `TurnoOut` suma un campo; los consumidores que validan estrictamente el JSON de respuesta no existen en el repo (el frontend tipa la interfaz).
- Códigos: 201 (retención y reserva), 200 (reprogramación), 404 (token inexistente), 409 (conflicto, retención vencida/consumida, ventana, estado), 422 (validación/`extra`), 429 (rate-limit).

## Risks / Trade-offs

- **Rate-limit por proceso** → con N workers el límite real es N × configurado. Mitigación: límites configurables y documentados; la interfaz `RateLimiter` permite un backend compartido sin cambiar endpoints ni specs.
- **IP compartida (Wi-Fi del consultorio o NAT móvil)** → una ráfaga legítima de varios pacientes puede tocar el techo de escritura. Mitigación: `rate_limit_public_write_max` default 10/min por IP, configurable; los tests de integración lo apagan con `rate_limit_enabled=false`.
- **Retenciones huérfanas** → filas `vigente` vencidas que nadie marca. Mitigación: no afectan la corrección (se filtran por `expira_en`), el `BackgroundTasks` de higiene las marca y existe índice por `expira_en` para una limpieza futura.
- **Carrera retención → turno** → entre retener y confirmar, recepción puede ocupar el hueco. Mitigación: el antisolapamiento sigue siendo la verdad (R6); el 409 se comunica en el paso de datos y no se consume la retención.
- **Backfill de `origen`** → los turnos públicos históricos quedan como `interno`. Aceptado: son datos de demo; se documenta en `design.md` y no se inventa una heurística.
- **`segno` como dependencia nueva** → suma superficie de supply chain. Mitigación: librería pura, MIT, sin dependencias transitivas ni red; el test de "sin red" verifica que la generación es local.
- **Dos relojes (cliente y servidor)** → la cuenta regresiva del navegador puede adelantarse o atrasarse. Mitigación: el servidor es la autoridad (409); la UI solo anticipa el estado y ofrece reintento.
- **Sin tests de DOM** → los estados visuales de retención/QR/reprogramación se validan con tests puros de helpers + `tsc`/`eslint`/`build` + Playwright manual. Limitación del harness, no del change.
- **RN-AG-07 inexistente** → `CHANGES.md` la cita y la KB solo llega a `RN-AG-06`. Mitigación: no se cita como regla vigente; se propone la redacción en §Open Questions y se especifica el comportamiento en los delta specs. **Requiere confirmación del grupo antes de archivar.**
- **Discrepancia sistémica de KB** → el mismo patrón aparece con `RN-AG-09` (C-15) y `RN-CJ-04/05` (C-12/C-13a), que tampoco existen en `05_reglas_de_negocio.md`. Mitigación: registrar el desfase KB↔CHANGES como riesgo transversal para el grupo; este change no lo corrige.

## Migration Plan

1. `cd backend && alembic upgrade head` aplica `0006_pre_reserva_origen` (tabla + columnas).
2. Verificar con `\d pre_reservas`, `\d turnos` y `alembic current` → `0006_pre_reserva_origen`.
3. Reversión: `alembic downgrade 0005_agenda_indice_inicio` elimina la tabla y las columnas sin tocar turnos existentes (el `CHECK` se elimina antes que la columna).
4. Rollback de aplicación: un backend anterior ignora `pre_reservas` y la columna `origen` (con default), y sigue sirviendo el contrato de C-06; el frontend nuevo tolera que los endpoints de retención/QR no existan solo si se despliega desacoplado — por eso el orden es **backend primero, frontend después**.
5. Datos: no hay backfill ni migración de datos; el seed no crea retenciones.
6. Verificación: `pytest -m "not integration" -q`, luego `alembic upgrade head` + `python -m app.db.seed` + `pytest -q` dos veces; `ruff check src test`; `npm test`, `npm run lint`, `npx tsc --noEmit`, `npm run build`.

## UI Mockups

- Design system revision: 1
- Decision: yes (project policy)
- Mockups: openspec/changes/c-10-reserva-publica-avanzada/mockups/
- Approval: approved (2026-11-05, by user)
- Preview: rendered (2026-11-05, mockups/previews/*-390x844.png y *-1440x900.png)
- Visual verify: passed (2026-11-05, capturas E2E en mockups/verify/*-390x844.png y *-1440x900.png; sin errores de consola ni requests fallidas)

### Pantallas y estados que necesitan mockup

Todos reutilizan `design-system/tokens.css`, `brand.js` y `assets/logo.svg` (revisión 1 aprobada); no se introducen colores literales ni fuentes remotas.

1. **`reserva-retencion.html`** — `/reservar`, paso 4 "Datos del paciente" con la retención activa.
   - Estados: cuenta regresiva normal (≥ 5 min), cuenta regresiva en alerta (< 2 min), retención vencida (envío deshabilitado + CTA "Elegir otro horario").
   - Variantes: mobile 390×844 y desktop 1440×900.
2. **`reserva-qr.html`** — bloque "Compartí el portal" con el QR de `/reservar`.
   - Estados: colapsado (por defecto), expandido con QR y texto de ayuda, error de carga del QR con fallback textual a la URL.
   - Variantes: mobile y desktop.
3. **`turno-publico.html`** — `/p/turno/:token` con QR del turno y acción "Reprogramar".
   - Estados: turno `reservado`, turno `confirmado`, turno `cancelado` (sin acciones), QR visible con leyenda "Mostrá este código en recepción".
   - Variantes: mobile y desktop.
4. **`reprogramar.html`** — `/p/turno/:token/reprogramar`.
   - Estados: selección de día, selección de horario (slot elegido), confirmación con resumen, éxito (redirige a la confirmación).
   - Variantes: mobile y desktop.
5. **`errores-publicos.html`** — estados de error compartidos.
   - Estados: 409 conflicto al reprogramar, 409 retención perdida, 429 rate-limit con segundos de `Retry-After`, 404 token inexistente.
   - Variantes: mobile y desktop.

Criterio de aceptación visual: los cinco HTML se renderizan a 390×844 y 1440×900, sin scroll horizontal de página, con foco visible, controles de al menos 44 px de alto y textos en español rioplatense (R10). Ningún mockup se considera aprobado hasta que el usuario lo confirme.

## Open Questions

1. **Redacción de la regla faltante (`RN-AG-07`)** — la KB no la define. Propuesta para que el grupo confirme o reemplace:
   > **RN-AG-07 (Pre-reserva y autogestión pública):** una pre-reserva retiene un hueco concreto por un TTL configurable (default 10 min) y lo libera automáticamente al vencer, sin crear un turno. La confirmación exige que el token siga vigente y que el horario coincida. El paciente puede reprogramar su turno por token solo si está `reservado` o `confirmado` y con al menos `reprogramacion_min_horas` de anticipación (default 12), reutilizando la validación de antisolapamiento de RN-AG-01.
   
   Si el grupo prefiere no crear la regla, alcanza con `RN-AG-06` + la ventana de cancelación de C-09a y este change queda como está, pero `CHANGES.md` debería dejar de citar `RN-AG-07`.
2. **¿El TTL de 10 min es el correcto para el consultorio?** Se deja configurable; cambiarlo no altera specs ni tareas.
3. **¿La reprogramación pública debe permitir cambiar de profesional si el paciente lo pide?** Hoy no (D6). Habilitarlo es un cambio de contrato y merece su propio change.
4. **¿El QR del portal debe imprimirse desde la agenda interna?** Queda para C-18; este change solo expone el SVG y lo muestra en `/reservar`.
