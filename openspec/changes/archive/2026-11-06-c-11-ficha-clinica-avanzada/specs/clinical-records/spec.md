# Spec Delta — clinical-records

## ADDED Requirements

### Requirement: Evolución clínica por paciente

El sistema SHALL exponer `GET /api/v1/pacientes/{id}/evoluciones` y `POST /api/v1/pacientes/{id}/evoluciones` para pacientes activos. Cada evolución SHALL persistir `texto`, `fecha` y el `autor_usuario_id` del usuario autenticado; el cliente NO SHALL declarar autor ni fecha. Un paciente inexistente o con `deleted_at` no nulo SHALL responder 404.

#### Scenario: Registro por odontólogo

- **WHEN** un usuario con rol `odontologo` envía `POST` con un `texto` no vacío sobre un paciente activo
- **THEN** la API responde 201 con la evolución creada, su `fecha` y el autor resuelto

#### Scenario: Autor tomado del token

- **WHEN** el odontólogo registra una evolución sin indicar autor en el cuerpo
- **THEN** el `autor_usuario_id` persistido es el `sub` del JWT y no otro valor

#### Scenario: Autor declarado en el cuerpo

- **WHEN** el cuerpo incluye `autor_usuario_id` o `fecha` como campos no declarados
- **THEN** la API responde 422 por `extra="forbid"` (R1) y no persiste nada

#### Scenario: Recepción intenta registrar

- **WHEN** un usuario con rol `recepcion` envía `POST` de una evolución
- **THEN** la API responde 403 con la forma única de error

#### Scenario: Lectura cronológica

- **WHEN** un usuario autorizado consulta las evoluciones de un paciente con varias entradas
- **THEN** la API responde 200 con las evoluciones ordenadas de la más reciente a la más antigua

#### Scenario: Paciente borrado

- **WHEN** se consulta o registra una evolución de un paciente con `deleted_at` no nulo
- **THEN** la API responde 404 y no crea ni devuelve datos clínicos

### Requirement: Inmutabilidad de la evolución clínica

Las evoluciones clínicas SHALL ser append-only: no SHALL existir endpoint de edición ni de borrado, y una evolución registrada SHALL conservarse intacta ante cualquier intento de modificación (R13). Corregir un texto SHALL requerir una evolución nueva.

#### Scenario: Sin rutas de edición ni borrado

- **WHEN** se intenta `PUT`, `PATCH` o `DELETE` sobre una evolución existente
- **THEN** la API responde 405 y la evolución original permanece

#### Scenario: Corrección por evolución nueva

- **WHEN** el odontólogo detecta un error y registra una evolución nueva con la corrección
- **THEN** la API conserva la evolución original y devuelve ambas en la lectura

### Requirement: Consentimiento informado versionado

El sistema SHALL exponer `GET` y `POST /api/v1/pacientes/{id}/consentimientos`. Cada consentimiento SHALL registrar `version`, `fecha` y `autor_usuario_id` del usuario autenticado; el cliente NO SHALL declarar autor ni fecha. Un paciente SHALL tener como máximo un consentimiento por `version`; un duplicado SHALL responder 409.

#### Scenario: Registro de una versión

- **WHEN** el odontólogo registra la versión `v1` del consentimiento de un paciente activo
- **THEN** la API responde 201 con `version`, `fecha` y el autor del JWT

#### Scenario: Versión duplicada

- **WHEN** se intenta registrar una segunda vez la misma `version` para el mismo paciente
- **THEN** la API responde 409 y conserva el consentimiento original

#### Scenario: Versión nueva no pisa la anterior

- **WHEN** el odontólogo registra la versión `v2` de un paciente que ya firmó `v1`
- **THEN** la API responde 201 y el listado devuelve ambas versiones

#### Scenario: Autor o fecha declarados en el cuerpo

- **WHEN** el cuerpo incluye `autor_usuario_id` o `fecha`
- **THEN** la API responde 422 y no persiste nada

#### Scenario: Recepción intenta registrar

- **WHEN** un usuario con rol `recepcion` envía `POST` de un consentimiento
- **THEN** la API responde 403

#### Scenario: Lectura de consentimientos

- **WHEN** un usuario autorizado consulta los consentimientos de un paciente activo
- **THEN** la API responde 200 con las versiones registradas, ordenadas por fecha descendente

#### Scenario: Paciente borrado

- **WHEN** se consulta o registra un consentimiento de un paciente con `deleted_at` no nulo
- **THEN** la API responde 404

### Requirement: Autoría y fecha del hallazgo por pieza

Todo hallazgo de pieza creado o actualizado SHALL registrar el `autor_usuario_id` del odontólogo autenticado y su fecha clínica. El autor SHALL provenir del JWT y no del cuerpo de la request. Los hallazgos heredados de C-07 PUEDEN conservar autor nulo hasta su próxima actualización.

#### Scenario: Upsert nuevo guarda autor

- **WHEN** el odontólogo registra por primera vez la pieza 16
- **THEN** el hallazgo persistido tiene `autor_usuario_id` igual al usuario del JWT

#### Scenario: Upsert existente actualiza autor

- **WHEN** el odontólogo vuelve a registrar una pieza ya existente
- **THEN** el hallazgo conserva una sola fila y su `autor_usuario_id` pasa a ser el del usuario que actualizó

#### Scenario: Autor declarado en el cuerpo

- **WHEN** el cuerpo del `PUT` de pieza incluye `autor_usuario_id`
- **THEN** la API responde 422 y no persiste el hallazgo

#### Scenario: Hallazgo heredado sin autor

- **WHEN** se lee un hallazgo creado antes de C-11 con autor nulo y luego el odontólogo lo actualiza
- **THEN** la lectura inicial responde 200 con autor nulo y la actualización completa el autor

### Requirement: Historial de cambios por pieza

El sistema SHALL exponer `GET /api/v1/pacientes/{id}/odontograma/piezas/{pieza}/historial`, que devuelve las versiones de la pieza ordenadas de la más reciente a la más antigua. Cada versión SHALL incluir estado y observación anteriores y nuevos, autor y fecha de registro. El historial SHALL ser append-only y SHALL registrar una versión por cada upsert.

#### Scenario: Primera versión

- **WHEN** el odontólogo registra por primera vez la pieza 16 con estado `caries`
- **THEN** el historial devuelve una versión con `estado_anterior` nulo y `estado_nuevo="caries"`

#### Scenario: Versión posterior conserva la anterior

- **WHEN** la pieza 16 pasa de `caries` a `obturacion`
- **THEN** el historial devuelve dos versiones y la más reciente tiene `estado_anterior="caries"` y `estado_nuevo="obturacion"`

#### Scenario: Pieza sin cambios

- **WHEN** se consulta el historial de una pieza FDI válida sin hallazgos
- **THEN** la API responde 200 con una lista vacía

#### Scenario: Pieza fuera de FDI

- **WHEN** se consulta el historial de la pieza 19, 20 o 49
- **THEN** la API responde 422

#### Scenario: Paciente borrado

- **WHEN** se consulta el historial de un paciente con `deleted_at` no nulo
- **THEN** la API responde 404

#### Scenario: Lectura por los tres roles

- **WHEN** `admin`, `recepcion` u `odontologo` consultan el historial de una pieza
- **THEN** la API responde 200 con las versiones

### Requirement: RBAC de la ficha clínica avanzada

El backend SHALL autorizar la lectura de evoluciones, consentimientos e historial a `admin`, `recepcion` y `odontologo`, y la escritura de evoluciones y consentimientos solo a `odontologo`. `recepcion` conserva lectura informativa y `admin` supervisa sin escribir (RN-CL-02, R8).

#### Scenario: Sin token

- **WHEN** se llama a cualquier endpoint de la ficha avanzada sin token válido
- **THEN** la API responde 401

#### Scenario: Recepción intenta escribir

- **WHEN** un usuario con rol `recepcion` envía `POST` de evolución o consentimiento
- **THEN** la API responde 403

#### Scenario: Admin intenta escribir

- **WHEN** un usuario con rol `admin` envía `POST` de evolución o consentimiento
- **THEN** la API responde 403 porque la escritura clínica es exclusiva de `odontologo`

#### Scenario: Lectura de supervisión

- **WHEN** `admin` o `recepcion` consultan evoluciones, consentimientos o historial
- **THEN** la API responde 200 con los datos clínicos permitidos

### Requirement: Privacidad de la ficha clínica avanzada

El sistema SHALL no registrar en logs el texto de una evolución, la versión de un consentimiento ni los estados u observaciones del historial. Los datos clínicos SHALL viajar en el cuerpo o la respuesta y nunca como parámetros de query; las rutas SHALL usar solo identificadores internos (R9).

#### Scenario: Logs sin texto clínico

- **WHEN** se registra una evolución o se actualiza una pieza
- **THEN** los logs de la aplicación no contienen el texto, el estado ni la observación clínica

#### Scenario: URL sin datos clínicos

- **WHEN** el frontend consulta evoluciones, consentimientos o historial
- **THEN** la URL solo contiene el `pacienteId` y, si aplica, el número de pieza; nunca texto ni diagnóstico

#### Scenario: Respuesta acotada al paciente

- **WHEN** se consulta la ficha avanzada de un paciente
- **THEN** la respuesta no incluye datos clínicos de otros pacientes ni credenciales

### Requirement: Interfaz de ficha clínica avanzada

La SPA SHALL ampliar `/app/odontograma/:pacienteId` con secciones de evolución clínica, consentimiento informado e historial por pieza. Las acciones de escritura SHALL ocultarse o deshabilitarse para roles sin permiso y la UI SHALL usar los tokens del sistema de diseño revisión 1.

#### Scenario: Secciones visibles

- **WHEN** un usuario autenticado abre la ficha de un paciente
- **THEN** ve el odontograma y las secciones de evolución, consentimiento e historial

#### Scenario: Odontólogo registra una evolución

- **WHEN** el odontólogo completa el texto y guarda
- **THEN** la SPA invoca el `POST` y muestra la evolución en la lista sin recargar la página

#### Scenario: Recepción en modo lectura

- **WHEN** un usuario con rol `recepcion` abre la ficha
- **THEN** ve las secciones pero los formularios de alta están ocultos o deshabilitados

#### Scenario: Historial por pieza

- **WHEN** el usuario selecciona una pieza con cambios
- **THEN** la SPA muestra las versiones con estado anterior, estado nuevo, autor y fecha
