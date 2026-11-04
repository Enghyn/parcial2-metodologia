# Design — C-08 caja-movimientos-balance

## Context

Ver `proposal.md` — Why. `MovimientoCaja` existe desde C-02 con `CHECK` de monto/tipo/medio, `ImmutableLedgerMixin`, guardas ORM y triggers de base (`0003`). No hay columnas de anulación ni de vínculo entre contra-asientos. El consultorio opera en ART y la caja se cierra por día calendario.

## Goals / Non-Goals

**Goals:**

- Registrar ingresos/egresos con trazabilidad de usuario y turno.
- Consultar el libro del día y el resumen por medio de pago.
- Mantener la inmutabilidad sin migración.
- Pantalla usable en `/app/caja`.

**Non-Goals:**

- Integración real con Mercado Pago/ARCA.
- Exportación CSV o cierre inmutable por período.
- Conciliación bancaria.
- Anulación con columna dedicada.

## Decisions

### D1 — Seña manual, no automática

`Turno.sena_monto` no crea un `MovimientoCaja` al reservar. La seña se registra como ingreso cuando recepción la cobra, con `turno_id` y concepto “Seña de reserva”. La UI de caja SHALL mostrar un aviso de “seña pendiente” cuando el turno tenga `sena_monto > 0` y no exista un ingreso vinculado con concepto de seña.

- **Por qué**: evita acoplar C-06 con caja y mantiene un único libro append-only.
- **Alternativa descartada**: generar el movimiento al reservar (C-06 tendría que conocer caja y los reintentos podrían duplicar).
- **Consecuencia**: la UI puede precargar el monto de la seña desde el turno, pero el asiento es explícito.

### D2 — Contra-asiento como fila inversa

Una corrección se registra como un nuevo movimiento de tipo opuesto, mismo monto, concepto aclaratorio y `turno_id` si aplica. No se agrega `contra_asiento_de` ni migración.

- **Por qué**: R3/RN-CJ-02 prohíbe update/delete; el libro conserva ambos asientos.
- **Alternativa descartada**: columna de vínculo (requiere migración y no agrega valor al MVP).
- **Riesgo**: sin vínculo estructurado, la relación se lee en el concepto; se documenta.

### D3 — Usuario desde el JWT

El endpoint recibe `usuario: Usuario = Depends(require_role("admin", "recepcion"))` y pasa `usuario.id` al servicio. El body no acepta `usuario_id`.

- **Por qué**: R4 y R8; evita suplantación.
- **Alternativa descartada**: aceptar `usuario_id` en el body (rechazado por regla dura).

### D3b — Turno vinculado: cualquier estado no borrado

Si se envía `turno_id`, el servicio solo exige que el turno exista y tenga `deleted_at` nulo; no restringe por estado (`reservado`, `confirmado`, `presente`, `atendido` o `cancelado`).

- **Por qué**: un movimiento de caja es un hecho contable y puede corresponder a una atención, una seña, una devolución o una penalidad.
- **Riesgo aceptado**: permite vincular un ingreso a un turno cancelado. Se prioriza la simplicidad operativa; la UI muestra el estado del turno para que el usuario decida.
- **Alternativa descartada**: atar ingreso a `atendido` y egreso a `cancelado` (opción C), que bloquea señas, penalidades y garantías reales.

### D4 — Append-only sin migración

El servicio solo hace `add` + `commit`; no expone update/delete. Las guardas existentes (`ImmutableLedgerMixin`, triggers) siguen siendo la red de seguridad.

### D5 — Día calendario ART

`GET /movimientos?fecha=` y `GET /resumen-diario?fecha=` usan `inicio_dia`/`fin_dia` de `app/core/timezone.py`; sin `fecha`, el resumen usa `ahora().date()`.

- **Por qué**: la caja se cierra por día del consultorio, no UTC.
- **Alternativa descartada**: rango UTC (desfase de 3 horas).

### D6 — Dinero con Decimal y ARS

`monto: Decimal` con `gt=0`, `max_digits=10, decimal_places=2`. El backend devuelve Decimal (Pydantic lo serializa como string en JSON); el frontend lo convierte con `Number` y `formatArs`.

- **Por qué**: evitar errores de punto flotante.
- **Alternativa descartada**: `float` (pierde centavos).

### D7 — RBAC de caja

`admin` y `recepcion` pueden registrar y consultar; `odontologo` recibe 403. El frontend oculta la pantalla, pero el backend es la autoridad (R8).

### D8 — Frontend `/app/caja`

- `shared/api/caja.ts` tipado; `crearMovimiento`, `listarMovimientos`, `resumenDiario`.
- Página con formulario de ingreso/egreso, selector de turno (desde `listarTurnos` del día), tabla y tarjetas: Efectivo, Transferencias, Tarjetas (débito + crédito), Total del día, Egresos y Balance.
- Ruta bajo `/app`, link “Caja” en `AppLayout`.
- Sin tests de componentes: se validan `tsc`, `eslint` y `build` (limitación documentada).

### D9 — Tests

- Unitarios de schemas (R1, Literal, monto).
- Servicio contra PostgreSQL: usuario, turno borrado 404, append-only, listado, resumen con ceros.
- Router: 401/403, 201, 404 turno, listado y resumen.
- Correr la suite completa dos veces.

## Risks / Trade-offs

- [Doble submit] → no hay idempotency key; el usuario puede registrar dos veces. Se mitiga con confirmación en UI; un change futuro puede agregar clave.
- [Redondeo] → `Numeric(10,2)` y Decimal; la UI muestra ARS.
- [Sin vínculo de contra-asiento] → se usa concepto; se documenta.
- [Turno en estado cancelado] → se permite vincular si no está borrado; el movimiento es un hecho contable, no una reserva.
- [Sin exportación] → fuera del MVP.

## Migration Plan

Sin migración. Solo se montan rutas y se completa la UI.

## Open Questions

- ¿Se agrega una clave de idempotencia en C-08b? Recomendado si se quiere evitar doble click.
- ¿Se agrega `contra_asiento_de` en el futuro? No es necesario para el MVP.

## Decisiones aprobadas (2026-11-04)

| # | Decisión | Alternativa considerada | Impacto |
|---|---|---|---|
| 1 | **A**: seña manual al cobrar, con aviso de “seña pendiente” en la UI | Automática al reservar | Acopla C-06/C-08 y riesgo de duplicados |
| 2 | **A**: contra-asiento como fila inversa sin columna | Migración con `contra_asiento_de` | Más estructura, más complejidad |
| 3 | **A**: filtro por `fecha` única | Rango `desde`/`hasta` | El MVP cierra por día |
| 4 | **A**: cualquier turno no borrado, sin restringir por estado | C: ingreso→`atendido`, egreso→`cancelado` | Se acepta el riesgo de vincular un ingreso a un turno cancelado para simplificar señas, penalidades y garantías |
