# Spec Delta — internal-agenda

## ADDED Requirements

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
