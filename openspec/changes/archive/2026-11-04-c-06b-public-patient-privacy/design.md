# Design — C-06b public patient privacy

## Context

Ver `proposal.md` — Why. `PublicReservaService._find_or_create_paciente` corre en un endpoint sin autenticación. El DNI es la clave natural de reutilización; hoy también es la llave para modificar una ficha ajena. La base ya tiene `deleted_at` y `UNIQUE(dni)`.

## Goals / Non-Goals

**Goals:**

- Reutilizar pacientes existentes sin tocar sus datos de contacto.
- No reactivar fichas borradas desde el portal público.
- Mantener el flujo exitoso para pacientes nuevos.

**Non-Goals:**

- Verificar identidad con DNI + teléfono o código.
- Permitir que el paciente edite su ficha.
- Resolver duplicados históricos por DNI.

## Decisions

### D1 — Paciente activo: reutilizar sin sobrescribir

Si `Paciente.dni` existe y `deleted_at IS NULL`, se usa esa ficha y **no** se asignan `telefono` ni `email` desde el request.

- **Por qué**: el portal no puede probar que quien reserva es el titular del DNI.
- **Alternativa descartada**: actualizar solo si el teléfono coincide (sigue sin verificación y filtra información).

### D2 — Paciente con borrado lógico: 409

Si el DNI existe con `deleted_at` no nulo, se responde `409 Conflict` con un mensaje que invita a contactar al consultorio. No se modifica `deleted_at`, `activo` ni los datos.

- **Por qué**: reactivar una ficha borrada desde un endpoint anónimo revierte una decisión administrativa.
- **Alternativa descartada**: crear un paciente nuevo con el mismo DNI (lo impide el UNIQUE y duplicaría historias clínicas).

### D3 — Paciente nuevo: crear con los datos del request

Si no existe ningún registro con ese DNI, se crea con `nombre`, `dni`, `telefono` y `email` opcional.

- **Por qué**: es el caso feliz de la reserva pública.
- **Alternativa descartada**: exigir login (rompe RN-AG-06 y US-004).

### D4 — Sin cambios de contrato

`ReservaCreate`, `PublicTurnoOut` y los endpoints no cambian. El 409 usa la forma única de error.

### D5 — Tests contra PostgreSQL

Se suman casos al `test_public_service.py` existente: paciente existente con teléfono distinto, email distinto, ficha borrada y paciente nuevo. Los tests puros no cambian.

## Risks / Trade-offs

- [Un paciente quiere cambiar su teléfono desde el portal] → no se permite; debe hacerlo recepción (C-07). Se documenta en el mensaje.
- [DNI con ficha borrada] → 409; evita resucitar historias clínicas sin control.
- [Datos existentes incompletos] → se usan tal cual; no se completan desde el request.

## Migration Plan

1. Tests en rojo.
2. Cambio en `_find_or_create_paciente`.
3. Suite con PostgreSQL.
4. Sin migración de base.

## Open Questions

- ¿Recepción podrá corregir el teléfono de un paciente existente? Sí, en C-07; no es parte de este change.
