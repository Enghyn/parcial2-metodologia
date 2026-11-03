# Spec Delta — core-data-model (hardening)

## MODIFIED Requirements

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
