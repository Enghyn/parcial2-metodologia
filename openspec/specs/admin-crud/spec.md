# admin-crud Specification

## Purpose
Permite al administrador gestionar usuarios, sillones y profesionales con baja lógica.

## Requirements

### Requirement: CRUD de usuarios

El sistema SHALL exponer CRUD de usuarios con nombre, email, rol y activo para admin. No se puede desactivar el último admin activo.

#### Scenario: Crear usuario
- **WHEN** un admin crea un usuario válido
- **THEN** la API responde 201

#### Scenario: Último admin
- **WHEN** se intenta desactivar el último admin activo
- **THEN** la API responde 409

### Requirement: CRUD de sillones

El sistema SHALL exponer CRUD de sillones con nombre, descripción y activo.

#### Scenario: Crear sillón
- **WHEN** un admin crea un sillón
- **THEN** la API responde 201

### Requirement: CRUD de profesionales

El sistema SHALL exponer CRUD de profesionales con matrícula, especialidad, duración default y vínculo opcional a usuario.

#### Scenario: Crear profesional
- **WHEN** un admin crea un profesional
- **THEN** la API responde 201

### Requirement: Baja lógica

El sistema SHALL usar borrado lógico (deleted_at) en Paciente, Turno, Profesional y Sillon; no borrado físico.

#### Scenario: Baja lógica
- **WHEN** se elimina un profesional
- **THEN** se setea deleted_at y no se borra la fila

### Requirement: RBAC

El sistema SHALL permitir gestión solo a admin; sin token SHALL responder 401.

#### Scenario: Recepción gestiona
- **WHEN** recepcion intenta crear usuario
- **THEN** la API responde 403
