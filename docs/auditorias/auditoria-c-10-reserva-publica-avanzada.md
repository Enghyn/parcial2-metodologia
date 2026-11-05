# Auditoría de cobertura de reglas — c-10-reserva-publica-avanzada

**Fecha:** 2026-11-05
**Scope:** change `c-10-reserva-publica-avanzada` (single change)
**Fuentes leídas:** `knowledge-base/05_reglas_de_negocio.md`, `AGENTS.md` (Reglas Duras R1–R13), `knowledge-base/03_actores_y_roles.md`, `knowledge-base/04_modelo_de_datos.md`, `knowledge-base/06_funcionalidades.md`, `knowledge-base/07_flujos_principales.md`, `openspec/changes/c-10-reserva-publica-avanzada/{proposal,design,specs/*/spec,tasks}.md`, `backend/src/app/modules/public/*`, `backend/src/app/modules/agenda/{models,service,schemas}.py`, `backend/src/app/core/{config,errors,rate_limit}.py`, `backend/test/test_public_*.py`, `backend/test/test_agenda_*.py`, `backend/test/test_models_structure.py`, `backend/test/test_migration_*.py`, `frontend/test/{preReserva,rateLimit,publicApi}.test.ts`, `frontend/src/shared/*`, `docs/auditorias/matriz-reglas-tests.md`.

> Auditoría de solo lectura: no se modificó ningún artefacto del change ni del repo.

## 1. Catálogo de reglas auditadas

| ID | Texto (resumido) | Fuente | Tipo |
|---|---|---|---|
| RN-AG-01 | Un sillón/profesional no puede tener dos turnos activos superpuestos; 409 indicando recurso | 05 §Agenda | business |
| RN-AG-02 | Duración variable según prestación; `fin = inicio + duracion_min` | 05 §Agenda | business |
| RN-AG-03 | Todo turno debe tener `sillon_id` y `profesional_id` obligatorios | 05 §Agenda | business |
| RN-AG-04 | Bloqueos (mantenimiento/feriados/ausencias) impiden reserva y cuentan como ocupación | 05 §Agenda | business |
| RN-AG-05 | Estados `reservado→confirmado→presente→atendido` (o `cancelado`); cancelar libera | 05 §Agenda | business |
| RN-AG-06 | Reserva pública exige Nombre completo, DNI y Teléfono válido | 05 §Agenda | business |
| RN-CL-01 | Odontograma FDI 11–48, 6 estados clínicos por pieza | 05 §Clínica | business |
| RN-CL-02 | Edición clínica solo `odontologo`/`admin`; recepción solo lectura | 05 §Clínica | business |
| RN-CJ-01 | Todo movimiento registra fecha, monto>0, medio, concepto, usuario | 05 §Caja | business |
| RN-CJ-02 | Prohibido DELETE físico en caja; compensatorios | 05 §Caja | business |
| RN-CJ-03 | Señas anticipadas vinculadas al turno; se deducen al liquidar | 05 §Caja | business |
| RN-SEG-01 | API interna requiere JWT; rutas públicas validan con Pydantic `extra='forbid'` | 05 §Seguridad | business |
| RN-SEG-02 | Borrado lógico (`deleted_at`) en Paciente/Turno/Profesional/Sillon | 05 §Seguridad | business |
| RN-G-01 | Notificaciones/WhatsApp click-to-chat `wa.me/` | 05 §Comunicación | business |
| R1 | Schemas Pydantic con `extra='forbid'` | AGENTS.md | hard |
| R2 | Sin `tenant_id` (mono-consultorio) | AGENTS.md | hard |
| R3 | Sin UPDATE/DELETE físico en caja | AGENTS.md | hard |
| R4 | Cobro registra medio de pago y usuario | AGENTS.md | hard |
| R5 | Type hints + snake_case; cambio de schema con migración Alembic | AGENTS.md | hard |
| R6 | Turno creado/reprogramado con validación antisolapamiento en servicio + test de conflicto | AGENTS.md | hard |
| R7 | Sin `any`; TS strict; componentes PascalCase | AGENTS.md | hard |
| R8 | RBAC en backend; UI solo cosmética | AGENTS.md | hard |
| R9 | Sin datos sensibles de salud en logs ni URLs | AGENTS.md | hard |
| R10 | Superficies públicas en español rioplatense, montos ARS | AGENTS.md | hard |
| R11 | No commitear/pushear sin pedido | AGENTS.md | hard |
| R12 | Commits conventional sin co-autoría IA | AGENTS.md | hard |
| R13 | Borrado lógico en Paciente/Turno/Profesional/Sillon | AGENTS.md | hard |

## 2. Matriz de cobertura (scope = C-10)

| Regla | Artefacto que la cubre | Estado | Verificación / brecha |
|---|---|---|---|
| RN-AG-01 | `specs/agenda/spec.md` (escenarios "Reprogramación que choca", "El antisolapamiento no cambia"); `service.py` reusa `TurnoService.crear/reprogramar` (R6); `test_agenda_conflicts.py` (C-04) | ✅ | Spec con outcome 409. Falta test de conflicto específico de reprogramación pública (tasks 7.4 marcada [x] pero `test_public_reprogramar.py` no existe) |
| RN-AG-02 | `schemas.py` `PreReservaCreate.duracion_min: gt=0`; `service.py` `fin = inicio + timedelta(minutes=duracion_min)`; `models.py` CHECK `fin = inicio + duracion_min*interval` | ⚠️ parcial | No hay escenario/test que verifique el cálculo de `fin` en pre-reserva ni que la duración varíe por prestación en el portal |
| RN-AG-03 | `models.py` `PreReserva.sillon_id`/`profesional_id` NOT NULL; `service.crear_pre_reserva` valida recursos activos; `Turno` NOT NULL | ✅ | Code path + modelo. Sin scenario explícito en spec delta, pero la asignación física es invariante del modelo |
| RN-AG-04 | `specs/public-reservation/spec.md` ("Retención de un hueco ocupado" incluye bloqueo); `service.crear_pre_reserva` consulta `Bloqueo` y `slot_libre` | ✅ | Scenario con outcome 409. Falta test HTTP/integración que ejercite el caso de bloqueo en pre-reserva |
| RN-AG-05 | `specs/public-reservation/spec.md` ("Reprogramación exitosa" 200, "Turno no reprogramable" 409); `service.reprogramar_por_token` valida `reservado`/`confirmado`; cancelación pública existente | ✅ | Scenario con outcomes. Falta test de estados no reprogramables (tasks 7.1 marcada [x] sin archivo) |
| RN-AG-06 | `test_public_schemas.py::test_paciente_requiere_nombre_dni_telefono`; `PacientePublicoIn` con `min_length=1` | ✅ | Test puro ejecutable. Pre-reserva no pide datos (correcto, R9) |
| RN-CL-01 | — | ➖ N/A | No toca clínica/odontograma |
| RN-CL-02 | — | ➖ N/A | No toca clínica |
| RN-CJ-01 | — | ➖ N/A | No toca caja |
| RN-CJ-02 | — | ➖ N/A | No toca caja |
| RN-CJ-03 | — | ➖ N/A | No toca señas |
| RN-SEG-01 | `specs/public-reservation/spec.md` ("Acceso sin token exitoso", "Campo extra rechazado" 422, "Acceso acotado por token" 404); router sin `Authorization` | ✅ | Scenario con outcomes. Falta test HTTP para endpoints nuevos (pre-reservas, reprogramar, QR) |
| RN-SEG-02 | `test_soft_delete.py`; `Turno`/`Paciente` SoftDeleteMixin; `PreReserva` sin soft delete (justificado D1) | ✅ | Justificado: R13 nombra solo Paciente/Turno/Profesional/Sillon; pre-reserva usa estados |
| RN-G-01 | — | ➖ N/A | C-10 no toca WhatsApp; agrega QR (capacidad nueva sin regla RN existente) |
| R1 | `specs/public-reservation/spec.md` ("Campo extra rechazado" 422, "Endpoint público nuevo también rechaza campos extra", "La reprogramación no cambia de recurso ni de duración" 422); schemas con `extra="forbid"` | ✅ | Scenario con outcome 422. Falta test unitario para `PreReservaCreate`/`ReprogramarPublico` extra forbid |
| R2 | `test_models_structure.py::test_ninguna_tabla_tiene_tenant_id`; `PreReserva` sin tenant_id | ✅ | Test ejecutable |
| R3 | — | ➖ N/A | No toca caja |
| R4 | — | ➖ N/A | No toca cobros |
| R5 | `backend/src/app/db/migrations/versions/0006_pre_reserva_origen.py`; type hints en `service.py`/`schemas.py`; `ruff` | ✅ | Migración reversible. Falta `test_migration_0006.py` (tasks 3.1 marcada [x] sin archivo) |
| R6 | `specs/agenda/spec.md` ("Las pre-reservas públicas no bloquean la agenda interna"); `service.py` delega en `TurnoService`; `detectar_conflicto` sin cambios | ✅ | Scenario con outcome 201/409. Falta test de conflicto de reprogramación pública |
| R7 | `tsc --noEmit`, `eslint`, `build` (tasks 11.9); sin `any` en helpers | ⚠️ parcial | Sin tests de componentes React (limitación del harness, declarada) |
| R8 | `specs/public-reservation/spec.md` ("Acceso acotado por token" 404); público sin auth por diseño; agenda interna sin cambios | ✅ | Scenario con outcome 404. Falta test HTTP de 404 por token inválido en endpoints nuevos |
| R9 | `specs/public-reservation/spec.md` ("Retención sin datos sensibles", "El QR no filtra datos del paciente"); `test_public_service.py::test_reservar_no_loguea_datos_paciente` (C-06); token opaco UUID | ✅ | Scenario con outcomes. Falta test `caplog` para pre-reserva (tasks 6.6 marcada [x] sin archivo) |
| R10 | Textos es-AR en frontend (`mensajeRateLimit`, mockups); `R10` en tasks 11.8 | ⚠️ parcial | Sin test automatizado de textos (brecha conocida) |
| R11 | Regla de proceso | ➖ N/A | No aplica a auditoría |
| R12 | Regla de proceso | ➖ N/A | No aplica a auditoría |
| R13 | `test_soft_delete.py`; `PreReserva` sin `SoftDeleteMixin` y sin `deleted_at` (D1) | ✅ | Justificado por D1: ciclo cubierto por estados; aplicación nunca hace DELETE (test de estructura pendiente) |

## 3. Ambigüedades detectadas

- **RN-AG-07 inexistente (transversal)** — `CHANGES.md` cita `RN-AG-07` para este change, pero `knowledge-base/05_reglas_de_negocio.md` solo define `RN-AG-01` a `RN-AG-06`. Dos lecturas: (a) crear la regla con la redacción propuesta en `design.md` §Open Questions #1 (pre-reserva con TTL, confirmación por token, reprogramación pública con ventana); (b) no crearla y basarse en `RN-AG-06` + la ventana de cancelación de C-09a. **Propuesta:** registrar la decisión en `knowledge-base/10_preguntas_abiertas.md` antes de archivar; si no se crea, corregir la cita en `CHANGES.md`. El change ya lo registra correctamente como pregunta abierta (no como regla vigente).

- **TTL de pre-reserva (10 min)** — configurable; ¿es el valor correcto para el consultorio? (`design.md` §Open Questions #2). Propuesta: confirmar con el grupo; cambiarlo no altera specs ni tareas.

- **Reprogramación pública no permite cambiar de profesional** — D6 lo excluye (solo mueve el horario). ¿Debe permitirse si el paciente lo pide? (`design.md` §Open Questions #3). Propuesta: si se habilita, merece su propio change (cambio de contrato).

- **QR imprimible desde la agenda interna** — C-10 solo expone el SVG y lo muestra en `/reservar`. ¿Debe la agenda interna poder imprimirlo? (`design.md` §Open Questions #4). Propuesta: dejar para C-18.

- **Ventana de reprogramación vs cancelación** — D6 las separa (`reprogramacion_min_horas` y `cancelacion_min_horas`, ambas default 12). ¿Deben ser la misma? No está decidido en la KB. Propuesta: registrar en `knowledge-base/10_preguntas_abiertas.md` si el grupo quiere un único valor.

- **Duración variable: ¿por prestación o por profesional?** — `05` dice prestación; `Profesional.duracion_default_min` existe en el modelo (04). Ambigüedad transversal de `RN-AG-02`. Propuesta: decidir y documentar en KB 09/10.

- **Antelación mínima configurable: ¿quién configura?** — admin o profesional. No decidido (KB 10). Transversal a `RN-AG-05`/cancelación/reprogramación.

- **"La seña puede ser no reembolsable"** — ¿en qué estados se retiene? No decidido (KB 10). Transversal a `RN-CJ-03`.

## 4. Conflictos detectados

- **`CHANGES.md` cita `RN-AG-07` (inexistente) vs `05_reglas_de_negocio.md`** — conflicto documental. Prevalece la KB (fuente de reglas) y el change ya lo registra como pregunta abierta. Resolución pendiente: crear la regla o corregir la cita. El mismo patrón aparece con `RN-AG-09` (C-15) y `RN-CJ-04/05` (C-12/C-13a) — deuda documental transversal (`design.md` §Risks).

- **`PreReserva` sin `SoftDeleteMixin` vs R13** — no es conflicto: R13 enumera solo Paciente/Turno/Profesional/Sillon. D1 justifica el ciclo por estados (`vigente`/`consumida`/`expirada`/`cancelada`) y prohíbe DELETE físico por aplicación. Prevalece R13 (no la incluye). Se recomienda documentar la justificación en KB 09 (decisión DD).

- **`TurnoService.eliminar_bloqueo` usa `db.delete(bloqueo)` (borrado físico de `Bloqueo`)** — R13 no incluye `Bloqueo`, por lo que no viola. Pero si el grupo considera `Bloqueo` entidad de negocio, habría conflicto. Propuesta: decidir si `Bloqueo` entra a R13 o queda como está (registrar en KB 09).

- **Atomicidad de la reserva sobre pre-reserva** — `design.md` D2 exige "misma transacción". En `service.py`, `reservar()` llama a `TurnoService.crear()` (que hace `commit` propio) y luego actualiza la retención con un segundo `commit`. Si el segundo falla, queda un turno creado con la retención todavía `vigente` (inconsistencia). No es un conflicto de reglas, pero es una desviación del diseño. Ver revisión crítica.

- **Rate-limit por proceso vs varios workers** — limitación declarada en D8; con N workers el límite efectivo es N×. No viola regla, pero debe documentarse en despliegue.

## 5. Cobertura faltante propuesta

### 5.1 Escenarios (Given/When/Then)

1. **Pre-reserva de hueco ocupado por turno**
   - Given un turno activo en Sillón 1 / Prof. A (10:00–10:30)
   - When se hace `POST /public/pre-reservas` para el mismo rango
   - Then 409 y no se crea la retención (RN-AG-01, R6).

2. **Pre-reserva de hueco bloqueado**
   - Given un bloqueo en Sillón 1 (10:00–10:30)
   - When se retiene ese rango
   - Then 409 (RN-AG-04).

3. **Pre-reserva con inicio pasado**
   - Given un `inicio` <= ahora()
   - When se retiene
   - Then 422 (RN-AG-06/R1, validación).

4. **Pre-reserva con `duracion_min <= 0`**
   - Given `duracion_min = 0`
   - When se retiene
   - Then 422 (R1).

5. **Pre-reserva con campo extra**
   - Given un body con campo no declarado
   - When se retiene
   - Then 422 (R1, RN-SEG-01).

6. **Retención vencida libera el hueco (sin limpieza)**
   - Given una retención con `expira_en` en el pasado
   - When se consulta `GET /public/disponibilidad`
   - Then el slot se devuelve como libre (RN-AG-01, D4).

7. **Confirmación con token vencido**
   - Given una retención vencida
   - When se hace `POST /public/reservar` con su token
   - Then 409 y no se crea el turno (D2).

8. **Confirmación con token de otra franja**
   - Given una retención vigente
   - When se reserva con `inicio`/sillón/profesional distintos
   - Then 409 (D2).

9. **Reutilización de token consumido**
   - Given una retención ya consumida
   - When se reserva de nuevo con el mismo token
   - Then 409 y no se crea un segundo turno (D2).

10. **Reserva sin retención (compatibilidad C-06)**
    - Given un hueco libre
    - When se reserva sin `pre_reserva_token`
    - Then 201 (compatibilidad aditiva).

11. **Reprogramación exitosa**
    - Given un turno `reservado` con ≥12h de anticipación
    - When se reprograma a un hueco libre
    - Then 200 con nuevo `inicio`/`fin` y mismo token (R6).

12. **Reprogramación que choca con otro turno**
    - Given un turno activo en el destino
    - When se reprograma al mismo rango
    - Then 409 y el turno conserva su horario original (RN-AG-01, R6).

13. **Reprogramación dentro de la ventana mínima**
    - Given un turno que comienza en <12h
    - When se reprograma
    - Then 409 (RN-AG-05).

14. **Reprogramación de turno no reprogramable**
    - Given un turno `atendido`/`cancelado`/`ausente`/`presente`
    - When se reprograma
    - Then 409 (RN-AG-05).

15. **Reprogramación con campo extra (`sillon_id`/`profesional_id`/`duracion_min`)**
    - Given un body con alguno de esos campos
    - When se reprograma
    - Then 422 (R1).

16. **Reprogramación con inicio en el pasado**
    - Given un `inicio` <= ahora()
    - When se reprograma
    - Then 422.

17. **Token inexistente al reprogramar**
    - Given un token que no existe
    - When se reprograma
    - Then 404 (R8, RN-SEG-01).

18. **QR del portal**
    - Given `GET /public/qr/reserva.svg`
    - When se solicita
    - Then 200 `image/svg+xml`, SVG no vacío, sin red (R9).

19. **QR de turno existente**
    - Given un token existente
    - When se solicita su QR
    - Then 200 con SVG que codifica `{public_base_url}/p/turno/{token}`.

20. **QR de token inexistente**
    - Given un token que no existe
    - When se solicita su QR
    - Then 404 (R8).

21. **Rate-limit exceso de escrituras**
    - Given una IP que supera el máximo de escrituras en la ventana
    - When hace una escritura más
    - Then 429 con `Retry-After` y `code="rate_limited"` (RN-SEG-01).

22. **Rate-limit no afecta endpoints internos**
    - Given un usuario autenticado con la IP agotada
    - When opera `GET /api/v1/turnos`
    - Then responde normal (R8).

23. **Origen del turno público**
    - Given una reserva desde `/reservar`
    - When se consulta `GET /api/v1/turnos`
    - Then el turno tiene `origen="publico"` (agenda spec).

24. **Origen del turno interno**
    - Given una creación desde la agenda
    - When se consulta
    - Then `origen="interno"` y el cliente no puede fijarlo (`origen` en body → 422).

25. **Pre-reserva no bloquea agenda interna**
    - Given una pre-reserva vigente
    - When recepción crea un turno en ese hueco
    - Then 201 (agenda spec).

26. **Log sin datos sensibles en pre-reserva**
    - Given una pre-reserva creada
    - When se captura `caplog`
    - Then no aparecen DNI/teléfono/nombre (R9).

### 5.2 Casos de test (pytest/vitest)

- `backend/test/test_turno_origen.py`: `TurnoCreate` rechaza `origen` (422); `TurnoOut` incluye `origen`; `crear` default `interno`; `crear(..., origen="publico")`; `crear_sobreturno` default `interno`.
- `backend/test/test_pre_reserva_schemas.py`: `PreReservaCreate` acepta 5 campos; rechaza `duracion_min <= 0`; rechaza campo extra; normaliza `inicio` naive a ART; rechaza `paciente`/`dni`.
- `backend/test/test_pre_reserva_service.py` (integración): retención exitosa con `expira_en = ahora + ttl`; 409 si ocupado por turno/bloqueo/retención; 422 inicio pasado; estado `vigente`; retención vencida libera sin limpieza; dos retenciones seguidas del mismo hueco → 201 y 409; token UUID distinto.
- `backend/test/test_public_pre_reserva_router.py`: 201 sin auth; 409 hueco ocupado; 422 campo extra; 422 inicio pasado; respuesta sin `dni`/`telefono`/`nombre`.
- `backend/test/test_public_router.py` (ampliar): reserva con token vigente → 201 + retención `consumida` + `turno_id` + `origen="publico"`; token vencido → 409 sin turno; token de otra franja → 409; token reutilizado → 409; sin token → 201; 409 de antisolapamiento no consume la retención; disponibilidad refleja el turno; reserva pública aparece en `GET /turnos` con `origen="publico"`; `caplog` sin datos sensibles.
- `backend/test/test_public_reprogramar.py`: exitosa conserva token/sillón/profesional/duración; 409 choque; 409 ventana; 409 estados no reprogramables; 422 inicio pasado; 422 con `sillon_id`/`profesional_id`/`duracion_min`; 404 token inexistente; conflicto contra profesional en otro sillón y contra bloqueo; liberación del horario anterior; reprogramación al mismo horario 200; destino con retención de otro paciente 409.
- `backend/test/test_rate_limit.py` (puro): admite hasta máximo; rechaza el siguiente; `retry_after > 0`; ventana se reinicia con reloj inyectable; buckets independientes; claves distintas no se contaminan.
- `backend/test/test_rate_limit_router.py`: N+1 escrituras → 429 con `Retry-After` y `code="rate_limited"`; lecturas siguen 200; `GET /turnos` con JWT no se limita; 429 no revela si un token existe; desactivable por setting.
- `backend/test/test_qr_service.py` (puro): `url_reserva`, `url_turno`; `svg_qr` devuelve SVG con `<svg`, `viewBox`, al menos un `path`; determinista; sin DNI/nombre.
- `backend/test/test_qr_router.py`: 200 + `image/svg+xml`; token existente 200; token inexistente 404; `Cache-Control: no-store` en QR de turno; sin red (`socket.socket` parcheado).
- `backend/test/test_migration_0006.py`: revision/down_revision; `create_table("pre_reservas")` con token unique y FK a turnos; `add_column("turnos","origen")` con `server_default='interno'` y `nullable=False`; CHECKs; tres índices; downgrade con `drop_column`+`drop_table`; `--sql` contiene CREATE/ALTER/DROP.
- `backend/test/test_models_structure.py` (ampliar): verificar `PreReserva` sin `deleted_at`; `turnos.origen` CHECK; `pre_reservas` constraints/índices.
- `frontend/test/preReserva.test.ts` (ya existe): ampliar con `retencionVencida` boundary.
- `frontend/test/rateLimit.test.ts` (ya existe): OK.
- `frontend/test/publicApi.test.ts` (ya existe): ampliar con `crearPreReserva`/`reprogramarTurnoPublico`/`getDisponibilidad` reutilizable.

### 5.3 Criterios para tasks.md

- Desmarcar las tareas [x] cuyos archivos de test no existen (`test_turno_origen.py`, `test_pre_reserva_schemas.py`, `test_pre_reserva_service.py`, `test_public_pre_reserva_router.py`, `test_public_reprogramar.py`, `test_rate_limit.py`, `test_rate_limit_router.py`, `test_qr_service.py`, `test_qr_router.py`, `test_migration_0006.py`) hasta crearlos, o crearlos.
- Agregar criterio de verificación de atomicidad: `reservar` con pre-reserva debe consumir la retención en la misma transacción que crea el turno; si el UPDATE falla, el turno no debe quedar persistido (o documentar la decisión de dos commits).
- Agregar criterio de verificación de logs: `caplog` durante `POST /public/pre-reservas` sin DNI/teléfono/nombre.
- Agregar criterio de verificación de R8: endpoint público con token inválido responde 404 y no expone existencia del recurso.

## 6. Resumen cuantitativo

- Reglas auditadas: 27 (14 RN + 13 R).
- Aplicables al scope C-10: 17.
- ✅ cubiertas: 14 (82% de las aplicables).
- ⚠️ parciales: 3 (RN-AG-02, R7, R10).
- ❌ sin cobertura: 0.
- ➖ N/A: 10 (RN-CL-01/02, RN-CJ-01/02/03, RN-G-01, R3, R4, R11, R12).

Nota: el 82% se sostiene sobre escenarios de spec delta con outcome esperado. La verificación automatizada real es menor: varios archivos de test marcados [x] en `tasks.md` no existen en el filesystem (ver revisión crítica), por lo que la cobertura ejecutable es inferior a la declarada.

## 7. Revisión crítica

- **Omisión detectada:** `tasks.md` marca como completadas ([x]) las tareas que crean archivos de test nuevos de C-10 (`test_turno_origen.py` 4.1, `test_pre_reserva_schemas.py` 5.1, `test_pre_reserva_service.py` 5.3, `test_public_pre_reserva_router.py` 6.1, `test_public_reprogramar.py` 7.1, `test_rate_limit.py` 8.1, `test_rate_limit_router.py` 8.4, `test_qr_service.py` 9.2, `test_qr_router.py` 9.4, `test_migration_0006.py` 3.1), pero esos archivos **no existen** en `backend/test/` (verificado con `Get-ChildItem`). Los tests existentes (`test_public_router.py`, `test_public_service.py`, `test_public_slots.py`, `test_public_schemas.py`, `test_agenda_schemas.py`, `test_agenda_service.py`) no cubren los nuevos comportamientos (pre-reserva, reprogramación pública, QR, rate-limit, origen, retención). Por lo tanto, la implementación de C-10 no está verificada por la suite aunque `tasks.md` lo declara.

- **Cómo se detectó:** listado del directorio `backend/test/` y búsqueda de `origen`/`pre_reserva`/`rate_limit`/`qr` en los tests (sin resultados para los nuevos). Comparación contra `tasks.md` §3–§9.

- **Fuente que permitió corregir:** `tasks.md` (tareas 3.1, 4.1, 5.1, 5.3, 6.1, 7.1, 8.1, 8.4, 9.2, 9.4) + `AGENTS.md` R6/R5 (test de conflicto obligatorio, migración con test) + skill (no marcar ✅ sin evidencia).

- **Antes:** `tasks.md` con `- [x] 4.1 **RED**: crear backend/test/test_turno_origen.py ... Verificación: el archivo falla.` (y análogos), dando por verificado un archivo inexistente.

- **Después:** o bien crear los archivos listados en §5.2 (TDD) y mantener [x], o bien desmarcarlos a [ ] hasta que existan. Hasta entonces, la cobertura real de C-10 es la de C-06/C-09a reusada, no la nueva.

**Hallazgo adicional (no bloqueante, a corregir):** la reserva sobre pre-reserva no es atómica respecto al consumo de la retención (`TurnoService.crear` commitea antes del `UPDATE` de la retención). Fuente: `design.md` D2 ("misma transacción"). Propuesta: envolver ambos pasos en una sola transacción o documentar la decisión de dos commits con compensación.

**¿Debería actualizarse la matriz del repo (`docs/auditorias/matriz-reglas-tests.md`)?** Sí, antes de archivar C-10. Actualmente no refleja ninguna evidencia de C-10 (pre-reserva, reprogramación pública, QR, rate-limit, origen). Se recomienda agregar filas/columnas con las evidencias de §2 y §5.2, y actualizar el estado de RN-AG-01/RN-AG-05/R1/R6/R8/R9 con las nuevas referencias (tests cuando existan). No se modificó la matriz en esta auditoría (read-only).