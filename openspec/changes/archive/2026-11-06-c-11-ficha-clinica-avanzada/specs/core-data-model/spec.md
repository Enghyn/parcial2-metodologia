# Spec Delta — core-data-model

## ADDED Requirements

### Requirement: Evolución clínica append-only

El esquema SHALL persistir las evoluciones clínicas en `evoluciones_clinicas` con `paciente_id`, `autor_usuario_id`, `fecha` y `texto` no vacío, y SHALL impedir `UPDATE` y `DELETE` incluso por SQL directo mediante trigger. Las filas SHALL conservarse aunque el paciente tenga baja lógica.

#### Scenario: Inserción válida

- **WHEN** se inserta una evolución con paciente, autor, fecha y texto no vacío
- **THEN** la persistencia acepta el registro

#### Scenario: Texto vacío o solo espacios

- **WHEN** se intenta persistir una evolución con `texto = ""` o `texto = "   "`
- **THEN** la persistencia rechaza la operación por el `CHECK` de texto no vacío

#### Scenario: UPDATE o DELETE por SQL directo

- **WHEN** se ejecuta `UPDATE` o `DELETE` sobre `evoluciones_clinicas` sin pasar por el ORM
- **THEN** el trigger de base rechaza la operación y la fila permanece intacta

#### Scenario: Paciente con baja lógica

- **WHEN** un paciente recibe `deleted_at` y tenía evoluciones
- **THEN** las evoluciones siguen existiendo y no se borran en cascada

### Requirement: Consentimiento informado persistido y versionado

El esquema SHALL persistir los consentimientos en `consentimientos_informados` con `paciente_id`, `version`, `fecha` y `autor_usuario_id`, SHALL impedir duplicados de `(paciente_id, version)` y SHALL bloquear `UPDATE` y `DELETE` por trigger.

#### Scenario: Inserción válida

- **WHEN** se inserta un consentimiento con paciente, versión, fecha y autor
- **THEN** la persistencia acepta el registro

#### Scenario: Versión duplicada

- **WHEN** se intenta persistir dos consentimientos con el mismo `paciente_id` y `version`
- **THEN** la persistencia rechaza la operación por violación de unicidad

#### Scenario: Versión vacía

- **WHEN** se intenta persistir un consentimiento con `version = ""` o solo espacios
- **THEN** la persistencia rechaza la operación por el `CHECK` de versión no vacía

#### Scenario: UPDATE o DELETE por SQL directo

- **WHEN** se ejecuta `UPDATE` o `DELETE` sobre `consentimientos_informados`
- **THEN** el trigger de base rechaza la operación

### Requirement: Autoría del hallazgo persistida

El esquema SHALL agregar `autor_usuario_id` a `hallazgos_pieza` como FK opcional a `usuarios`, para conservar la autoría de los hallazgos nuevos y permitir filas heredadas sin autor.

#### Scenario: Columna y FK existen

- **WHEN** se aplica la migración de C-11
- **THEN** `hallazgos_pieza` tiene `autor_usuario_id` con FK a `usuarios.id`

#### Scenario: Usuario inexistente

- **WHEN** se intenta persistir un hallazgo con un `autor_usuario_id` que no existe
- **THEN** la persistencia rechaza la operación por violación de FK

#### Scenario: Fila heredada sin autor

- **WHEN** existe un hallazgo creado antes de C-11
- **THEN** la columna admite `autor_usuario_id` nulo sin romper la lectura

### Requirement: Historial inmutable de hallazgos por pieza

El esquema SHALL persistir cada cambio de hallazgo en `hallazgos_pieza_historial` con pieza, estado y observación anteriores y nuevos, autor y fecha de registro, SHALL validar el catálogo de estados y SHALL bloquear `UPDATE` y `DELETE` por trigger.

#### Scenario: Inserción válida

- **WHEN** se inserta una versión con pieza FDI, estados del catálogo y autor
- **THEN** la persistencia acepta el registro

#### Scenario: Estado fuera del catálogo

- **WHEN** se intenta persistir un historial con `estado_nuevo="conducto"` o `estado_anterior="implante"`
- **THEN** la persistencia rechaza la operación

#### Scenario: UPDATE o DELETE por SQL directo

- **WHEN** se ejecuta `UPDATE` o `DELETE` sobre `hallazgos_pieza_historial`
- **THEN** el trigger de base rechaza la operación y la versión permanece

#### Scenario: Consulta por pieza

- **WHEN** se consultan las versiones de un hallazgo ordenadas por fecha
- **THEN** el plan de ejecución puede usar el índice por hallazgo y fecha de registro

### Requirement: Migración reversible de ficha clínica avanzada

El sistema SHALL crear `evoluciones_clinicas`, `consentimientos_informados`, `hallazgos_pieza_historial`, la columna `hallazgos_pieza.autor_usuario_id` y sus triggers mediante la migración `0007_ficha_clinica_avanzada`, encadenada a la última migración aplicada, y SHALL revertirlos con `downgrade`.

#### Scenario: Upgrade crea los objetos

- **WHEN** se ejecuta `alembic upgrade head` sobre una base con la migración anterior aplicada
- **THEN** existen las tres tablas, la columna y los triggers de inmutabilidad

#### Scenario: Downgrade revierte

- **WHEN** se ejecuta `alembic downgrade` a la revisión anterior
- **THEN** las tres tablas, la columna y los triggers dejan de existir sin objetos huérfanos

#### Scenario: Sin multi-tenant

- **WHEN** se inspecciona el esquema resultante
- **THEN** ninguna de las tablas nuevas tiene `tenant_id` (R2)
