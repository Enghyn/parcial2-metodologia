# Spec Delta

## Purpose

Gestiona el catálogo de obras sociales, convenios y nomenclador de prácticas del consultorio, la afiliación de pacientes y el cálculo de cobertura/copago para estimar montos a cargo de la OS y del paciente.

## ADDED Requirements

### Requirement: Catálogo de obras sociales

El sistema SHALL exponer CRUD de obras sociales para `admin`, con nombre único, código (opcional) y estado activo/inactivo. Una OS con convenios vigentes SHALL NOT borrarse físicamente (R13); se desactiva.

#### Scenario: Alta de obra social
- **WHEN** un admin crea una OS con nombre único
- **THEN** la API responde 201 con la OS creada

#### Scenario: Nombre duplicado
- **WHEN** se crea una OS con un nombre ya existente
- **THEN** la API responde 409

### Requirement: Convenios por obra social

El sistema SHALL permitir a `admin` registrar convenios asociados a una OS, con vigencia (desde/hasta), descuento global opcional y estado. Un convenio vencido SHALL NOT aplicar cobertura.

#### Scenario: Convenio vigente
- **WHEN** se calcula cobertura con un convenio vigente a la fecha
- **THEN** se usa su arancel/copago

#### Scenario: Convenio vencido
- **WHEN** el convenio está fuera de vigencia
- **THEN** la cobertura se considera nula (paciente paga 100%)

### Requirement: Nomenclador de prácticas

El sistema SHALL mantener un nomenclador de prácticas odontológicas con código, descripción y arancel base. Por convenio se puede sobrescribir arancel y copago (monto fijo o porcentaje).

#### Scenario: Arancel por convenio
- **WHEN** una práctica tiene arancel específico en el convenio del paciente
- **THEN** se usa ese arancel en lugar del base

#### Scenario: Sin arancel específico
- **WHEN** no hay arancel específico para la práctica en el convenio
- **THEN** se usa el arancel base del nomenclador

### Requirement: Afiliación del paciente

El sistema SHALL permitir afiliar un paciente a una OS/convenio con número de afiliado y vigencia. Un paciente puede tener a lo sumo una afiliación vigente.

#### Scenario: Afiliación vigente
- **WHEN** se consulta la afiliación de un paciente con convenio vigente
- **THEN** se devuelve OS, convenio y número de afiliado

#### Scenario: Sin afiliación
- **WHEN** el paciente no tiene afiliación vigente
- **THEN** la cobertura es nula (paciente paga 100%)

### Requirement: Cálculo de cobertura

El sistema SHALL exponer un endpoint que, dado un paciente y una práctica, calcule monto OS, copago y monto a cargo del paciente según convenio vigente. Si no hay afiliación o convenio vencido, el paciente paga el 100% del arancel.

#### Scenario: Cobertura con copago fijo
- **WHEN** el convenio define copago fijo
- **THEN** monto paciente = copago, monto OS = arancel - copago

#### Scenario: Sin cobertura
- **WHEN** el paciente no tiene afiliación vigente
- **THEN** monto paciente = arancel base, monto OS = 0

### Requirement: RBAC de OS y nomenclador

La gestión (alta/edición/baja) SHALL ser solo `admin`. La consulta SHALL estar disponible para `admin`, `recepcion` y `odontologo`. Sin token SHALL responder 401; `odontologo` en gestión SHALL responder 403.

#### Scenario: Recepción consulta nomenclador
- **WHEN** recepción consulta el nomenclador
- **THEN** la API responde 200

#### Scenario: Odontólogo gestiona OS
- **WHEN** un odontólogo intenta crear una OS
- **THEN** la API responde 403