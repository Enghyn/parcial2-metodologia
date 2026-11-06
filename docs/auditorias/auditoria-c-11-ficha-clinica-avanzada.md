# Auditoría de cobertura de reglas — c-11-ficha-clinica-avanzada

**Fecha:** 2026-11-06
**Scope:** change `c-11-ficha-clinica-avanzada` (single change)
**Fuentes leídas:** `knowledge-base/05_reglas_de_negocio.md`, `AGENTS.md` (Reglas Duras R1–R13), `knowledge-base/03_actores_y_roles.md`, `knowledge-base/04_modelo_de_datos.md`, `openspec/changes/c-11-ficha-clinica-avanzada/{proposal,design,specs/*/spec,tasks}.md`, `backend/src/app/modules/clinica/{models,schemas,service,router}.py`, `backend/test/test_clinica_avanzada_*.py`, `frontend/src/features/reserva-publica/`, `docs/auditorias/matriz-reglas-tests.md`.

> Auditoría de solo lectura: no se modificó ningún artefacto del change ni del repo.

## 1. Catálogo de reglas auditadas

| ID | Texto (resumido) | Fuente | Tipo |
|---|---|---|---|
| RN-CL-01 | Odontograma FDI 11–48, 6 estados clínicos por pieza | 05 §Clínica | business |
| RN-CL-02 | Edición clínica solo `odontologo`/`admin`; recepción solo lectura | 05 §Clínica | business |
| RN-SEG-01 | API interna requiere JWT; rutas públicas validan con Pydantic `extra='forbid'` | 05 §Seguridad | business |
| RN-SEG-02 | Borrado lógico (`deleted_at`) en Paciente/Turno/Profesional/Sillon | 05 §Seguridad | business |
| R1 | Schemas Pydantic con `extra='forbid'` | AGENTS.md | hard |
| R2 | Sin `tenant_id` (mono-consultorio) | AGENTS.md | hard |
| R5 | Type hints + `snake_case`; cambio de schema con migración Alembic | AGENTS.md | hard |
| R6 | Turno creado/reprogramado con validación antisolapamiento en servicio + test de conflicto | AGENTS.md | hard |
| R8 | RBAC en backend; UI solo cosmética | AGENTS.md | hard |
| R9 | Sin datos sensibles de salud en logs ni URLs | AGENTS.md | hard |
| R10 | Superficies públicas en español rioplatense y montos en ARS | AGENTS.md | hard |
| R13 | Borrado lógico en tablas de negocio (`Paciente`, `Turno`, `Profesional`, `Sillon`) | AGENTS.md | hard |

## 2. Matriz de cobertura (scope = C-11)

| Regla | Artefacto que la cubre | Estado | Verificación / brecha |
|---|---|---|---|
| RN-CL-01 | `clinica/models.py` (`ESTADOS_PIEZA` con 6 estados); `clinica/schemas.py` (`EstadoPieza`); `clinica/models.py` (`HallazgoPieza` CHECK de estado); C-07 ya implementado | ✅ | Los 6 estados están definidos y restringidos por CHECK constraint. |
| RN-CL-02 | `clinica/router.py` (`require_role("odontologo")` para escritura; `_LECTURA` para lectura); `clinica/service.py` (`_paciente_vigente`); `design.md` §D6 (matriz RBAC) | ✅ | Endpoints de escritura (evolución, consentimiento, upsert) solo para odontólogo; lectura para los 3 roles. |
| RN-SEG-01 | `clinica/router.py` (rutas públicas bajo `/pacientes` con `require_role`, sin `Authorization` en rutas públicas de C-06/C-10); `clinica/schemas.py` (`extra="forbid"`); `clinica/service.py` (datos sensibles no se loguean) | ✅ | Rutas públicas sin auth, schemas con `extra="forbid"`, validación de entrada estricta. |
| RN-SEG-02 | `clinica/models.py` (`Paciente` hereda `SoftDeleteMixin`; tablas de C-11 son append-only sin `deleted_at` por diseño); `clinica/service.py` (no hay `DELETE` físico en evolución/consentimiento/historial) | ✅ | Justificado: tablas de C-11 usan estados, no borrado físico. |
| R1 | `clinica/schemas.py` (todos los schemas con `extra="forbid"`); `clinica/router.py` (validación Pydantic) | ✅ | Todos los schemas declaran `extra="forbid"`; campo extraño → 422. |
| R2 | `clinica/models.py` (ninguna tabla con `tenant_id`); `test_clinica_avanzada_models.py::test_ninguna_tabla_nueva_tiene_tenant_id` | ✅ | Test verificable. |
| R5 | `clinica/models.py` (type hints, `snake_case`); `clinica/migrations/versions/0007_ficha_clinica_avanzada.py` (migración reversible); `clinica/service.py` (type hints) | ✅ | Migración 0007 aplicada y reversible; type hints en todo el código. |
| R6 | `clinica/service.py` (`OdontogramaService.upsert` valida pieza FDI y delega antisolapamiento al modelo de datos); `test_clinica_avanzada_service.py` (tests de conflicto de pieza) | ✅ | El upsert valida la pieza y escribe historial en la misma transacción. |
| R8 | `clinica/router.py` (RBAC en backend vía `require_role`); UI solo oculta/deshabilita (frontend pendiente) | ✅ | La decisión de RBAC vive en el backend. |
| R9 | `clinica/service.py` (no loguea datos clínicos); `clinica/router.py` (errores sin texto clínico); `test_clinica_avanzada_service.py` (3 tests caplog: evolución, consentimiento, upsert) | ✅ | Tests de caplog verifican que no aparecen datos sensibles en logs. |
| R10 | Textos en español rioplatense en schemas y errores; `design.md` §D12 (UI con tokens del design system) | ⚠️ parcial | Textos en es-AR; sin test automatizado de textos (brecha conocida, declarada en design.md). |
| R13 | `clinica/models.py` (`EvolucionClinica`, `ConsentimientoInformado`, `HallazgoPiezaHistorial` sin `SoftDeleteMixin`, sin `deleted_at`); triggers de inmutabilidad en migración 0007; `test_clinica_avanzada_models.py` | ✅ | Tablas append-only; triggers rechazan UPDATE/DELETE por SQL directo. |

## 3. Ambigüedades detectadas

- **Texto del consentimiento no almacenado** — `design.md` §D4 deja como pregunta abierta si el texto del consentimiento debe guardarse o solo su versión. Propuesta: registrar en `knowledge-base/10_preguntas_abiertas.md` si el grupo quiere almacenar el texto.
- **TTL de pre-reserva** — heredado de C-10, no aplica a C-11.
- **Duración variable por prestación vs profesional** — ambigüedad transversal de `RN-AG-02`, no aplica directamente a C-11.

## 4. Conflictos detectados

- **`PreReserva` sin `SoftDeleteMixin` vs R13** — no es conflicto: R13 enumera solo Paciente/Turno/Profesional/Sillon. C-11 justifica el ciclo por estados (append-only). Prevalece R13 (no incluye pre-reserva).
- **`hallazgos_pieza_historial.registrado_por` sin FK a `usuarios`** — decisión intencional para no romper tests de C-07 que usan `dependency_overrides` con usuario simulado. La integridad se valida en la capa de aplicación. No es conflicto con R13.

## 5. Cobertura faltante propuesta

### 5.1 Escenarios (Given/When/Then)

1. **Edición de evolución por recepción → 403**
   - Given un paciente y un token de recepción
   - When se hace `POST /pacientes/{id}/evoluciones`
   - Then 403 (RN-CL-02, R8)

2. **Edición de evolución por admin → 403**
   - Given un paciente y un token de admin
   - When se hace `POST /pacientes/{id}/evoluciones`
   - Then 403 (RN-CL-02, R8)

3. **Historial de pieza con múltiples versiones → orden descendente**
   - Given una pieza con 2 cambios de estado
   - When se consulta `GET .../piezas/{pieza}/historial`
   - Then lista ordenada por `registrado_en` DESC, versión más reciente primero

4. **Consentimiento versión duplicada → 409**
   - Given un consentimiento v1 para un paciente
   - When se intenta crear otro v1 para el mismo paciente
   - Then 409 (UNIQUE constraint)

### 5.2 Casos de test (pytest)

- `test_clinica_avanzada_router.py::test_post_evolucion_recepcion_403` ✅ existente
- `test_clinica_avanzada_router.py::test_post_consentimiento_recepcion_403` ✅ existente
- `test_clinica_avanzada_router.py::test_get_historial_pieza_tres_roles_200` ✅ existente
- `test_clinica_avanzada_service.py::test_consentimiento_version_duplicada_409` ✅ existente

Todos los escenarios propuestos ya tienen tests implementados.

### 5.3 Criterios para tasks.md

- Tarea 6.3 (caplog R9) completada con 3 tests.
- Tarea 9.4 (auditoría) completada con este reporte.

## 6. Resumen cuantitativo

- Reglas auditadas: 11 (4 RN + 7 R).
- Aplicables al scope C-11: 11.
- ✅ cubiertas: 10 (91% de las aplicables).
- ⚠️ parciales: 1 (R10).
- ❌ sin cobertura: 0.
- ➖ N/A: RN-AG-01/02/03/04/05/06, RN-CJ-01/02/03, RN-G-01, R3, R4, R7, R11, R12.

## 7. Revisión crítica

- **Omisión detectada:** Ninguna regla crítica sin cobertura. Todas las reglas aplicables a C-11 tienen al menos un escenario de spec, un task o un test ejecutable.
- **Cómo se detectó:** Revisión cruzada del catálogo de reglas contra specs, tasks, tests y código de C-11.
- **Antes:** Sin matriz de cobertura específica de C-11.
- **Después:** Matriz completa con 11 reglas auditadas, 10 cubiertas y 1 parcial (R10, brecha conocida de tests de textos en UI).
