# Tasks — C-09b agenda-vista-semanal

> **TDD estricto.** Backend desde `backend/` con PostgreSQL migrado y sembrado para integración. Frontend con `node:test` puro (no hay harness de componentes React): la lógica de semana, agrupación y filtro se prueba primero; el render se valida con `tsc`, `eslint`, `build` y Playwright.
> Cada grupo escribe sus propios tests antes de implementar. No commitear ni pushear (R11).
>
> **Criterio visual aprobado:** `mockups/` (revisión 1 del design system) es criterio de aceptación. Durante la verificación, comparar cada pantalla implementada contra `mockups/previews/` a 390x844 y 1440x900, reportar diferencias por prioridad y registrar el resultado en `design.md` (`Visual verify`).

## 1. Safety net

- [x] 1.1 Correr la línea base del backend y registrar los conteos: `cd backend; python -m pytest -m "not integration" -q; python -m pytest -q`. Verificación: ambos comandos terminan en 0 y los conteos quedan anotados en este archivo.
- [x] 1.2 Correr la línea base del frontend: `cd frontend; npm test; npm run lint; npx tsc --noEmit`. Verificación: los tres comandos terminan en 0.
- [x] 1.3 Releer `backend/src/app/modules/agenda/{router,service,schemas,models}.py`, `backend/src/app/core/timezone.py`, `frontend/src/features/agenda/AgendaPage.tsx`, `useAgendaStore.ts`, `frontend/src/shared/api/agenda.ts` y `frontend/src/app/router.tsx`. Verificación: nota breve en este archivo confirmando que `detectar_conflicto` y el RBAC no se tocan.

## 2. Filtro de consulta (schema)

- [x] 2.1 **RED**: crear `backend/test/test_agenda_rango_schema.py` con: semana válida (`desde`/`hasta`), solo `desde` → error, solo `hasta` → error, `desde > hasta` → error, 32 días → error, `fecha` + rango → error, campo extra → error con `extra="forbid"`, 31 días → válido. Verificación: `python -m pytest test/test_agenda_rango_schema.py -q` falla por ausencia de `FiltroTurnos`.
- [x] 2.2 **GREEN**: implementar `FiltroTurnos` en `backend/src/app/modules/agenda/schemas.py` con `ConfigDict(extra="forbid")`, tipos `date | None`, `UUID | None` y validadores de rango. Verificación: el test de 2.1 pasa.
- [x] 2.3 **TRIANGULATE**: ampliar `test_agenda_rango_schema.py` con rango de un solo día, rango que cruza año bisiesto (`2028-02-28` a `2028-03-01`), `fecha` sola válida y todos los filtros en `None`. Verificación: el archivo completo pasa.
- [x] 2.4 **REFACTOR**: extraer `_validar_rango` con type hints y docstring; `ruff check src/app/modules/agenda/schemas.py`. Verificación: `ruff` sin hallazgos y los tests de 2.1–2.3 siguen en verde.

## 3. Servicio por rango

- [x] 3.1 **RED**: crear `backend/test/test_agenda_rango_service.py` contra Postgres con: lunes 00:00 ART incluido, domingo 23:30 ART incluido, domingo anterior 23:30 excluido, turno con `deleted_at` excluido, turno `cancelado` incluido, filtro combinado por profesional y por sillón, y orden estable con dos turnos del mismo `inicio`. Verificación: el archivo falla porque `listar` ignora `desde`/`hasta`.
- [x] 3.2 **GREEN**: extender `TurnoService.listar` con `desde`/`hasta` usando `inicio_dia`/`fin_dia` y ordenar por `inicio, sillon_id, id`. Verificación: el test de 3.1 pasa.
- [x] 3.3 **TRIANGULATE**: agregar rango de un día, rango de 31 días, semana sin turnos → `[]`, filtro solo por profesional, filtro solo por sillón y turno sobreturno incluido. Verificación: el archivo completo pasa.
- [x] 3.4 **REFACTOR**: extraer un helper privado para aplicar el rango, mantener type hints y `snake_case`; `ruff check src/app/modules/agenda/service.py`. Verificación: `ruff` limpio y tests de 3.1–3.3 en verde.
- [x] 3.5 **REGRESIÓN RN-AG-01**: correr `pytest test/test_agenda_service.py test/test_agenda_conflicts.py test/test_agenda_schemas.py -q`. Verificación: todo pasa y `detectar_conflicto` no tiene cambios en `git diff`.

## 4. Router

- [x] 4.1 **RED**: crear `backend/test/test_agenda_rango_router.py` con: `GET /turnos?desde&hasta` 200 y cuerpo ordenado, cada variante inválida → 422 con `{error:{code,message}}`, sin token → 401, rol `odontologo` → 200, `fecha` sigue devolviendo el día, y query param desconocido sigue respondiendo 200 (compatibilidad). Verificación: el archivo falla contra el handler actual.
- [x] 4.2 **GREEN**: usar `FiltroTurnos` como dependencia de `listar_turnos` en `router.py` y pasar el rango al servicio. Verificación: el test de 4.1 pasa.
- [x] 4.3 **TRIANGULATE**: agregar rango + `profesional_id`, rango + `sillon_id`, semana vacía `[]` y verificación de que `TurnoOut` conserva todos sus campos. Verificación: el archivo completo pasa.
- [x] 4.4 **REFACTOR**: mantener el handler delgado y documentar los parámetros en el docstring/OpenAPI; `ruff check src/app/modules/agenda/router.py`. Verificación: `ruff` limpio y tests de 4.1–4.3 en verde.
- [x] 4.5 **R9**: agregar a `test_agenda_rango_router.py` un caso que capture logs durante `GET /turnos?desde&hasta` y verifique que la query string solo contiene fechas/filtros y que ningún log de `app` incluye `prestacion` ni `notas`. Verificación: el test pasa y no aparece dato clínico en `caplog`.

## 5. Migración 0005 (índice de rango)

- [x] 5.1 **RED**: crear `backend/test/test_migration_0005.py` que exija `revision="0005_agenda_indice_inicio"`, `down_revision="0004_agenda_avanzada"`, `create_index("ix_turnos_inicio", "turnos", ["inicio"])`, `drop_index` en downgrade y el `Index("ix_turnos_inicio", "inicio")` en `models.py`. Verificación: el test falla.
- [x] 5.2 **GREEN**: agregar el índice al modelo `Turno` y crear `backend/src/app/db/migrations/versions/0005_agenda_indice_inicio.py`. Verificación: el test de 5.1 pasa.
- [x] 5.3 **TRIANGULATE**: verificar `alembic upgrade head --sql` contiene el `CREATE INDEX` y `alembic downgrade 0004_agenda_avanzada --sql` contiene el `DROP INDEX`; correr `test_migrations.py`. Verificación: ambos SQL contienen el índice y el test pasa.
- [x] 5.4 **REFACTOR/APLICAR**: comentar el propósito del índice y ejecutar `alembic upgrade head` contra PostgreSQL; consultar `pg_indexes` para confirmar `ix_turnos_inicio`. Verificación: la consulta devuelve el índice y `alembic current` marca `0005`.

## 6. Frontend: cliente API y lógica pura de semana

- [x] 6.1 **RED**: crear `frontend/test/apiAgendaRango.test.ts` para una función pura exportada `construirQueryTurnos` con: rango completo, `fecha` sola, sin filtros, rango + profesional y codificación de parámetros. Agregar el archivo al script `test` de `frontend/package.json`. Verificación: `npm test` falla porque la función no existe.
- [x] 6.2 **GREEN**: exportar `construirQueryTurnos` desde `frontend/src/shared/api/agenda.ts` y extender el tipo de filtros con `desde`/`hasta`; `listarTurnos` la usa. Verificación: el test de 6.1 pasa.
- [x] 6.3 **RED**: crear `frontend/test/agendaSemana.test.ts` para `inicioSemana`, `diasSemana`, `rangoSemana`, `agruparSemana`, `filtrarPorProfesional` y `construirCeldas` con: lunes como inicio, domingo como entrada, semana que cruza año, 7 días consecutivos, 7 × 3 celdas, solo sillones activos, orden por hora, celdas vacías, flag de sobreturno y filtro sin coincidencias. Verificación: `npm test` falla por módulo inexistente.
- [x] 6.4 **GREEN**: implementar `frontend/src/features/agenda/semanaUtils.ts` con funciones puras y tipos exportados. Verificación: el test de 6.3 pasa.
- [x] 6.5 **TRIANGULATE**: agregar timestamp `2027-01-04T02:00:00Z` (domingo 23:00 ART) que debe caer en la semana anterior, turno domingo 23:30 ART en la semana correcta, arreglo vacío y dos turnos con el mismo `inicio` en orden estable. Verificación: el archivo completo pasa.
- [x] 6.6 **REFACTOR**: sin `any`, funciones puras y nombres en `camelCase` para utilidades, componentes en `PascalCase`; `npm run lint` y `npx tsc --noEmit`. Verificación: ambos comandos en 0.

## 7. Frontend: vista semanal

- [x] 7.1 **GREEN**: agregar `cargarSemana(desde, hasta)` a `useAgendaStore` con una sola llamada a `listarTurnos` y catálogos en paralelo reutilizando `cargarCatalogos`; no cargar por día. Verificación: Playwright muestra exactamente una request a `/api/v1/turnos?desde=...&hasta=...` al abrir la semana.
- [x] 7.2 Crear `SemanaPage.tsx`, `SemanaGrid.tsx`, `TurnoChip.tsx`, `SelectorSemana.tsx`, `FiltroProfesional.tsx` y `VistaToggle.tsx` en `frontend/src/features/agenda/`; registrar `/app/agenda/semana` en `frontend/src/app/router.tsx`. Verificación: `npx tsc --noEmit` y `npm run lint` en 0; la ruta renderiza con sesión válida.
- [x] 7.3 Reutilizar `EstadoTurnoMenu` y `ReprogramarModal` desde `TurnoChip`: estado local `turnoSeleccionado`/`reprogramando` y callbacks a `cambiarEstado`/`reprogramar`; sin handler en celdas vacías. Verificación: Playwright confirma cambio de estado y reprogramación, y que clickear una celda vacía no abre modal ni envía request.
- [x] 7.4 Agregar `VistaToggle` al encabezado de `AgendaPage` sin alterar la carga diaria (sigue abriendo “hoy”); marcar la opción activa con `aria-current`. Verificación: `/app/agenda` sigue funcionando y el toggle navega a `/app/agenda/semana` y de vuelta.
- [x] 7.5 Aplicar `estadoClasses` a los seis estados, etiqueta textual por estado, badge “Sobreturno” y borde punteado cuando `es_sobreturno`, cancelados atenuados y leyenda compacta. Verificación: Playwright con un turno de cada estado y un sobreturno muestra estilos y etiquetas distintas.
- [x] 7.6 Implementar estados de carga, error con reintento y semana vacía en `SemanaPage`; al navegar de semana reemplazar el arreglo completo. Verificación: Playwright con backend caído muestra error y el botón “Reintentar” recupera la grilla.
- [x] 7.7 **TRIANGULATE UI**: navegar semana anterior/siguiente/actual, filtrar por profesional y volver a “Todos”, reprogramar dentro de la semana, reprogramar hacia otra semana (el turno desaparece y se informa el destino) y reprogramar con respuesta 409 (el turno conserva su celda original). Verificación: checklist de Playwright firmado en el resumen del apply.
- [x] 7.8 **ACCESIBILIDAD Y R10**: labels en español rioplatense para el selector de profesional y los botones de semana, montos (si aparecen) en ARS, foco visible, navegación por teclado del menú de estado y contraste de los chips. Verificación: recorrido con Tab/Enter en Playwright y revisión visual de contraste y textos.

## 8. Integración y verificación

- [x] 8.1 `cd backend; alembic upgrade head; python -m app.db.seed; python -m pytest -q` dos veces. Verificación: ambas corridas en verde y sin datos residuales entre tests.
- [x] 8.2 `cd backend; ruff check src test`. Verificación: sin hallazgos.
- [x] 8.3 `cd frontend; npm test; npm run lint; npx tsc --noEmit; npm run build`. Verificación: los cuatro comandos en 0.
- [x] 8.4 Playwright: abrir `/app/agenda` y `/app/agenda/semana` en 390×844 y 1440×900, revisar consola y requests fallidas, guardar capturas. Verificación: sin errores de consola, sin requests 4xx/5xx inesperadas y capturas adjuntas al resumen.
- [x] 8.5 `openspec validate "c-09b-agenda-vista-semanal" --strict` y `openspec validate --all`. Verificación: ambos comandos en 0.
- [x] 8.6 Pasar `business-rule-coverage-auditor` sobre este change y corregir los gaps encontrados. Verificación: matriz de cobertura con RN-AG-01, RN-AG-05, R1, R7, R8 y R9 en ✅ o con propuesta aplicada.

## Workflow follow-up

- Gate visual resuelto: política `system-and-mockups` registrada en `.active-orchestrator-state.json`, design system revisión 1 aprobado y mockups de C-09b aprobados (2026-11-04, by user).
- Registrar el gap de US-001 sobre bloqueos/feriados visibles en la agenda para priorizarlo en un change futuro.
- Revisión humana del design (layout 7 × 3, filtro en cliente, límite de 31 días).
- Archivar con `openspec archive "c-09b-agenda-vista-semanal" -y` y marcar `C-09b` como `[x]` en `CHANGES.md`.
- Continuar con C-10 (reserva pública avanzada).

---

## Registro de apply — backend grupos 1–5 (2026-11-04)

- **1.1 Línea base** (pre-cambio, `DATABASE_URL=postgresql+psycopg://postgres@127.0.0.1:5433/odonto_test`):
  `pytest -m "not integration" -q` → **180 passed, 7 skipped, 104 deselected**; `pytest -q` →
  **284 passed, 7 skipped**. Ambos comandos terminaron en 0.
- **1.2 Línea base frontend**: `npm test` → 4 pass / 0 fail; `npm run lint` → 0; `npx tsc --noEmit` → 0.
- **1.3** `detectar_conflicto`, `solapamiento`, `require_role` (RBAC) y los endpoints de escritura
  (`crear`, `crear_sobreturno`, `reprogramar`, `cambiar_estado`) NO se modificaron: `git diff -U0`
  sobre `service.py` no tiene hunks en el rango de `detectar_conflicto` (solo imports, `listar` y
  `_aplicar_rango`). El working tree ya traía los cambios sin commitear de C-09a (R11).
- **Cierre de la fase** (post-cambio): `pytest -q` → **332 passed, 7 skipped** en dos corridas
  consecutivas; `pytest -m "not integration" -q` → **200 passed, 7 skipped, 132 deselected**;
  `ruff check src test` → 0 hallazgos. `alembic upgrade head` → `0005_agenda_indice_inicio`;
  `alembic downgrade 0004_agenda_avanzada` y el re-`upgrade head` terminaron en 0.
- **D2 resuelto**: `FiltroTurnos` (`extra="forbid"`, R1) se valida dentro de la dependencia
  `filtro_turnos` de `router.py`; los parámetros `Query` siguen declarados explícitamente en esa
  dependencia, así los query params desconocidos se siguen ignorando (compatibilidad) mientras el
  `forbid` del modelo se ejerce en el modelo y en sus tests de schema.
- **Deuda detectada (no de esta fase)**: los fixtures de integración hacen soft delete de los turnos
  de su ventana; la base `odonto_test` ya estaba con 0 turnos activos al iniciar la fase y
  `app.db.seed` no recrea turnos. Las ventanas nuevas de C-09b usan 2028 para no ampliar el daño.
---

## Registro de apply — frontend, verificación y auditoría (2026-11-04)

- **Comandos finales**: `npm test` → **32 tests, 32 pass / 0 fail**; `npm run lint` → 0;
  `npx tsc --noEmit` → 0; `npm run build` → 0. Backend: `pytest -q` → **339 passed, 7 skipped**
  (dos corridas); `ruff check src test` → 0.
- **6.1–6.2**: `construirQueryTurnos`/`rutaTurnos` viven en `shared/api/turnosQuery.ts` (módulo puro
  sin red) y `agenda.ts` los reexporta y usa; `listarTurnos` quedó en una línea.
  Motivo del módulo aparte: `node:test` no puede cargar `client.ts` (React + zustand + imports sin
  extensión), así que el test puro importa el módulo sin dependencias.
- **6.3–6.5**: `semanaUtils.ts` (`inicioSemana`, `diasSemana`, `rangoSemana`, `formatearRangoSemana`,
  `agruparSemana`, `filaSemana`, `construirCeldas`, `turnosDeSemana`, `filtrarPorProfesional`),
  todo cálculo de calendario en UTC sobre el día ISO para no depender de la zona del navegador.
- **7.1**: `cargarSemana` hace una sola request; el efecto de `SemanaPage` deduplica por rango para
  que el doble render de `StrictMode` no duplique la consulta (verificado: 1 sola request).
- **7.6**: se agregó `errorCarga` al store para que un error de acción (409) no reemplace la grilla;
  solo el fallo de carga muestra el banner con `Reintentar`.
- **Defecto corregido (fuera del alcance original, con test)**: no existían `GET /api/v1/sillones`
  ni `GET /api/v1/profesionales`, así que `cargarCatalogos()` caía siempre al fallback con IDs
  ficticios y **ninguna** grilla podía asociar un turno a su sillón (la diaria tampoco). Se agregaron
  ambos endpoints de lectura (RBAC de lectura, `extra="forbid"`, `deleted_at IS NULL`, `activo`) con
  `backend/test/test_catalogo_router.py` (7 tests). Sin ellos la vista semanal no era verificable.
- **Corregido de paso**: `test_resumen_vacio` (caja) era flaky por colisión aleatoria de fechas;
  ahora elige un día sin movimientos (`_fecha_sin_movimientos`).
- **8.4 Verificación visual**: `differences` (menores). Capturas en `mockups/verify/`:
  `diaria-390x844.png`, `diaria-1440x900.png`, `semana-390x844.png`, `semana-1440x900.png`,
  `semana-completa-390x844.png`, `semana-completa-1440x900.png`, `semana-vacia-1440x900.png`,
  `semana-error-1440x900.png`, `semana-reintento-1440x900.png`,
  `semana-filtro-sin-turnos-1440x900.png`, `reprogramar-409-1440x900.png`,
  `reprogramar-fuera-semana-1440x900.png`.
- **8.6 Auditoría**: ver informe en el resumen del apply; gap de RN-AG-05 (máquina de estados) queda
  como propuesta abierta, no se modifica comportamiento de C-09a en este change.
- **Estabilidad de la suite (residuo de datos)**: la corrida de cierre falló con 42 errores porque
  `_seed_ids` de los tests de agenda/caja elegía profesionales y sillones sin filtrar `activo` y
  acumulaba `Profesional(activo=False)` de corridas previas (alfabéticamente primero). Se filtró
  `activo` en `test_agenda_{service,router}.py`, `test_agenda_rango_{service,router}.py`,
  `test_caja_{router,service}.py` y se agregó limpieza (soft delete) a los tests que crean entidades
  temporales (`test_crear_rechaza_profesional_inactivo`, catálogos). Suite estable: 339/7 dos veces.
- **Reparación post-verify (2026-11-04)**: (1) cabecera de `/app/agenda` reordenada en dos filas por
  debajo de `sm` (el toggle ya no se superpone a “Nuevo turno”/“Cerrar sesión”); botones de fecha y
  de acción con `min-h-11`. (2) `mockups/verify/semana-390x844.png` re-capturada sobre
  `/app/agenda/semana` (antes mostraba por error la vista diaria). (3) grilla semanal con
  `table-fixed` y columnas iguales (155 px a 1440); navegación de semana compacta en una fila a 390
  (44 px de alto) y en dos filas a 320 sin recortes. (4) `formatHora` unificado a 24 h con test
  (`test/date.test.ts`): diaria, semanal, caja y páginas públicas comparten formato; se eliminó
  `formatHoraCorta`. Medición final: `scrollWidth === clientWidth` en `/app/agenda` y
  `/app/agenda/semana` a 320/390/1440, sin solapamientos de la cabecera.
- **Datos de demo**: la verificación creó 28 turnos por API: 18 en la semana del 9–15/11, 2 en la
  del 16–22/11 y 8 en la del 2–8/11 (6 de jue-sáb + 2 de hoy). Quedan en `odonto_test` como
  datos de demostración; no se borraron.
