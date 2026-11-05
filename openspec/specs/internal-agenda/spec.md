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

### Requirement: Acciones de agenda avanzada

La SPA SHALL ofrecer, para los roles autorizados, la acción de reprogramar un turno y la de marcarlo como `ausente`; SHALL reflejar el nuevo horario o estado sin recargar manualmente y SHALL mostrar el error del backend si la operación falla.

#### Scenario: Reprogramar desde la agenda

- **WHEN** recepción selecciona “Reprogramar”, elige un nuevo horario y confirma
- **THEN** la SPA invoca el endpoint de reprogramación y actualiza el bloque del turno

#### Scenario: Marcar ausente desde la agenda

- **WHEN** un usuario autorizado marca un turno como `ausente`
- **THEN** el bloque se actualiza con el estilo de `ausente`

#### Scenario: Error de reprogramación

- **WHEN** el backend responde 409 por solapamiento
- **THEN** la SPA muestra el mensaje y mantiene el horario original

### Requirement: Vista semanal 7 × 3

La SPA SHALL mostrar en `/app/agenda/semana` una grilla de siete columnas, de lunes a domingo, y una fila por cada sillón físico activo. Cada celda SHALL listar los turnos de ese sillón y día ordenados por hora de inicio, con horario, paciente, profesional, prestación y estado; las celdas sin turnos SHALL mostrar un estado vacío sin errores.

#### Scenario: Semana con turnos

- **WHEN** un usuario autenticado abre `/app/agenda/semana` en una semana con turnos
- **THEN** se renderizan siete columnas por día, una fila por sillón activo y cada turno aparece en la celda de su sillón y su día ART

#### Scenario: Celda vacía

- **WHEN** un sillón no tiene turnos en un día de la semana
- **THEN** la celda muestra un estado vacío y la grilla no falla

#### Scenario: Turno nocturno en su día correcto

- **WHEN** existe un turno a las 23:30 ART del domingo de la semana mostrada
- **THEN** el turno aparece en la columna del domingo y no en la del lunes siguiente

#### Scenario: Sillón inactivo

- **WHEN** un sillón está inactivo o borrado lógicamente
- **THEN** no se renderiza su fila en la grilla semanal

### Requirement: Navegación de semana

La SPA SHALL permitir avanzar una semana, retroceder una semana y volver a la semana actual, recalculando el lunes de la semana en zona ART y consultando el rango correspondiente. La semana SHALL comenzar el lunes y terminar el domingo.

#### Scenario: Avanzar una semana

- **WHEN** el usuario activa “Semana siguiente”
- **THEN** la grilla muestra los siete días de la semana siguiente y consulta su rango

#### Scenario: Retroceder una semana

- **WHEN** el usuario activa “Semana anterior”
- **THEN** la grilla muestra los siete días de la semana anterior y consulta su rango

#### Scenario: Volver a la semana actual

- **WHEN** el usuario activa “Semana actual”
- **THEN** la grilla muestra la semana que contiene la fecha de hoy en ART

#### Scenario: Cambio de mes o año

- **WHEN** la semana cruza el límite entre diciembre y enero
- **THEN** los siete días se muestran en orden cronológico sin duplicados ni huecos

### Requirement: Filtro por profesional en la vista semanal

La SPA SHALL ofrecer un filtro por profesional con la opción “Todos los profesionales”. Al seleccionar un profesional, la grilla SHALL mostrar únicamente sus turnos para toda la semana, manteniendo las columnas de días y las filas de sillones; al volver a “Todos”, SHALL restaurar la vista completa sin recargar la página.

#### Scenario: Filtrar por un profesional

- **WHEN** el usuario selecciona un profesional en el filtro
- **THEN** solo se muestran sus turnos de la semana y las celdas restantes quedan vacías

#### Scenario: Restaurar todos los profesionales

- **WHEN** el usuario vuelve a “Todos los profesionales”
- **THEN** la grilla vuelve a mostrar los turnos de todos los profesionales de la semana

#### Scenario: Profesional sin turnos

- **WHEN** el profesional seleccionado no tiene turnos en la semana
- **THEN** la grilla muestra todas las celdas vacías sin error

### Requirement: Conmutador entre vista diaria y semanal

La SPA SHALL ofrecer un conmutador Diaria / Semanal accesible desde ambas vistas. “Diaria” SHALL navegar a `/app/agenda` conservando el comportamiento diario existente; “Semanal” SHALL navegar a `/app/agenda/semana`. La opción activa SHALL indicarse con texto o atributo accesible, no solo con color.

#### Scenario: Pasar a la vista semanal

- **WHEN** el usuario activa “Semanal” desde la vista diaria
- **THEN** la SPA navega a `/app/agenda/semana` y carga la semana actual

#### Scenario: Volver a la vista diaria

- **WHEN** el usuario activa “Diaria” desde la vista semanal
- **THEN** la SPA navega a `/app/agenda` y la vista diaria conserva su comportamiento previo

#### Scenario: Acceso directo a la vista semanal

- **WHEN** un usuario autenticado abre `/app/agenda/semana` directamente
- **THEN** la SPA renderiza la grilla semanal sin pasar por la vista diaria

### Requirement: Acciones de turno desde la vista semanal

En la vista semanal, seleccionar un turno SHALL abrir las mismas acciones que la vista diaria, cambio de estado y reprogramación, para los roles que el backend autoriza; el resultado SHALL reflejarse en la grilla sin recarga manual y los errores del backend SHALL mostrarse al usuario. Clickear una celda vacía SHALL NOT crear ni modificar turnos.

#### Scenario: Cambiar estado desde la grilla

- **WHEN** un usuario autorizado marca un turno como `presente` desde la vista semanal
- **THEN** la SPA invoca el endpoint de estado y el bloque se actualiza con el estilo de `presente`

#### Scenario: Reprogramar desde la grilla

- **WHEN** recepción elige “Reprogramar” en un turno de la grilla, define un nuevo horario y confirma
- **THEN** la SPA invoca la reprogramación y, si el nuevo horario cae en la semana mostrada, el turno se mueve a la celda del nuevo día y horario

#### Scenario: Reprogramar fuera de la semana mostrada

- **WHEN** el nuevo horario de la reprogramación cae en otra semana
- **THEN** el turno deja de mostrarse en la semana actual y la SPA informa la semana de destino sin recargar la página

#### Scenario: Error de reprogramación

- **WHEN** el backend responde 409 por solapamiento
- **THEN** la SPA muestra el mensaje y el turno conserva su horario original

#### Scenario: Click en celda vacía

- **WHEN** el usuario clickea una celda sin turnos
- **THEN** no se abre ningún modal de creación ni se envía ninguna request

### Requirement: Estados visuales y sobreturnos en la vista semanal

La SPA SHALL distinguir los seis estados del turno (`reservado`, `confirmado`, `presente`, `atendido`, `cancelado`, `ausente`) con el mismo criterio de color y estilo que la vista diaria, acompañado de una etiqueta textual. Los sobreturnos SHALL mostrar un indicador textual adicional, y los turnos cancelados SHALL permanecer visibles atenuados.

#### Scenario: Turno ausente

- **WHEN** un turno tiene estado `ausente`
- **THEN** su bloque usa el estilo de `ausente` y muestra la etiqueta “ausente”

#### Scenario: Sobreturno

- **WHEN** un turno tiene `es_sobreturno = true`
- **THEN** su bloque muestra un indicador textual de sobreturno además del color del estado

#### Scenario: Turno cancelado visible

- **WHEN** un turno de la semana está `cancelado`
- **THEN** sigue visible en su celda con el estilo atenuado de `cancelado`

#### Scenario: Estado identificable sin color

- **WHEN** un usuario no distingue colores
- **THEN** puede identificar el estado por su etiqueta textual en el bloque

### Requirement: Carga semanal en una sola consulta

Al abrir o navegar a una semana, la SPA SHALL obtener todos los turnos del rango lunes–domingo con una única consulta a `GET /api/v1/turnos?desde=...&hasta=...`, SHALL mostrar un estado de carga mientras espera y SHALL mostrar un mensaje con opción de reintentar si la consulta falla. La SPA SHALL NOT emitir una consulta por día.

#### Scenario: Una sola request por semana

- **WHEN** el usuario abre la vista semanal
- **THEN** la SPA emite exactamente una consulta de turnos para el rango de siete días

#### Scenario: Error de red

- **WHEN** la consulta semanal falla
- **THEN** la SPA muestra el mensaje de error y permite reintentar sin recargar la página

#### Scenario: Navegación entre semanas

- **WHEN** el usuario avanza a otra semana
- **THEN** la grilla reemplaza los turnos de la semana anterior por los de la nueva sin mezclarlos
