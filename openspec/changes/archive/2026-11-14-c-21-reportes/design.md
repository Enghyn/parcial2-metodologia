# Design — C-21 reportes

## Context

Ver `proposal.md` — Why. El punto de partida real:

- `Turno` (estado `reservado`/`confirmado`/`presente`/`atendido`/`cancelado`, `sillon_id`, `profesional_id`, `paciente_id`, `inicio`/`fin`) existe desde C-04/C-09a.
- `MovimientoCaja` (`tipo`, `medio_pago`, `monto`, `turno_id`, `usuario_id`, `fecha`) existe desde C-02/C-08/C-12; es append-only y no se toca en C-21.
- `Paciente` (`obra_social`, `nro_afiliado`) existe desde C-02; la afiliación a OS/convenio vive en C-13a.
- `Presupuesto` existe desde C-16; no es fuente de facturación real para reportes (se usa MovimientoCaja).
- C-12 ya expone `GET /api/v1/caja/resumen-diario` y export CSV del libro; C-21 reutiliza la lógica de agregación por medio de pago y el formateador CSV es-AR de C-12.
- No hay migración en C-21: solo consultas de lectura sobre tablas existentes (R5 no obliga a migración sin cambio de schema; R2 prohíbe `tenant_id`).
- La KB no define `US-041` (citada en `CHANGES.md` como "Leer antes: KB 06"); `knowledge-base/06_funcionalidades.md` solo llega a `US-011`. No se inventa: se registra como pregunta abierta.
- Design system: revisión 1, aprobada 2026-11-04, modo `system-and-mockups`.

## Goals / Non-Goals

**Goals:**

- Exponer reportes de solo lectura: ocupación por sillón/profesional, facturación por medio de pago/OS, ausentismo y recuperación.
- Soportar filtros `desde`/`hasta` (día calendario ART) con default de 30 días.
- Exportar cada reporte a CSV es-AR (BOM UTF-8, separador `;`, coma decimal, `dd/mm/aaaa`).
- Cumplir RBAC en backend (R8) y no exponer datos sensibles de salud en URLs ni logs (R9).
- No crear tablas ni migraciones.

**Non-Goals:**

- Export masivo de varios días en un solo archivo.
- Envío programado por email ni dashboards en tiempo real.
- Modificar `Turno`, `MovimientoCaja` ni ninguna tabla existente.
- Integración con ARCA/Mercado Pago ni facturación electrónica.
- Multitenencia: sin `tenant_id` (R2).

## Decisions

### D1 — Reportes como capacidad nueva `reports`, solo lectura

Se crea `openspec/specs/reports/spec.md` con tres reportes y sus export CSV. Cada reporte es un endpoint `GET` que lee de tablas existentes y devuelve JSON; la variante `.../export.csv` devuelve el mismo resultado en CSV.

- **Por qué**: C-21 no modifica comportamiento de ninguna capacidad existente (cash-ledger, agenda, insurance-coverage), por tanto no hay capabilities modificadas, solo una nueva.
- **Alternativa descartada**: agregar requisitos a `cash-ledger` o `agenda`. Diludiría esos contratos con consultas analíticas que no son parte de su propósito.

### D2 — Endpoints y rutas

- `GET /api/v1/reportes/ocupacion?desde&hasta&profesional_id&sillon_id`
- `GET /api/v1/reportes/facturacion?desde&hasta`
- `GET /api/v1/reportes/ausentismo?desde&hasta`
- Variantes `.../export.csv` para cada uno.

Todos validan `desde <= hasta` (422 si no), default `desde = hoy - 30 días`, `hasta = hoy`, día calendario ART.

- **Por qué**: coherencia con `resumen-diario` de C-08 y con el uso de fecha ART en todo el sistema.
- **R9**: ningún endpoint recibe ni expone DNI, diagnósticos ni tokens en la URL; los filtros son solo fechas e ids internos.

### D3 — Cálculo de ocupación

Sobre `Turno`: conteos por estado (`reservado`, `confirmado`, `presente`, `atendido`, `cancelado`) agrupados por `sillon_id` y `profesional_id`, dentro del rango. Tasa de ocupación = `atendido / (reservado + confirmado + presente + atendido)` del período (cero si no hay turnos). Horas bloqueadas desde `Bloqueo` (C-03/C-09a) si existe; si no, cero.

- **Por qué**: usa solo tablas existentes; no hay tabla de "asistencia" dedicada en el MVP.

### D4 — Cálculo de facturación

Sobre `MovimientoCaja` tipo `ingreso`, agrupado por `medio_pago`. Para desglose por OS: se une `Turno.paciente_id` → `Paciente` → afiliación OS/convenio vigente (C-13a); si no hay afiliación vigente, se agrupa como "sin OS" (paciente paga 100%).

- **Por qué**: la facturación real es el libro de caja (C-08/C-12), no los presupuestos (C-16), que son estimaciones.

### D5 — Cálculo de ausentismo y recuperación

Ausentismo = turnos `cancelado` o con `estado` distinto de `atendido`/`presente` en el rango. Recuperados = turnos del mismo paciente reagendados (se detecta por paciente con varios turnos en el rango; se deja como heurística documentada). Tasa = ausentes / totales.

- **Por qué**: no hay campo explícito de "reagendado" en el MVP; se documenta como aproximación y pregunta abierta.

### D6 — Export CSV reutilizable de C-12

Se reutiliza el formateador CSV de C-12 (BOM UTF-8, separador `;`, coma decimal, `dd/mm/aaaa`, `Content-Disposition: attachment`) con las columnas de cada reporte. Sin DNI ni datos clínicos (R9).

- **Por qué**: evita duplicar el formateador y garantiza consistencia es-AR entre caja y reportes.

### D7 — RBAC

| Acción | admin | recepcion | odontologo |
|---|---|---|---|
| Leer ocupación global | sí | sí | 403 |
| Leer propia ocupación | sí | sí | sí (profesional_id = propio) |
| Leer facturación global | sí | sí | 403 |
| Leer ausentismo global | sí | sí | 403 |
| Export CSV de cualquier reporte | sí | sí | 403 |

El backend es la autoridad; la UI solo oculta o deshabilita (R8).

- **Por qué**: los reportes de caja y ausentismo contienen información de gestión restringida.

### D8 — Frontend

- `shared/api/reportes.ts`: tipos y funciones de los tres reportes + export (blob).
- `features/reportes/OcupacionPage.tsx`, `FacturacionPage.tsx`, `AusentismoPage.tsx` con filtros de rango, tabla de resumen y botón de export.
- `app/router.tsx`: rutas `/app/reportes/*` protegidas.
- Sin tests de componentes (limitación del proyecto): se validan `tsc`, `eslint` y `build`.

## Risks / Trade-offs

- **Ausentismo sin campo de reagendado** → heurística por paciente; se documenta como aproximación y se deja como mejora futura. Residual: tasa de recuperación puede subestimar.
- **Desglose por OS depende de C-13a** → si un paciente no tiene afiliación vigente, se agrupa como "sin OS"; se asume convenio vigente según C-13a.
- **Solo lectura, sin migración** → R5 no exige migración, pero cualquier cambio futuro de schema en tablas leídas puede afectar los reportes; se valida con tests de integración.
- **R9 en CSV** → se excluyen DNI y datos clínicos; solo ids, conceptos y montos.
- **Rendimiento** → consultas sobre `Turno` y `MovimientoCaja` con índices existentes; volumen bajo (consultorio de 2–3 sillones).

## Migration Plan

Ninguno. C-21 es de solo lectura sobre tablas existentes; no crea, altera ni borra tablas ni columnas. Se valida con `alembic heads` para confirmar que no hay heads pendientes antes de implementar.

## Open Questions

- **¿Existe `US-041`?** `CHANGES.md` cita "Leer antes: KB 06 (US-041)" pero `knowledge-base/06_funcionalidades.md` solo define US-001 a US-011. No se cita ni se inventa; hay que decidir si se agrega a la KB o se corrige la referencia en `CHANGES.md`.
- **¿Detección de turno recuperado?** No hay campo explícito de reagendado. Default: heurística por paciente con varios turnos en el rango. Si el negocio lo exige, se agrega un campo en `Turno` (migración futura).
- **¿Ocupación por horas o por turnos?** Default: conteo de turnos y tasa sobre atendidos; se deja abierta la métrica de horas si se requiere precisión de capacidad.
- **¿Odontólogo ve su propia ocupación?** Default: sí, limitada a su `profesional_id`. Si se quiere total restricción, cambia a 403.

## UI Mockups

- Design system revision: 1
- Decision: yes (project policy, system-and-mockups)
- Mockups: openspec/changes/c-21-reportes/mockups/
- Approval: approved (2026-11-14, by user)
- Preview: manual (Playwright MCP no disponible; ver pasos en mockups/README.md)
- Visual verify: pending

### Pantallas y estados que requieren mockup

Todos los mockups usan `design-system/tokens.css`, `design-system/brand.js` y assets locales; no se crean tokens nuevos. Se renderizan a 390×844 y 1440×900.

1. **Ocupación por sillón/profesional** (`ocupacion.html`): filtros de rango (desde/hasta), selector de profesional/sillón, tarjetas de ocupación por sillón (turnos por estado, tasa), tabla de detalle y botón de export CSV.
2. **Facturación por medio de pago/OS** (`facturacion.html`): filtros de rango, tarjetas de totales por medio (efectivo, transferencia, tarjeta, débito, otro), desglose por OS (monto OS / copago / paciente), tabla y export CSV.
3. **Ausentismo y recuperación** (`ausentismo.html`): filtros de rango, tarjetas de cancelados, no presentados, recuperados y tasa de ausentismo, tabla de turnos y export CSV.
4. **Estado vacío / sin datos** (estado dentro de cada pantalla): mensaje de estado vacío y CTA para ajustar el rango.
5. **Estados transversales**: carga, error de red, 403 por rol, rango inválido (422) y éxito de export, en mobile (390×844) y desktop (1440×900).

## Decisiones que requieren aprobación humana

Por gobernanza MEDIO, antes de implementar se deben confirmar: detección de turno recuperado (heurística vs campo nuevo), ocupación por turnos vs horas, lectura propia del odontólogo y el tratamiento de `US-041` (agregar a KB o corregir CHANGES.md). Si alguna cambia, se actualizan `proposal.md`, el spec `reports` y `tasks.md` antes de escribir código.
