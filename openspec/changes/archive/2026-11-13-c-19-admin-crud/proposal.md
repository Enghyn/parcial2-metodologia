# Proposal

## Why

El administrador necesita gestionar usuarios, sillones y profesionales (CRUD con baja lógica) desde la UI. Hoy no existe.

## What Changes

- CRUD de usuarios con roles y activo.
- CRUD de sillones.
- CRUD de profesionales (matrícula, especialidad, duración, vínculo a usuario).
- Baja lógica; no desactivar último admin.
- Migración: sin migración (usa tablas existentes).

## Capabilities

### New Capabilities
- `admin-crud`: gestión de usuarios, sillones y profesionales por admin.

### Modified Capabilities
- (ninguna)

## Impact

- Backend: ampliar módulo admin con CRUDs, tests.
- Frontend: pantallas de administración.
- Dependencias: C-03.