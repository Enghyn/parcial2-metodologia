# Proposal

## Why

El consultorio necesita registrar obras sociales (OS), convenios y aranceles para calcular cobertura y copago de las prácticas odontológicas, hoy inexistentes en el modelo. Sin esto, los presupuestos (C-16) y la facturación manual (C-13b) no pueden estimar el monto a cargo del paciente ni el monto a cargo de la OS.

## What Changes

- Nuevos modelos y migración: `ObraSocial`, `Convenio`, `NomencladorPractica`, `PacienteObraSocial` (afiliación).
- CRUD de obras sociales y convenios (admin).
- Catálogo de prácticas con arancel y copago por convenio.
- Afiliación del paciente a una OS/convenio con número de afiliado.
- Cálculo de cobertura: dado una práctica y un paciente afiliado, devuelve monto OS, copago y monto a cargo del paciente.
- Endpoints bajo `/api/v1/os/*` y `/api/v1/nomenclador/*`.
- RBAC: gestión solo admin; consulta admin/recepcion/odontologo.

## Capabilities

### New Capabilities
- `insurance-coverage`: catálogo de obras sociales, convenios y nomenclador de prácticas; afiliación del paciente y cálculo de cobertura/copago.

### Modified Capabilities
- (ninguna a nivel de spec; los modelos nuevos no alteran requisitos existentes)

## Impact

- Backend: nuevos módulos `os` y `nomenclador`, migración `0009` (o la que corresponda), tests de modelos y routers.
- Frontend: pantallas de administración de OS/convenios/nomenclador (admin) y selector de OS en ficha de paciente.
- Base de datos: nuevas tablas sin `tenant_id` (R2), PK UUID con `gen_random_uuid()`.
- Dependencias: requiere C-11 (ficha clínica) y C-12 (caja) archivados.