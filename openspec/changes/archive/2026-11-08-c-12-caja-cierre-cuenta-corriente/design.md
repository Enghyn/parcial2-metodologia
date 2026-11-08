# Design — C-12 caja-cierre-cuenta-corriente

## Context

Ver `proposal.md` — Why. C-08 implementó `MovimientoCaja` (libro append-only), `POST /caja/movimientos`, `GET /caja/movimientos`, `GET /caja/resumen-diario`, guardas `ImmutableLedgerMixin` y triggers de base (`0003`), pantalla `/app/caja` y tests. No existe cierre de período, ni cuenta corriente por paciente, ni ajustes auditados, ni export CSV. La última migración aplicada es `0007_ficha_clinica_avanzada`; la de C-12 es `0008_caja_cierre_cuenta_corriente`. El consultorio opera en ART (`America/Argentina/Buenos_Aires`) y cierra caja por día calendario. Gobernanza CRÍTICO: este diseño solo se implementa con aprobación humana explícita.

## Goals / Non-Goals

**Goals:**

- Cierre diario aprobado exclusivamente por `admin` con balance calculado del libro y bloqueo del período (409 en día cerrado).
- Cuenta corriente por paciente con saldo derivado de movimientos vinculados a sus turnos.
- Ajustes auditados: contra-asiento vinculado al movimiento corregido, motivo y aprobador; nunca UPDATE/DELETE del libro original (RN-CJ-02, R3, R13).
- Export CSV (UTF-8) del libro/día y del cierre, sin datos clínicos (R9).
- Migración `0008` reversible con las tablas `cierres_caja`, `cuentas_corrientes_paciente`, `ajustes_caja`.
- RBAC: cierre y ajuste solo `admin`; consulta de cierre, cuenta corriente y export para `admin` y `recepcion`; `odontologo` recibe 403 (R8).

**Non-Goals:**

- Conciliación bancaria o integración con Mercado Pago/ARCA.
- Clave de idempotencia para doble submit (deferido a cambio futuro).
- Columna `contra_asiento_de` dedicada (el vínculo vive en `ajustes_caja`).
- Cierre multi-sede (mono-consultorio, sin `tenant_id`, R2).
- Export de varios días a la vez ni programación automática de cierres.

## Decisions

### D1 — Cierre como entidad `CierreCaja` con `fecha_dia` único

Tabla `cierres_caja(id, fecha_dia UNIQUE, estado, balance, total_ingresos, total_egresos, aprobado_por, aprobado_en, created_at)`. `POST /cierres` (solo `admin`) calcula totales desde `movimientos_caja` del día ART, inserta fila en `cerrado` y bloquea nuevos movimientos con esa fecha (409). `GET /cierres` lista estados para `admin`/`recepcion`.

- **Por qué**: una fila por día hace el bloqueo de período una consulta por `fecha_dia` y estado; el historial de cierres queda para auditoría (C-20, C-21).
- **Alternativa descartada**: solo una bandera `bloqueado` en memoria (no persiste, no sobrevive reinicios).
- **Consecuencia**: `registrar` debe consultar `cierres_caja` antes de insertar; transacción para evitar race conditions (SELECT ... FOR UPDATE o constraint de exclusión).

### D2 — Cuenta corriente como tabla derivada `cuentas_corrientes_paciente`

Tabla `cuentas_corrientes_paciente(paciente_id UNIQUE, saldo NUMERIC(10,2), actualizado_en)`. El saldo se deriva de `movimientos_caja` filtrados por `turno_id → paciente` (ingresos menos egresos); no es fuente de verdad autónoma. Se recalcula al cerrar el día y al registrar movimientos del paciente.

- **Por qué**: consultas de saldo O(1) y compatibles con C-13a/C-16/C-17 (presupuestos, pagos, cobertura) que dependen de C-12.
- **Alternativa descartada**: vista SQL pura (más simple pero menos controlable en tests y sin `actualizado_en` para detección de stale).
- **Riesgo aceptado**: posible desincronía si se inserta movimiento fuera del servicio; se mitiga recalculando en cada escritura de caja.

### D3 — AjusteCaja vincula original + contra-asiento

Tabla `ajustes_caja(id, movimiento_corregido_id FK, movimiento_ajuste_id FK, motivo, fecha, usuario_aprobador_id FK)`. `usuario_aprobador_id` solo `admin`. Ambas tablas (`movimientos_caja` y `ajustes_caja`) append-only: triggers bloquean UPDATE/DELETE.

- **Por qué**: R3/RN-CJ-02 prohíbe tocar el asiento original; el contra-asiento conserva el motivo y quién lo aprobó. C-20/auditoría necesita el vínculo estructurado.
- **Alternativa descartada**: columna `contra_asiento_de` en `movimientos_caja` (requiere migración adicional y no agrega valor operativo inmediato).
- **Consecuencia**: leer la relación requiere join con `ajustes_caja`; documentado en el diseño.

### D4 — Export CSV plano y local

`GET /caja/export?fecha=YYYY-MM-DD` devuelve `text/csv` UTF-8 con columnas `fecha,tipo,medio_pago,monto,concepto,turno_id,usuario_id` más fila de totales. Si se pasa un cierre, exporta los movimientos de ese día. Solo `admin`/`recepcion`. Nunca incluye datos de salud ni clínicos (R9).

- **Por qué**: requisito explícito de C-12; C-20/auditoría lo consume.
- **Alternativa descartada**: export Excel/JSON (CSV es el estándar del consultorio y suficiente para el MVP académico).

### D5 — Día calendario ART

Todos los filtros de fecha usan `inicio_dia`/`fin_dia` de `app/core/timezone.py` (zona `America/Argentina/Buenos_Aires`), como C-08 y C-09a. Sin `fecha`, usa `ahora().date()`.

- **Por qué**: la caja se cierra por día del consultorio, no UTC (evita desfase de 3 horas).
- **Alternativa descartada**: rango UTC (desfase y confusión operativa).

### D6 — RBAC de caja extendido

- `admin`: cierre, ajuste, consulta cierre, cuenta corriente, export.
- `recepcion`: consulta cierre, cuenta corriente, export, registro de movimientos (C-08).
- `odontologo`: 403 en todos los endpoints de caja (R8).
- Sin token: 401.

- **Por qué**: R4 (usuario responsable del JWT), R8 (autoridad en backend), R9 (sin datos sensibles en URL/logs).

### D7 — Migración `0008` reversible, sin `tenant_id`, type hints estrictos

`upgrade` crea `cierres_caja`, `cuentas_corrientes_paciente`, `ajustes_caja` con FKs, check constraints (`saldo` puede ser negativo, `balance` cualquiera, `monto > 0` ya está en `movimientos_caja`) e índices. `downgrade` las elimina sin objetos huérfanos. Todo con type hints, `snake_case`, y migración Alembic obligatoria (R5). Sin `tenant_id` (R2).

### D8 — Frontend: dos páginas y extensión de `shared/api/caja.ts`

- `/app/caja/cierre`: formulario "Cerrar día" (solo admin), lista de cierres con estado/balance, botón export CSV del cierre.
- `/app/caja/cuenta-corriente`: buscador de paciente, saldo y detalle de movimientos; lista de saldos pendientes.
- `shared/api/caja.ts` agrega `cerrarCaja`, `listarCierres`, `cuentaCorriente`, `cuentasCorrientes`, `exportCajaCsv`.
- `app/router.tsx` y `app/layout.tsx` (links).
- Sin `any` (R7, tsconfig strict), componentes `PascalCase`, montos con `formatArs` (R10).

## Risks / Trade-offs

- [Race condition en cierre] → dos cierres concurrentes del mismo día; mitigado con transacción + UNIQUE `fecha_dia` y 409 en `registrar` si el día ya está cerrado.
- [Desincronía de saldo derivado] → `cuentas_corrientes_paciente` es caché; se recalcula en escritura de caja y cierre. Si se inserta fuera del servicio, queda stale hasta el próximo recálculo.
- [Sin clave de idempotencia] → doble submit posible; se mitiga con confirmación en UI; cambio futuro puede agregar clave.
- [Vínculo de ajuste por tabla aparte] → se lee con join; se documenta y se acepta por simplicidad.
- [Turno cancelado vinculado] → se permite (hecho contable), como en C-08 (D3b).

## Migration Plan

1. `alembic revision --autogenerate -m "0008_caja_cierre_cuenta_corriente"` (o escrita a mano si autogenerate no captura todo).
2. `upgrade` crea las 3 tablas con índices/FKs.
3. Los servicios nuevos usan las tablas; `registrar` consulta `cierres_caja` antes de insertar.
4. `downgrade` elimina las 3 tablas. Idempotente: si ya está aplicada, `upgrade head` no hace nada.

## Open Questions

- ¿Permitir "reabrir" un día cerrado (`estado = reabierto`)? Recomendado solo para corregir errores de cierre, con auditoría; se deja como decisión abierta por gobernanza CRÍTICO.
- ¿El saldo de cuenta corriente se expone también en `/pacientes/{id}` (ficha clínica C-07/C-11)? No en C-12; posible en C-11b/C-16.
- ¿Export CSV con fila de totales o solo movimientos? Se incluye fila de totales (balance del día).

## Decisiones aprobadas (pendiente revisión humana)

| # | Decisión | Alternativa considerada | Impacto |
|---|----------|-------------------------|---------|
| 1 | **A**: `CierreCaja` con `fecha_dia` único + bloqueo 409 | Solo bandera en memoria | Persistencia y auditoría de cierres |
| 2 | **A**: saldo derivado en tabla materializada | Vista SQL pura | Consultas rápidas, posible stale controlado |
| 3 | **A**: `AjusteCaja` con par original/contra-asiento | Columna `contra_asiento_de` | Vínculo estructurado para auditoría (C-20) |
| 4 | **A**: CSV UTF-8, columnas del movimiento | Excel/JSON | Simplicidad y consumo por auditoría |
| 5 | **A**: cierre y ajuste solo `admin` | `recepcion` también cierra | Refuerza R4 y segregación de funciones |
