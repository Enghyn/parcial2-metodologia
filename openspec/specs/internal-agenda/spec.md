# internal-agenda Specification

## Purpose
Contrato de comportamiento observable de la agenda interna del consultorio en la SPA React: visualización diaria por sillón físico, navegación de fecha, código de colores por estado, alta de turno y cambio rápido de estado, con autenticación del personal y gating cosmético por rol (R8), todo consumiendo los endpoints internos ya definidos por la capability `agenda`.

## Requirements

### Requirement: Login de personal interno en la SPA

La SPA SHALL exponer un formulario de login que recolecte email y password, invoque `POST /api/v1/auth/login`, almacene el `access_token` resultante en el store de autenticación y redirija a `/app/agenda`; ante credenciales inválidas SHALL mostrar un mensaje de error genérico sin revelar si falló el email o el password.

#### Scenario: Login exitoso
- **WHEN** un usuario interno envía credenciales válidas desde `/login`
- **THEN** la SPA almacena el token, obtiene el perfil vía `GET /api/v1/auth/me` y navega a `/app/agenda`

#### Scenario: Credenciales inválidas
- **WHEN** el login falla con 401
- **THEN** la SPA muestra un mensaje de error y permanece en `/login` sin almacenar token

### Requirement: Cierre de sesión

La SPA SHALL permitir cerrar sesión, eliminando el token del store y redirigiendo a `/login`, de modo que las rutas `/app/*` dejen de ser accesibles.

#### Scenario: Logout
- **WHEN** el usuario activa "Cerrar sesión"
- **THEN** el token se elimina del store y la SPA redirige a `/login`

### Requirement: Visualización de agenda por sillón

La SPA SHALL mostrar en `/app/agenda` la agenda del día seleccionado distribuida en una columna por cada sillón físico activo (Sillón 1, Sillón 2, Sillón 3), y cada turno SHALL mostrarse como un bloque con horario, paciente, profesional, prestación y estado.

#### Scenario: Agenda del día
- **WHEN** un usuario autenticado abre `/app/agenda` para una fecha con turnos
- **THEN** se renderiza una columna por sillón activo y los turnos del día aparecen en la columna del sillón asignado

#### Scenario: Sin turnos
- **WHEN** la fecha seleccionada no tiene turnos
- **THEN** cada columna muestra un estado vacío sin errores

### Requirement: Navegación de fecha

La SPA SHALL proveer controles para seleccionar la fecha actual, el día anterior y el día siguiente, y SHALL recargar los turnos correspondientes a la fecha seleccionada.

#### Scenario: Cambio de día
- **WHEN** el usuario navega a anterior/siguiente/hoy
- **THEN** la SPA actualiza la fecha seleccionada y vuelve a consultar `GET /api/v1/turnos?fecha=...`

### Requirement: Código de colores por estado del turno

La SPA SHALL distinguir visualmente cada bloque de turno por su estado (`reservado`, `confirmado`, `presente`, `atendido`, `cancelado`) mediante una asignación consistente de color/estilo, de modo que los estados sean identificables de un vistazo.

#### Scenario: Estado cancelado
- **WHEN** un turno tiene estado `cancelado`
- **THEN** su bloque se renderiza con el estilo asignado a `cancelado` (diferenciado de los demás estados)

### Requirement: Alta de turno mediante modal

La SPA SHALL proveer un modal para crear un turno que requiera paciente, profesional, prestación, sillón, inicio y duración, invoque `POST /api/v1/turnos` y, ante una respuesta 409, muestre el mensaje de conflicto devuelto por el backend; el envío SHALL deshabilitarse mientras la request está en curso.

#### Scenario: Creación exitosa
- **WHEN** un usuario autorizado completa el modal con datos válidos y confirma
- **THEN** la SPA crea el turno, cierra el modal y refresca la agenda del día

#### Scenario: Conflicto de agenda
- **WHEN** el backend responde 409 por solapamiento o bloqueo
- **THEN** el modal permanece abierto y muestra el mensaje de error devuelto

### Requirement: Cambio rápido de estado del turno

La SPA SHALL permitir actualizar el estado de un turno (al menos a `presente` y `cancelado`) mediante una acción contextual, invocando `PATCH /api/v1/turnos/{id}/estado` y reflejando el nuevo estado en la agenda sin recarga manual.

#### Scenario: Marcar presente
- **WHEN** un usuario autorizado marca un turno como `presente`
- **THEN** la SPA invoca el endpoint de cambio de estado y el bloque del turno se actualiza al estilo de `presente`

#### Scenario: Cancelar turno
- **WHEN** un usuario autorizado cancela un turno
- **THEN** la SPA invoca el endpoint con estado `cancelado` y el bloque se actualiza al estilo de `cancelado`

### Requirement: Gating cosmético por rol en la UI

La SPA SHALL ocultar o deshabilitar las acciones de creación y bloqueo para los roles que el backend no autoriza (p. ej. `odontologo` no puede crear turnos), manteniendo siempre la validación real en el backend (R8); las acciones de cambio de estado permanecen disponibles para los roles autorizados por el backend.

#### Scenario: Rol sin permiso de creación
- **WHEN** un usuario con rol `odontologo` abre la agenda
- **THEN** el botón de alta de turno no está disponible, aunque el backend siga siendo la autoridad final

### Requirement: Presentación de errores de la API

La SPA SHALL mostrar al usuario los mensajes de error devueltos por el backend en la forma única `{error:{code,message}}` para fallos de autenticación, autorización y agenda, sin exponer detalles internos.

#### Scenario: Error 403 en creación
- **WHEN** un cliente directo con rol insuficiente intenta crear un turno y el backend responde 403
- **THEN** la SPA muestra el mensaje de error devuelto

### Requirement: Persistencia del token entre recargas

La SPA SHALL persistir el `access_token` en almacenamiento del navegador para que la sesión sobreviva a recargas de página, y SHALL limpiarlo al cerrar sesión o ante un 401 del backend.

#### Scenario: Recarga de página
- **WHEN** el usuario recarga `/app/agenda` con un token válido persistido
- **THEN** la SPA restaura la sesión y carga la agenda sin redirigir a login

#### Scenario: Token inválido en recarga
- **WHEN** el token persistido es inválido o expirado
- **THEN** la SPA limpia el token y redirige a `/login`

### Requirement: Horarios de la agenda en ART

La SPA SHALL mostrar el inicio y el fin de cada turno en `America/Argentina/Buenos_Aires`, independientemente de la zona horaria configurada en el navegador del usuario, y SHALL construir el día seleccionado con el mismo criterio.

#### Scenario: Turno de las 09:00 ART

- **WHEN** el backend devuelve un turno con `inicio = 2027-01-10T12:00:00Z`
- **THEN** la agenda interna muestra `09:00` en el bloque del turno

#### Scenario: Navegador en otra zona

- **WHEN** el navegador está configurado en UTC o en otra zona
- **THEN** la agenda sigue mostrando la hora ART del consultorio

#### Scenario: Fecha seleccionada en ART

- **WHEN** el usuario abre la agenda y navega al día siguiente
- **THEN** la fecha consultada corresponde al calendario ART, no al día UTC
