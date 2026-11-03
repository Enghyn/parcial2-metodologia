# core-data-model Specification

## Purpose
Define el contrato de persistencia del consultorio odontológico mono-tenant: qué entidades existen, qué integridad garantiza el esquema y cómo se cargan los datos mínimos de demostración. Es la base sobre la que se apoyan autenticación, agenda, ficha clínica y caja.

## Requirements

### Requirement: Esquema de dominio versionado

El sistema SHALL crear las tablas de dominio mediante una migración Alembic encadenada al baseline, y SHALL poder revertirlas con `downgrade` sin dejar tablas de dominio ni objetos huérfanos.

#### Scenario: Migración desde el baseline

- **WHEN** se ejecuta `alembic upgrade head` sobre una base con la migración `0001_baseline` aplicada
- **THEN** existen las tablas `usuarios`, `sillones`, `profesionales`, `pacientes`, `turnos`, `bloqueos`, `odontogramas`, `hallazgos_pieza` y `movimientos_caja`

#### Scenario: Reversión de la migración

- **WHEN** se ejecuta `alembic downgrade 0001_baseline`
- **THEN** las nueve tablas de dominio dejan de existir y la extensión `btree_gist` permanece disponible

### Requirement: Identidad única de usuarios

El sistema SHALL garantizar que el `email` de cada usuario sea único y no nulo, SHALL normalizarlo con `btrim` + minúsculas antes de persistirlo y SHALL rechazar en base cualquier email que no cumpla esa forma canónica.

#### Scenario: Email duplicado rechazado

- **WHEN** se intenta registrar un segundo usuario con un email ya existente, ignorando mayúsculas y minúsculas
- **THEN** la persistencia rechaza la operación por violación de unicidad

#### Scenario: Email con mayúsculas o espacios se normaliza

- **WHEN** se registra un usuario con `email = "  Admin@Consultorio.COM  "`
- **THEN** el email persistido es `admin@consultorio.com`

#### Scenario: Email no canónico rechazado por la base

- **WHEN** se intenta insertar por SQL directo un email con mayúsculas o espacios
- **THEN** la base rechaza la operación por `ck_usuarios_email_normalizado`

#### Scenario: Rol fuera del catálogo rechazado

- **WHEN** se intenta persistir un usuario con un rol distinto de `admin`, `recepcion` u `odontologo`
- **THEN** la persistencia rechaza la operación

### Requirement: Profesionales vinculados opcionalmente a un usuario

El sistema SHALL permitir que un profesional exista sin usuario asociado, SHALL impedir que dos profesionales compartan el mismo `usuario_id`, SHALL exigir `nombre` obligatorio y SHALL garantizar que `matricula` sea única. El `nombre` NO es único: dos profesionales pueden ser homónimos.

#### Scenario: Profesional sin usuario

- **WHEN** se crea un profesional con `usuario_id` nulo
- **THEN** la persistencia acepta el registro y la matrícula sigue siendo única

#### Scenario: Dos profesionales con el mismo usuario

- **WHEN** se intenta asignar a un segundo profesional un `usuario_id` ya vinculado
- **THEN** la persistencia rechaza la operación por violación de unicidad

#### Scenario: Dos profesionales homónimos con matrículas distintas

- **WHEN** se crean dos profesionales con el mismo `nombre` y matrículas diferentes
- **THEN** la persistencia acepta ambos registros

### Requirement: Ficha de paciente con identificador único

El sistema SHALL exigir `nombre`, `dni` y `telefono` para todo paciente, SHALL garantizar que el `dni` sea único y SHALL tratar `email`, `obra_social` y `nro_afiliado` como datos opcionales.

#### Scenario: Paciente duplicado por DNI

- **WHEN** se intenta registrar un paciente con un DNI ya existente
- **THEN** la persistencia rechaza la operación y no crea un segundo registro

#### Scenario: Paciente sin teléfono

- **WHEN** se intenta registrar un paciente sin teléfono de contacto
- **THEN** la persistencia rechaza la operación

### Requirement: Integridad temporal y asignación de turnos

El sistema SHALL exigir que todo turno tenga paciente, profesional y sillón asignados, que `fin` sea igual a `inicio + duracion_min` minutos, que `fin` sea posterior a `inicio`, que `duracion_min` sea mayor que cero y que `estado` pertenezca al catálogo de turnos.

#### Scenario: Turno con fin anterior al inicio

- **WHEN** se intenta persistir un turno con `fin` menor o igual a `inicio`
- **THEN** la persistencia rechaza la operación por violación de integridad

#### Scenario: Fin incoherente con la duración

- **WHEN** se intenta persistir un turno con `inicio = 10:00`, `duracion_min = 30` y `fin = 10:45`
- **THEN** la persistencia rechaza la operación por `ck_turnos_fin_coherente`

#### Scenario: Turno sin sillón

- **WHEN** se intenta persistir un turno con `sillon_id` nulo
- **THEN** la persistencia rechaza la operación

#### Scenario: Token público único

- **WHEN** se intenta persistir un segundo turno con un `token_publico` ya usado
- **THEN** la persistencia rechaza la operación por violación de unicidad

### Requirement: Consulta eficiente de disponibilidad

El sistema SHALL proveer índices sobre `turnos(sillon_id, inicio, fin)` y `turnos(profesional_id, inicio, fin)` para que la detección de solapamientos consulte por recurso y rango temporal sin recorrer la tabla completa.

#### Scenario: Uso de índices en la consulta de solapamiento

- **WHEN** la capa de servicios consulta turnos de un sillón o profesional dentro de un rango de fechas
- **THEN** el plan de ejecución puede resolver el filtro con los índices compuestos declarados

### Requirement: Bloqueos de disponibilidad consistentes

El sistema SHALL exigir que todo bloqueo declare al menos un recurso afectado (sillón o profesional), que `hasta` sea posterior a `desde` y SHALL registrar un motivo con al menos un carácter no blanco.

#### Scenario: Bloqueo sin recurso

- **WHEN** se intenta persistir un bloqueo sin `sillon_id` ni `profesional_id`
- **THEN** la persistencia rechaza la operación

#### Scenario: Bloqueo con rango invertido

- **WHEN** se intenta persistir un bloqueo con `hasta` anterior o igual a `desde`
- **THEN** la persistencia rechaza la operación

#### Scenario: Bloqueo con motivo vacío o solo espacios

- **WHEN** se intenta persistir un bloqueo con `motivo = ""` o `motivo = "   "`
- **THEN** la persistencia rechaza la operación por `ck_bloqueos_motivo_no_vacio`

### Requirement: Odontograma FDI por paciente

El sistema SHALL mantener como máximo un odontograma por paciente, SHALL aceptar únicamente piezas FDI de los cuadrantes 1 a 4 con posición 1 a 8 y SHALL impedir dos hallazgos para la misma pieza dentro de un odontograma.

#### Scenario: Segundo odontograma para el mismo paciente

- **WHEN** se intenta crear un odontograma para un paciente que ya tiene uno
- **THEN** la persistencia rechaza la operación por violación de unicidad

#### Scenario: Pieza fuera de la nomenclatura FDI

- **WHEN** se intenta registrar un hallazgo en la pieza `19`, `20` o `49`
- **THEN** la persistencia rechaza la operación por violación de rango

#### Scenario: Hallazgo duplicado en una pieza

- **WHEN** se intenta registrar un segundo hallazgo para la misma pieza del mismo odontograma
- **THEN** la persistencia rechaza la operación por violación de unicidad

### Requirement: Libro de caja append-only

El sistema SHALL tratar `movimientos_caja` como un libro inmutable: SHALL registrar monto positivo, medio de pago del catálogo y usuario responsable, y SHALL impedir actualizaciones y borrados físicos de movimientos ya persistidos, incluso por SQL directo. Las correcciones SHALL registrarse como un movimiento compensatorio nuevo.

#### Scenario: Movimiento con monto no positivo

- **WHEN** se intenta persistir un movimiento con monto cero o negativo
- **THEN** la persistencia rechaza la operación

#### Scenario: Intento de modificar un movimiento existente

- **WHEN** se intenta actualizar o eliminar un movimiento de caja ya persistido
- **THEN** el sistema rechaza la operación y conserva el registro original intacto

#### Scenario: UPDATE o DELETE por SQL directo

- **WHEN** se ejecuta `UPDATE` o `DELETE` sobre `movimientos_caja` sin pasar por el ORM
- **THEN** el trigger de base rechaza la operación

#### Scenario: Corrección por contra-asiento

- **WHEN** se detecta un error en un movimiento y se registra el movimiento compensatorio con tipo opuesto y concepto aclaratorio
- **THEN** el libro conserva ambos movimientos y el balance refleja la corrección

### Requirement: Borrado lógico de entidades de negocio

El sistema SHALL exponer `deleted_at` en `pacientes`, `turnos`, `profesionales` y `sillones`, SHALL inicializarlo en nulo y SHALL impedir el borrado físico de esas entidades, incluso por SQL directo. Las consultas activas SHALL filtrar por `deleted_at IS NULL`.

#### Scenario: Borrado lógico de un paciente

- **WHEN** se solicita eliminar un paciente
- **THEN** el registro conserva sus datos y `deleted_at` queda con la marca temporal de la operación

#### Scenario: Borrado físico rechazado

- **WHEN** se intenta eliminar físicamente un turno o un sillón
- **THEN** el sistema rechaza la operación y el registro permanece

#### Scenario: DELETE por SQL directo

- **WHEN** se ejecuta `DELETE` sobre una de las cuatro entidades de negocio sin pasar por el ORM
- **THEN** el trigger de base rechaza la operación

### Requirement: Seed idempotente de demostración

El sistema SHALL proveer una carga de datos inicial que cree 3 sillones, 1 administrador, 1 recepcionista, 2 odontólogos con su profesional asociado y 2 pacientes, y SHALL poder ejecutarse repetidamente sin duplicar registros. La carga SHALL ser explícita y no ejecutarse automáticamente al arrancar la aplicación.

#### Scenario: Primera carga

- **WHEN** se ejecuta el comando de seed sobre una base migrada y vacía
- **THEN** quedan exactamente 3 sillones, 4 usuarios, 2 profesionales y 2 pacientes

#### Scenario: Segunda carga

- **WHEN** se vuelve a ejecutar el comando de seed sobre la misma base
- **THEN** los conteos no cambian y no se generan duplicados ni errores

#### Scenario: Seed sin base disponible

- **WHEN** se ejecuta el comando de seed sin conexión a la base
- **THEN** el comando falla con un mensaje operativo claro y no deja datos parciales
