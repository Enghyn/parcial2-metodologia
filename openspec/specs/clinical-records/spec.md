# clinical-records Specification

## Purpose
Define el comportamiento de la ficha clínica del consultorio: directorio y alta de pacientes, odontograma FDI por paciente y registro de hallazgos por pieza, con control de acceso por rol y sin exponer datos de salud innecesarios.

## Requirements

### Requirement: Directorio de pacientes activos

El sistema SHALL exponer `GET /api/v1/pacientes` con búsqueda opcional por nombre o DNI, devolviendo solo pacientes con `deleted_at` nulo y ordenados por nombre, para los roles `admin`, `recepcion` y `odontologo`.

#### Scenario: Listado sin borrados lógicos

- **WHEN** existe un paciente con `deleted_at` no nulo
- **THEN** no aparece en `GET /api/v1/pacientes`

#### Scenario: Búsqueda por DNI o nombre

- **WHEN** se consulta con `q` que coincide parcialmente con el DNI o el nombre
- **THEN** solo se devuelven los pacientes activos que coinciden

### Requirement: Alta de paciente con DNI único

El sistema SHALL exponer `POST /api/v1/pacientes` para los roles `admin` y `recepcion`, exigiendo `nombre`, `dni` y `telefono`, y SHALL responder 409 si el DNI ya existe (incluida una ficha borrada lógicamente).

#### Scenario: Alta exitosa

- **WHEN** un usuario autorizado envía un DNI no registrado y los campos obligatorios
- **THEN** la API responde 201 con el paciente creado y `activo=true`

#### Scenario: DNI duplicado

- **WHEN** se intenta crear un paciente con un DNI ya existente
- **THEN** la API responde 409 con la forma única de error

#### Scenario: Campo extra rechazado

- **WHEN** el cuerpo incluye un campo no declarado
- **THEN** la API responde 422

### Requirement: Odontograma por paciente

El sistema SHALL exponer `GET /api/v1/pacientes/{id}/odontograma` para los tres roles; SHALL devolver el odontograma del paciente y SHALL crearlo vacío si todavía no existe. Un paciente inexistente o con `deleted_at` no nulo SHALL responder 404.

#### Scenario: Primer acceso crea el odontograma

- **WHEN** se consulta el odontograma de un paciente activo que no tiene uno
- **THEN** la API crea el odontograma vacío y responde 200 con `hallazgos=[]`

#### Scenario: Paciente borrado

- **WHEN** se consulta el odontograma de un paciente con `deleted_at` no nulo
- **THEN** la API responde 404 y no crea un odontograma

### Requirement: Upsert de hallazgo por pieza FDI

El sistema SHALL exponer `PUT /api/v1/pacientes/{id}/odontograma/piezas/{pieza}` solo para `odontologo`, validando que la pieza sea FDI válida (11–48, posición 1–8) y que `estado` pertenezca a `sano`, `caries`, `obturacion`, `corona`, `extraccion` o `tratamiento_conducto`; SHALL insertar o actualizar el hallazgo de esa pieza.

#### Scenario: Pieza nueva

- **WHEN** el odontólogo registra la pieza 16 con estado `caries`
- **THEN** se crea el hallazgo y la API responde 200 con la pieza actualizada

#### Scenario: Pieza existente

- **WHEN** el odontólogo vuelve a registrar la pieza 16 con estado `obturacion`
- **THEN** se actualiza el mismo hallazgo, sin duplicar la pieza

#### Scenario: Pieza fuera de FDI

- **WHEN** se intenta registrar la pieza 19, 20 o 49
- **THEN** la API responde 422 y no persiste nada

#### Scenario: Estado inválido

- **WHEN** se envía `estado="conducto"`
- **THEN** la API responde 422

### Requirement: RBAC de la ficha clínica

El sistema SHALL validar token y rol en el backend: lectura para `admin`, `recepcion` y `odontologo`; alta de paciente para `admin` y `recepcion`; edición de piezas solo para `odontologo`. El frontend solo oculta o deshabilita la UI (R8).

#### Scenario: Sin token

- **WHEN** se llama a un endpoint clínico sin token válido
- **THEN** la API responde 401

#### Scenario: Recepción intenta editar una pieza

- **WHEN** un usuario con rol `recepcion` hace `PUT` sobre una pieza
- **THEN** la API responde 403

### Requirement: Privacidad de datos clínicos

El sistema SHALL no registrar en logs el estado, la observación ni el diagnóstico de una pieza, y las respuestas de pacientes SHALL no incluir credenciales ni datos de otras fichas (R9).

#### Scenario: Respuesta de paciente sin credenciales

- **WHEN** se lista o crea un paciente
- **THEN** la respuesta no contiene `password_hash` ni tokens

### Requirement: Interfaz de ficha clínica

La SPA SHALL exponer `/app/pacientes` con directorio, buscador y alta, y `/app/odontograma/:pacienteId` con una grilla de 4 cuadrantes y 32 piezas FDI (11–48), selector de estado y guardado del hallazgo; las acciones de escritura SHALL ocultarse o deshabilitarse para roles sin permiso.

#### Scenario: Odontograma visible

- **WHEN** un usuario autenticado abre `/app/odontograma/:pacienteId`
- **THEN** ve las 32 piezas agrupadas en 4 cuadrantes y los hallazgos existentes

#### Scenario: Guardar una pieza

- **WHEN** el odontólogo selecciona una pieza y un estado y guarda
- **THEN** la SPA invoca el `PUT` y refleja el estado actualizado
