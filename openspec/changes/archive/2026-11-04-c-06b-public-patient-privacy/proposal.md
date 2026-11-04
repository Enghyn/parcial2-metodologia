# Proposal — C-06b public patient privacy

## Why

La reserva pública es anónima y hoy busca al paciente por DNI. Si existe, **sobrescribe su teléfono y email**; si estaba borrado lógicamente, lo **reactiva**. Cualquiera que conozca un DNI puede modificar datos de contacto de otra persona. Es un problema de privacidad e integridad, no de autenticación del paciente.

## What Changes

- Un paciente **activo** existente se reutiliza **sin modificar** `nombre`, `telefono` ni `email`; el turno se asocia a esa ficha.
- Un DNI que pertenece a una ficha con **borrado lógico** responde **409** con un mensaje operativo (“contactá al consultorio”), sin reactivarla.
- Si el DNI no existe, se crea el paciente con los datos enviados.
- Tests de regresión para los tres casos y para el email opcional.

## Capabilities

### New Capabilities

- Ninguna.

### Modified Capabilities

- `public-reservation`: se reemplaza el “find-or-create con actualización” por reutilización sin sobrescritura y rechazo de fichas borradas.

## Impact

- **Backend**: `backend/src/app/modules/public/service.py` (`_find_or_create_paciente`).
- **Tests**: `backend/test/test_public_service.py` (nuevos casos) y ajuste de los existentes.
- **Sin cambios de API, schema, migraciones ni frontend** (la UI ya muestra el mensaje de error del backend).
- **Fuera de alcance**: validación de identidad del paciente, login público, actualización de datos por recepción (C-07) y timezone/recursos activos (C-04b).
