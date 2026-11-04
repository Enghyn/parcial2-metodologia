# Proposal — C-07 clinica-odontograma

## Why

El backend ya tiene las tablas `pacientes`, `odontogramas` y `hallazgos_pieza` (C-02), pero no hay endpoints ni UI para usarlas. C-07 cierra la capa clínica: directorio de pacientes, alta con DNI único y odontograma FDI interactivo para que el odontólogo registre el estado de las 32 piezas.

## What Changes

- **Pacientes**: `GET /api/v1/pacientes` (listado/búsqueda por nombre o DNI, sin borrados lógicos) y `POST /api/v1/pacientes` (alta con DNI único; duplicado → 409).
- **Odontograma**: `GET /api/v1/pacientes/{id}/odontograma` que devuelve el odontograma del paciente y lo crea si no existe; paciente inexistente o borrado → 404.
- **Hallazgos**: `PUT /api/v1/pacientes/{id}/odontograma/piezas/{pieza}` como upsert por `(odontograma, pieza)`, con validación FDI y catálogo `tratamiento_conducto`.
- **RBAC**: lectura para `admin`, `recepcion` y `odontologo`; alta de paciente para `admin`/`recepcion`; edición de pieza solo `odontologo` (R8, RN-CL-02).
- **Frontend**: `/app/pacientes` (directorio, buscador y alta) y `/app/odontograma/:pacienteId` (grilla de 4 cuadrantes, 32 piezas, selector de estado y guardado).
- **Documentación**: corregir `conducto` por `tratamiento_conducto` en `CHANGES.md`.

## Capabilities

### New Capabilities

- `clinical-records`: directorio de pacientes, odontograma FDI, upsert de hallazgos y sus reglas de acceso y privacidad.

### Modified Capabilities

- Ninguna. `core-data-model` ya define las entidades; C-07 agrega comportamiento.

## Impact

- **Backend**: `modules/clinica/{schemas,service,router}.py`, `api/v1/router.py`, `test/test_structure.py`.
- **Frontend**: `shared/api/clinica.ts`, `features/clinica/*`, `app/{router,layout}.tsx`.
- **Tests**: nuevos `test_clinica_schemas.py`, `test_clinica_service.py` y `test_clinica_router.py` (integración con PostgreSQL).
- **Sin migración**: se decide no agregar `deleted_at` a odontogramas; el filtro se hace por el paciente (ver design).
- **Fuera de alcance**: C-08 caja, WhatsApp, edición de datos de contacto por odontólogo y borrado de odontogramas.
