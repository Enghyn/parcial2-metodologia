# Design — C-07 clinica-odontograma

## Context

Ver `proposal.md` — Why. `Paciente`, `Odontograma` y `HallazgoPieza` existen desde C-02, con `UNIQUE(paciente_id)`, `UNIQUE(odontograma_id, pieza)` y `CHECK` FDI/estado. El módulo `clinica` sigue en stubs. La guía de handoff pide decidir si se agrega `deleted_at` a odontogramas y aclara que el estado válido es `tratamiento_conducto`.

## Goals / Non-Goals

**Goals:**

- CRUD mínimo de pacientes y lectura/escritura del odontograma.
- Upsert idempotente por pieza.
- RBAC clínico y ninguna fuga de datos de salud.
- UI usable con grilla FDI de 32 piezas.

**Non-Goals:**

- Borrar odontogramas o hallazgos (no hay endpoint).
- Editar datos de contacto del paciente desde la ficha clínica (C-07 no lo pide).
- Caja, WhatsApp y reportes.

## Decisions

### D1 — Sin `deleted_at` en odontogramas

`Odontograma` y `HallazgoPieza` no llevan soft delete. El filtro se hace por el paciente: si `Paciente.deleted_at` no es nulo, el odontograma responde 404 y no se crea nada.

- **Por qué**: el odontograma no tiene vida propia fuera del paciente; agregar columnas y migración `0004` no aporta al alcance y complica el modelo.
- **Alternativa descartada**: `SoftDeleteMixin` + migración (el handoff lo dejaba abierto; se descarta por costo/beneficio).
- **Consecuencia**: el texto de C-07 en `CHANGES.md` se interpreta como “pacientes activos y odontogramas de pacientes activos”.

### D2 — GET crea el odontograma si falta

`GET /pacientes/{id}/odontograma` busca el odontograma; si no existe, lo crea vacío y lo devuelve usando `INSERT ... ON CONFLICT DO NOTHING` sobre `UNIQUE(paciente_id)`, para que dos GET concurrentes no choquen.

- **Por qué**: simplifica el frontend (no necesita un endpoint de creación) y el odontograma es un contenedor vacío sin datos clínicos.
- **Alternativa descartada**: devolver 404 y que el front haga un POST (más pasos y otro contrato).
- **Riesgo**: GET con efecto de escritura; se documenta y se testea.

### D3 — Upsert por pieza

`PUT /pacientes/{id}/odontograma/piezas/{pieza}` valida la pieza FDI (11–48, posición 1–8), busca `(odontograma_id, pieza)` y actualiza o inserta.

- **Por qué**: el odontograma se edita pieza por pieza; el `UNIQUE` ya existe.
- **Alternativa descartada**: `POST` + `PATCH` separados (más superficie para el mismo caso).
- **Validación**: la pieza inválida responde 422 antes de tocar la base; el `CHECK` queda como red de seguridad.

### D4 — RBAC

- `GET /pacientes` y `GET /odontograma`: `admin`, `recepcion`, `odontologo`.
- `POST /pacientes`: `admin`, `recepcion` (KB 03).
- `PUT /piezas`: solo `odontologo` (RN-CL-02).
- El frontend oculta/deshabilita, pero el backend es la autoridad (R8).
- Una carrera de alta con el mismo DNI se traduce a 409 (`IntegrityError` + rollback), no a 500.

### D5 — Schemas y privacidad

Todos los schemas con `extra="forbid"` (R1). `PacienteOut` no expone `password_hash` (no existe en el modelo) ni datos de otros pacientes. Los logs no incluyen `estado`, `observacion` ni diagnóstico (R9); solo IDs operativos si hiciera falta.

### D6 — Frontend

- `shared/api/clinica.ts` tipado, reusa `request<T>` y `ApiError`.
- `/app/pacientes`: tabla, buscador por nombre/DNI, alta para admin/recepción, link al odontograma.
- `/app/odontograma/:pacienteId`: 4 cuadrantes, botones 11–48, estado y observación de la pieza seleccionada, guardado con `PUT`; el selector se deshabilita para roles sin permiso.
- Sin `any`; `tsc`, `eslint` y `vite build` deben pasar.

### D7 — Tests

- Unitarios de schemas (R1, estados, pieza).
- Integración de servicio y router con PostgreSQL (marker `integration` y fixture `db_disponible` del chore).
- Casos: DNI duplicado, listado sin borrados, GET crea, PUT inserta/actualiza, pieza 19/20/49 → 422, RBAC 401/403, paciente borrado → 404.
- Correr la suite completa dos veces seguidas (guía de handoff).

## Risks / Trade-offs

- [GET con escritura] → se documenta y se testea; el odontograma vacío no contiene datos clínicos.
- [Datos clínicos en logs] → no se loguean estados/observaciones; tests de contrato no aplican.
- [Piezas FDI] → validación doble (servicio + CHECK); la UI solo ofrece las 32 válidas.
- [Sin borrado de hallazgos] → corregir una pieza es un upsert; no se elimina historial.

## Migration Plan

Sin migración. Solo se montan rutas y se completan stubs. El odontograma se crea lazy en el primer GET.

## Open Questions

- ¿Recepción debe poder corregir el teléfono/email desde la ficha? Queda para un change posterior; C-07 solo alta y lectura.
- ¿Se necesita un `GET /pacientes/{id}`? El front puede resolver el nombre desde el listado; si crece, se agrega.
