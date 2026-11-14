# Auditoría de cobertura de reglas — C-21 reportes

**Fecha:** 2026-11-14
**Scope:** c-21-reportes (reportes de gestión de solo lectura: ocupación, facturación, ausentismo + export CSV es-AR; sin migración).
**Fuentes leídas:** knowledge-base/05_reglas_de_negocio.md; AGENTS.md (R1–R13); knowledge-base/03_actores_y_roles.md; knowledge-base/04_modelo_de_datos.md; knowledge-base/06_funcionalidades.md; openspec/changes/c-21-reportes/{proposal,specs/reports/spec,design,tasks}.md; backend/src/app/modules/reportes/{schemas,service,csv,router}.py; tests backend/test/test_reportes_*.py; frontend/src/shared/api/reportes.ts y features/reportes/{Ocupacion,Facturacion,Ausentismo}Page.tsx.

## 1. Catálogo de reglas auditadas

| ID | Texto (resumido) | Fuente | Tipo |
|---|---|---|---|
| RN-AG-01 | Antisolapamiento de agenda (sillón/profesional no superpuestos) | KB 05 | negocio |
| RN-AG-02 | Duración variable según prestación | KB 05 | negocio |
| RN-AG-03 | Asignación física obligatoria (sillon_id + profesional_id) | KB 05 | negocio |
| RN-AG-04 | Bloqueos de agenda impiden reserva | KB 05 | negocio |
| RN-AG-05 | Estados del turno (reservado/confirmado/presente/atendido/cancelado) | KB 05 | negocio |
| RN-AG-06 | Reserva pública requiere nombre/DNI/teléfono | KB 05 | negocio |
| RN-CL-01 | Nomenclatura FDI y estados de pieza | KB 05 | negocio |
| RN-CL-02 | Permisos clínicos (odontólogo edita, admin supervisa) | KB 05 | negocio |
| RN-CJ-01 | Todo cobro registra medio de pago y usuario responsable | KB 05 | negocio |
| RN-CJ-02 | Inmutabilidad contable (no borrado físico de movimientos) | KB 05 | negocio |
| RN-CJ-03 | Señas de turnos | KB 05 | negocio |
| RN-SEG-01 | Protección de rutas privadas (token JWT) | KB 05 | negocio |
| RN-SEG-02 | Borrado lógico con deleted_at | KB 05 | negocio |
| RN-G-01 | Notificaciones WhatsApp click-to-chat | KB 05 | negocio |
| R1 | Schema Pydantic con extra="forbid" | AGENTS.md | dura |
| R2 | Sin tenant_id (mono-consultorio) | AGENTS.md | dura |
| R3 | No UPDATE/DELETE físico en caja | AGENTS.md | dura |
| R4 | Cobro con medio de pago y usuario responsable | AGENTS.md | dura |
| R5 | Type hints + snake_case; migración por cambio de schema | AGENTS.md | dura |
| R6 | Turno con antisolapamiento + test de conflicto | AGENTS.md | dura |
| R7 | No any; tsc/eslint/build; componentes PascalCase | AGENTS.md | dura |
| R8 | RBAC en backend, no confiar en frontend | AGENTS.md | dura |
| R9 | No datos sensibles de salud en logs ni URL | AGENTS.md | dura |
| R10 | Superficies es-AR, montos ARS | AGENTS.md | dura |
| R11 | No commitear/pushear sin pedido | AGENTS.md | dura |
| R12 | Commits convencionales | AGENTS.md | dura |
| R13 | No borrado físico en tablas de negocio (deleted_at) | AGENTS.md | dura |

## 2. Matriz de cobertura

| Regla | Artefacto que la cubre | Estado | Verificación |
|---|---|---|---|
| RN-AG-01 | C-21 solo lee estados de turno; no crea ni reprograma turnos (D3) | ➖ | No aplica: C-21 no escribe agenda. |
| RN-AG-02 | C-21 no calcula `fin` de turnos | ➖ | No aplica: solo lectura. |
| RN-AG-03 | C-21 lee `sillon_id`/`profesional_id` de turnos existentes | ⚠️ parcial | Refleja la asignación; no la impone. |
| RN-AG-04 | C-21 lee `Bloqueo` para horas bloqueadas (ocupación) | ⚠️ parcial | Solo lectura de bloqueos existentes. |
| RN-AG-05 | `reporte_ocupacion` cuenta estados `reservado/confirmado/presente/atendido/cancelado` | ✅ | `test_reportes_ocupacion_service.py` (conteos y tasa). |
| RN-AG-06 | C-21 no expone reserva pública | ➖ | No aplica. |
| RN-CL-01 / RN-CL-02 | C-21 no toca odontograma ni ficha clínica | ➖ | No aplica. |
| RN-CJ-01 | `reporte_facturacion` agrupa `MovimientoCaja.tipo=ingreso` por `medio_pago` | ✅ | `test_reportes_facturacion_service.py` (por medio, por OS, sin OS). |
| RN-CJ-02 | C-21 es solo lectura; no escribe ni contra-asienta en caja | ➖ | No aplica: C-21 no modifica el libro. |
| RN-CJ-03 | C-21 no registra señas | ➖ | No aplica. |
| RN-SEG-01 | Endpoints de reportes exigen `Authorization: Bearer`; sin token → 401 | ✅ | `test_reportes_*_router.py::test_sin_token_401`; `test_reportes_integracion.py`. |
| RN-SEG-02 | C-21 no borra físicamente entidades de negocio | ➖ | No aplica: solo lectura. |
| RN-G-01 | C-21 no envía notificaciones | ➖ | No aplica. |
| R1 | Schemas de reportes con `extra="forbid"` | ✅ | `test_reportes_schemas.py::test_*_extra_forbid`; rechazo de campo extra. |
| R2 | C-21 no añade `tenant_id` a ninguna consulta | ✅ | Consultas sobre tablas existentes sin tenant; `test_structure.py` (ninguna tabla nueva). |
| R3 | C-21 no escribe en caja (solo lecturas) | ✅ | `reportes/service.py` solo usa `select`; sin escritura. |
| R4 | C-21 no cobra; solo lee `medio_pago` de `MovimientoCaja` | ➖ | No aplica: reportes no crea cobros. |
| R5 | Type hints + `snake_case`; sin cambio de schema → sin migración | ✅ | `reportes/*.py` tipados; `alembic heads` = `0016_auditoria`; `test_migration_revision_ids.py`. |
| R6 | C-21 no crea turnos; solo lee estados (no test de conflicto de creación) | ➖ | No aplica: C-21 no persiste turnos. |
| R7 | Frontend tipado, sin `any`, componentes PascalCase; `tsc`/`eslint`/`build` verde | ✅ | `npx tsc --noEmit`, `eslint src --max-warnings 0`, `npm run build` (C-21 archivos incluidos). |
| R8 | RBAC en backend: `admin`/`recepcion` leen global; `odontólogo` 403 en facturación/ausentismo y ocupación global; ocupación propia por `profesional_id` vinculado | ✅ | `test_reportes_ocupacion_router.py` (403 odontólogo otro profesional); `test_reportes_facturacion_router.py::test_odontologo_403`; `test_reportes_ausentismo_router.py::test_odontologo_403`; `test_reportes_integracion.py`. |
| R9 | CSV sin DNI ni datos clínicos; ningún dato sensible en URL (solo fechas e ids internos) | ✅ | `test_reportes_export_router.py::test_export_csv_r9_no_datos_clinicos`; columnas de CSV sin DNI. |
| R10 | CSV es-AR (BOM, `;`, coma decimal, `dd/mm/aaaa`); UI montos en ARS con `formatArs` | ✅ | `test_reportes_csv.py` (BOM, separador, coma decimal, fecha dd/mm/aaaa, escape); `shared/utils/format.ts`. |
| R11 | Regla de proceso: sin commit/push sin pedido explícito | ➖ | Proceso; no se commiteó ni pusheó en esta sesión. |
| R12 | Regla de proceso: commits convencionales | ➖ | Proceso; no se commiteó en esta sesión. |
| R13 | C-21 no borra físicamente `Paciente`/`Turno`/`Profesional`/`Sillon` | ➖ | No aplica: C-21 es solo lectura. |

## 3. Ambigüedades detectadas

- **RN-CJ-01 (monto cubierto por OS vs paciente):** `descuento_global` del convenio se interpreta como el porcentaje cubierto por la obra social (`monto_os = monto * descuento / 100`). La KB no especifica la fórmula exacta de copago → lectura A (descuento = cobertura OS) vs lectura B (descuento = descuento al paciente). Propuesta: mantener lectura A y registrar en `knowledge-base/10_preguntas_abiertas.md` si se requiere precisión contable.
- **D5 (turno recuperado):** no hay campo explícito de reagendado; C-21 usa heurística "paciente con N turnos en el rango → N-1 recuperados". Documentada como aproximación en `design.md` §D5 y Open Question. Pendiente de decisión de negocio.

## 4. Conflictos detectados

- Ninguno entre reglas duras (R1–R13) y C-21: C-21 respeta R2 (sin `tenant_id`), R3 (solo lectura), R8 (RBAC backend), R9 (CSV sin DNI/clinical), R13 (sin borrado físico).
- Observación (no conflicto): `require_role(*_ROLES_LECTURA, "odontologo")` en `/ocupacion` permite al odontólogo el endpoint, y `usuario_con_filtro_profesional` restringe a su propio profesional; esto es consistente con D7 y la Open Question de `design.md` (§Open Questions: odontólogo ve su propia ocupación = sí).

## 5. Cobertura faltante propuesta

### 5.1 Escenarios (Given/When/Then)
Todos los escenarios del spec `reports` ya tienen tests:
- Ocupación por sillón/profesional, rango vacío, filtro por profesional (ocupación service + router).
- Facturación por medio, desglose por OS, paciente sin afiliación, rango vacío (facturación service + router).
- Ausentismo, tasa cero, rango vacío (ausentismo service + router).
- Desde > hasta → 422; sin token → 401; odontólogo global → 403 (routers + integración).
- CSV es-AR: BOM, `;`, coma decimal, `dd/mm/aaada`, escape, R9 (csv + export router).

### 5.2 Casos de test
`test_reportes_*.py` (49 tests) cubre los escenarios anteriores. Ningún escenario del spec queda sin test.

### 5.3 Criterios para tasks.md
Todos los checklists de `tasks.md` (grupos 1 a 8) tienen verificación asociada y tests en verde.

## 6. Resumen cuantitativo (scope C-21)

- Reglas auditadas: 27 (13 RN-* + 14 R*).
- ✅ cubiertas: 11 (RN-AG-05, RN-CJ-01, RN-SEG-01, R1, R2, R3, R5, R7, R8, R9, R10).
- ⚠️ parciales: 3 (RN-AG-03, RN-AG-04 — solo lectura de datos que ellas regulan).
- ❌ sin cobertura: 0.
- ➖ no aplica: 13 (RN-AG-01/02/04/06, RN-CL-01/02, RN-CJ-02/03, RN-SEG-02, RN-G-01, R4, R6, R11, R12, R13 — reglas de escritura que C-21, de solo lectura, no toca).

## 7. Revisión crítica

- **Omisión detectada (borde de facturación):** el reporte de facturación agrupa ingresos de `MovimientoCaja` vinculados a turnos, pero los ingresos sin `turno_id` (cobros sueltos) caen bajo "sin OS" con el paciente pagando el 100%. Esto es una decisión de diseño documentada (`design.md` §D4: "si un paciente no tiene afiliación vigente, se agrupa como 'sin OS'").
- **Cómo se detectó:** lectura de `reportes/service.py::reporte_facturacion` (bloque "sin OS") + `design.md` §D4.
- **Antes:** el spec no definía el trato de movimientos sin turno ni sin afiliación.
- **Después:** documentado como "sin OS" (monto OS = 0, paciente = 100%) y probado en `test_reportes_facturacion_service.py::test_facturacion_paciente_sin_afiliacion_sin_os`.
- No se inventó ninguna regla de negocio; todas las propuestas citan RN/RN o R de KB/AGENTS.md.
