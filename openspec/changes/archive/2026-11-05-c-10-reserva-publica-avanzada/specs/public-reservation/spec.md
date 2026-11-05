# Spec Delta — public-reservation

## MODIFIED Requirements

### Requirement: Endpoints públicos sin autenticación

El sistema SHALL exponer bajo `/api/v1/public/*` los endpoints `GET /disponibilidad`, `POST /pre-reservas`, `POST /reservar`, `GET /turnos/{token}`, `POST /turnos/{token}/cancelar`, `POST /turnos/{token}/reprogramar`, `GET /qr/reserva.svg` y `GET /turnos/{token}/qr.svg` sin requerir cabecera `Authorization`, y SHALL validar toda entrada con schemas Pydantic `extra="forbid"` (RN-SEG-01, R8).

#### Scenario: Acceso sin token exitoso
- **WHEN** un cliente llama a cualquiera de los endpoints públicos sin token
- **THEN** la API procesa la request y no responde 401

#### Scenario: Campo extra rechazado
- **WHEN** el cuerpo de `POST /reservar` incluye un campo no declarado
- **THEN** la API responde 422

#### Scenario: Acceso acotado por token
- **WHEN** se llama a un endpoint público que recibe `{token}` con un token que no corresponde al recurso
- **THEN** la API responde 404 y no expone ni modifica ningún turno

#### Scenario: Endpoint público nuevo también rechaza campos extra
- **WHEN** el cuerpo de `POST /pre-reservas` o de `POST /turnos/{token}/reprogramar` incluye un campo no declarado
- **THEN** la API responde 422

## ADDED Requirements

### Requirement: Pre-reserva con retención temporal del hueco

El sistema SHALL exponer `POST /api/v1/public/pre-reservas` que retenga un hueco concreto (`prestacion`, `duracion_min`, `inicio`, `profesional_id`, `sillon_id`) durante `pre_reserva_ttl_min` (default 10) y devuelva un `pre_reserva_token` opaco con `expira_en`. La retención SHALL rechazar con 409 un rango no libre y no SHALL pedir datos del paciente.

#### Scenario: Retención exitosa
- **WHEN** se retiene un hueco libre con datos válidos
- **THEN** la API responde 201 con un `pre_reserva_token` no nulo y `expira_en` igual al inicio de la retención más el TTL configurado

#### Scenario: Retención de un hueco ocupado
- **WHEN** se retiene un rango que se solapa con un turno activo, un bloqueo o una retención vigente
- **THEN** la API responde 409 y no crea la retención

#### Scenario: Retención con inicio pasado
- **WHEN** se envía un `inicio` anterior o igual al momento de la request
- **THEN** la API responde 422 y no crea la retención

#### Scenario: Retención sin datos sensibles
- **WHEN** se crea una retención
- **THEN** el token es un identificador opaco y la respuesta no contiene DNI, teléfono ni nombre de paciente

#### Scenario: Duración inválida
- **WHEN** se envía `duracion_min` menor o igual a cero
- **THEN** la API responde 422

### Requirement: Expiración y liberación automática del hueco

Una retención SHALL ocupar el hueco solo mientras su `estado` sea `vigente` y su `expira_en` sea futuro. Al vencer SHALL dejar de ocuparlo sin intervención manual, sin worker externo y sin Redis, y toda confirmación posterior sobre esa retención SHALL responder 409.

#### Scenario: Retención vencida libera el hueco
- **WHEN** una retención supera su `expira_en` y se consulta la disponibilidad de ese rango
- **THEN** el hueco vuelve a ofrecerse como libre

#### Scenario: Confirmación de una retención vencida
- **WHEN** se intenta reservar con un `pre_reserva_token` vencido
- **THEN** la API responde 409 y no crea el turno

#### Scenario: Retención vigente sigue ocupando
- **WHEN** una retención no alcanzó su `expira_en`
- **THEN** el hueco no se ofrece como libre a otro paciente

#### Scenario: Liberación sin proceso de limpieza
- **WHEN** una retención vence y no se ejecutó ningún proceso de limpieza
- **THEN** el hueco ya se ofrece como libre en la siguiente consulta

### Requirement: Reserva confirmada a partir de una pre-reserva

`POST /api/v1/public/reservar` SHALL aceptar `pre_reserva_token` opcional. Con token SHALL exigir que coincidan `inicio`, `profesional_id`, `sillon_id`, `prestacion` y `duracion_min`, crear el turno con `origen = 'publico'` reutilizando el antisolapamiento de servicios y marcar la retención como `consumida` en la misma transacción. Un token vencido, consumido o que no coincida SHALL responder 409.

#### Scenario: Reserva sobre una retención vigente
- **WHEN** se reserva con un `pre_reserva_token` vigente y datos coincidentes
- **THEN** la API responde 201 con el turno en estado `reservado`, la retención queda `consumida` y el hueco sigue ocupado por el turno

#### Scenario: Token de otra franja horaria
- **WHEN** el `inicio`, el sillón o el profesional del payload no coinciden con la retención
- **THEN** la API responde 409 y no crea el turno

#### Scenario: Retención ya consumida
- **WHEN** se reutiliza un `pre_reserva_token` que ya generó un turno
- **THEN** la API responde 409 y no crea un segundo turno

#### Scenario: Reserva sin retención
- **WHEN** se reserva sin `pre_reserva_token` en un hueco libre
- **THEN** la API responde 201 como en C-06

#### Scenario: Retención consumida no bloquea el hueco del turno creado
- **WHEN** una retención se consume y crea su turno
- **THEN** la disponibilidad refleja el turno activo y no una retención adicional

### Requirement: Los huecos retenidos no se ofrecen en la disponibilidad pública

`GET /api/v1/public/disponibilidad` SHALL omitir los huecos que solapan una retención vigente del mismo sillón o del mismo profesional, además de los turnos activos y los bloqueos ya considerados.

#### Scenario: Retención vigente excluye el hueco
- **WHEN** existe una retención vigente para un sillón y profesional en un rango
- **THEN** ningún slot que use ese sillón o ese profesional en ese rango se devuelve

#### Scenario: Retención de otro recurso no excluye
- **WHEN** la retención vigente pertenece a otro sillón y a otro profesional
- **THEN** el slot del hueco consultado se sigue devolviendo

#### Scenario: Retención vencida no excluye
- **WHEN** la retención del rango ya venció
- **THEN** el slot se devuelve como libre

### Requirement: Reprogramación pública por token

El sistema SHALL exponer `POST /api/v1/public/turnos/{token}/reprogramar` con cuerpo `{inicio}` que mueva el turno conservando sillón, profesional, prestación y duración. SHALL aceptar solo estados `reservado` y `confirmado`, exigir `reprogramacion_min_horas` (default 12) de anticipación, reusar el antisolapamiento excluyendo el propio turno (R6) y responder 409 ante conflicto o estado no reprogramable.

#### Scenario: Reprogramación exitosa
- **WHEN** se mueve un turno `reservado` a un hueco libre con la anticipación mínima
- **THEN** la API responde 200 con el nuevo `inicio`/`fin` y el mismo token

#### Scenario: Reprogramación que choca con otro turno
- **WHEN** el nuevo rango se solapa con otro turno activo del mismo sillón o profesional
- **THEN** la API responde 409 y el turno conserva su horario original

#### Scenario: Reprogramación dentro de la ventana mínima
- **WHEN** el turno comienza en menos de `reprogramacion_min_horas`
- **THEN** la API responde 409 y no modifica el turno

#### Scenario: Turno no reprogramable
- **WHEN** se intenta reprogramar un turno en estado `atendido`, `cancelado`, `ausente` o `presente`
- **THEN** la API responde 409

#### Scenario: Nuevo inicio en el pasado
- **WHEN** el `inicio` solicitado es anterior o igual al momento de la request
- **THEN** la API responde 422 y no modifica el turno

#### Scenario: Token inexistente al reprogramar
- **WHEN** se reprograma con un token que no existe
- **THEN** la API responde 404

#### Scenario: La reprogramación no cambia de recurso ni de duración
- **WHEN** el cuerpo incluye `sillon_id`, `profesional_id` o `duracion_min`
- **THEN** la API responde 422

### Requirement: Rate-limit local en las superficies públicas

El sistema SHALL aplicar un límite de requests en memoria por IP y por bucket (lectura: disponibilidad y QR; escritura: pre-reserva, reservar, cancelar y reprogramar), configurable y sin captcha ni servicio externo, respondiendo 429 con `Retry-After` y sin afectar los endpoints internos.

#### Scenario: Exceso de escrituras
- **WHEN** una misma IP supera el máximo de escrituras públicas dentro de la ventana
- **THEN** la API responde 429 con cabecera `Retry-After` y no ejecuta la operación

#### Scenario: Dentro del límite
- **WHEN** una IP no alcanza el máximo de su bucket
- **THEN** la API responde con el resultado normal y no con 429

#### Scenario: La ventana se reinicia
- **WHEN** transcurre la ventana configurada desde las requests que agotaron el límite
- **THEN** la misma IP vuelve a ser admitida

#### Scenario: Buckets independientes
- **WHEN** una IP agota el bucket de escritura
- **THEN** las lecturas públicas de esa IP siguen respondiendo normalmente

#### Scenario: Los endpoints internos no se limitan
- **WHEN** un usuario autenticado opera la agenda interna
- **THEN** el rate-limit público no interviene en la request

#### Scenario: Forma única del error
- **WHEN** la API responde 429
- **THEN** el cuerpo usa la forma `{error:{code,message}}` con código `rate_limited`

### Requirement: Código QR local del portal y del turno

El sistema SHALL generar localmente los QR de `{public_base_url}/reservar` y `{public_base_url}/p/turno/{token}` como SVG en `GET /api/v1/public/qr/reserva.svg` y `GET /api/v1/public/turnos/{token}/qr.svg`, sin llamadas de red ni servicios externos; un token inexistente SHALL responder 404.

#### Scenario: QR del portal
- **WHEN** se solicita `GET /api/v1/public/qr/reserva.svg`
- **THEN** la API responde 200 con `Content-Type: image/svg+xml` y un SVG no vacío que codifica la URL de `/reservar`

#### Scenario: QR de un turno existente
- **WHEN** se solicita el QR de un token existente
- **THEN** la API responde 200 con `image/svg+xml` y el SVG codifica `{public_base_url}/p/turno/{token}`

#### Scenario: QR de un token inexistente
- **WHEN** se solicita el QR de un token que no existe
- **THEN** la API responde 404

#### Scenario: Generación sin red
- **WHEN** se genera un QR con las conexiones de red bloqueadas
- **THEN** la respuesta se produce igual, sin errores ni timeouts

#### Scenario: El QR no filtra datos del paciente
- **WHEN** se genera el QR de un turno
- **THEN** el contenido codificado es solo la URL pública con el token opaco, sin DNI, teléfono ni nombre

### Requirement: Presentación del portal: retención, QR y reprogramación

La SPA SHALL mostrar la cuenta regresiva de la retención en el paso de datos, recuperar el flujo con un mensaje accionable si vence, mostrar el QR del portal en `/reservar` y el del turno en `/p/turno/:token`, ofrecer reprogramación en `/p/turno/:token/reprogramar` y presentar los errores 409 y 429 en español rioplatense (R10).

#### Scenario: Cuenta regresiva de la retención
- **WHEN** el paciente llega al paso de datos con una retención vigente
- **THEN** la SPA muestra el tiempo restante y deshabilita el envío cuando llega a cero

#### Scenario: Retención vencida durante la carga
- **WHEN** la retención vence antes de confirmar
- **THEN** la SPA informa que el horario se liberó y ofrece volver al paso de horario

#### Scenario: QR visible en el portal
- **WHEN** el paciente abre `/reservar` o `/p/turno/:token`
- **THEN** la SPA muestra el QR correspondiente al portal o al turno

#### Scenario: Reprogramación desde la confirmación
- **WHEN** el paciente elige reprogramar y confirma un hueco libre
- **THEN** la SPA vuelve a `/p/turno/:token` con el nuevo horario

#### Scenario: Conflicto al reprogramar
- **WHEN** el backend responde 409 durante la reprogramación
- **THEN** la SPA permanece en la pantalla con un mensaje que explica el conflicto

#### Scenario: Rate-limit en el portal
- **WHEN** el backend responde 429
- **THEN** la SPA muestra un mensaje de espera con los segundos indicados por `Retry-After`
