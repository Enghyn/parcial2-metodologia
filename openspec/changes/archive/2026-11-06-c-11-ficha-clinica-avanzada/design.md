# Design — C-11 ficha-clinica-avanzada

## Context

Ver `proposal.md` — Why. C-07 dejó `Paciente`, `Odontograma` y `HallazgoPieza` con un upsert por pieza que pisa el estado anterior; `HallazgoPieza` ya tiene `fecha` pero no autor. `clinical-records` y `core-data-model` ya están archivadas con 7 y 11 requisitos. La última migración real es `0005_agenda_indice_inicio`; `CHANGES.md` decía `0006` para C-11, pero C-10 tomaría ese número si se implementa antes, por eso este design usa `0007` como número tentativo y lo confirma al implementar.

La KB no define entidad de evolución clínica, consentimiento informado ni historial de pieza; solo `RN-CL-01` (FDI + 6 estados), `RN-CL-02` (permisos clínicos) y la mención de "evolución clínica" en `knowledge-base/03` y `07`. El alcance funcional de C-11 viene de `CHANGES.md`. Las decisiones que la KB no cubre quedan marcadas como preguntas abiertas y no se presentan como reglas de negocio existentes.

## Goals / Non-Goals

**Goals:**

- Agregar evolución clínica y consentimiento informado sin romper el contrato de C-07.
- Preservar cada cambio de pieza con autor y fecha, en una estructura append-only.
- Mantener el RBAC y la privacidad ya definidos, extendidos a las nuevas superficies.
- Dejar una migración reversible y testeable.

**Non-Goals:**

- Firma digital, adjuntos, imágenes clínicas o plantillas de consentimiento.
- Revocación de consentimiento, vencimiento o renovación automática.
- Edición o borrado de evoluciones, consentimientos o versiones del historial.
- Cambiar los 6 estados clínicos o la nomenclatura FDI.
- Notificaciones, presupuestos, OS o caja (changes posteriores).

## Decisions

### D1 — Snapshot actual + historial append-only, no reescribir el modelo de C-07

`hallazgos_pieza` sigue siendo la foto actual con `UNIQUE(odontograma_id, pieza)` y el `PUT` sigue siendo upsert. Cada upsert, en la misma transacción, inserta una fila en `hallazgos_pieza_historial` con el estado/observación anteriores y los nuevos.

- **Por qué**: conserva el contrato y los tests de C-07, mantiene la lectura del odontograma en una sola tabla y evita duplicar la lógica de "última versión".
- **Alternativa descartada**: hacer `hallazgos_pieza` append-only y derivar el estado actual con `DISTINCT ON (pieza)`. Obligaría a eliminar el `UNIQUE` de la spec de `core-data-model`, cambiar el `PUT` y reescribir C-07.
- **Consecuencia**: el historial es la fuente de verdad de la evolución; `hallazgos_pieza` es la proyección actual. Nunca se pierde una versión.

### D2 — Autor siempre desde el JWT; nulo solo para filas heredadas

`hallazgos_pieza.autor_usuario_id` es FK nullable a `usuarios`. El servicio lo completa con `current_user.id` en cada alta o actualización; el schema de entrada no declara el campo. Las filas de C-07 quedan con autor nulo hasta su próxima actualización.

- **Por qué**: R8/R9 — el cliente no puede atribuir un hallazgo a otro usuario. La columna nullable evita inventar un autor retroactivo.
- **Alternativa descartada**: backfill con un usuario "sistema" o con el odontólogo del seed. Falsifica la historia clínica.
- **Alternativa descartada**: `NOT NULL` con backfill. Rompe la migración sobre datos existentes.

### D3 — Evolución clínica append-only

Tabla `evoluciones_clinicas`: `id`, `paciente_id` (FK), `autor_usuario_id` (FK), `fecha` (timestamptz, default `now()`), `texto` (Text, `CHECK btrim(texto) <> ''`). Sin `deleted_at`. Trigger `BEFORE UPDATE OR DELETE` y `BEFORE TRUNCATE` que rechaza la operación.

- **Por qué**: R13 exige no borrar historia; en un registro clínico la corrección es otra entrada, igual que RN-CJ-02 en caja. El trigger cubre SQL directo.
- **Alternativa descartada**: `deleted_at` + edición. Permitiría reescribir la historia clínica y rompería la trazabilidad.
- **Consecuencia**: no hay endpoint `PUT`/`DELETE`; la API responde 405 por ausencia de ruta.

### D4 — Consentimiento versionado, una fila por versión

Tabla `consentimientos_informados`: `id`, `paciente_id` (FK), `version` (String(20), `CHECK btrim(version) <> ''`), `fecha` (timestamptz, default `now()`), `autor_usuario_id` (FK). `UNIQUE(paciente_id, version)`. Triggers de inmutabilidad equivalentes a D3.

- **Por qué**: `CHANGES.md` pide versión, fecha y autor. La versión identifica el texto firmado y el `UNIQUE` evita duplicados accidentales.
- **Alternativa descartada**: catálogo `VersionConsentimiento` con texto y vigencia. Excede el alcance y no hay fuente en la KB.
- **Alternativa descartada**: consentimiento único por paciente con `updated_at`. Perdería el historial de versiones.
- **Consecuencia**: el texto del consentimiento no se guarda; solo su versión. Queda como pregunta abierta si debe almacenarse o referenciarse.

### D5 — Migración `0007_ficha_clinica_avanzada`

`down_revision = "0005_agenda_indice_inicio"` (o `0006` si C-10 ya está aplicado). Crea las tres tablas, agrega `hallazgos_pieza.autor_usuario_id`, crea índices y una función `fn_forbid_clinical_history_mutation()` reutilizada por los triggers de las tres tablas.

- **Por qué**: una sola migración atómica y reversible; el número se confirma contra `alembic heads` antes de escribirla.
- **Índices**: `hallazgos_pieza_historial(hallazgo_id, registrado_at DESC)`, `evoluciones_clinicas(paciente_id, fecha DESC)`, `consentimientos_informados(paciente_id, fecha DESC)`.
- **Downgrade**: dropea triggers, función, índices, columna y tablas en orden inverso.

### D6 — RBAC explícito por endpoint

| Endpoint | admin | recepcion | odontologo |
|---|---|---|---|
| `GET /pacientes/{id}/evoluciones` | 200 | 200 | 200 |
| `POST /pacientes/{id}/evoluciones` | 403 | 403 | 201 |
| `GET /pacientes/{id}/consentimientos` | 200 | 200 | 200 |
| `POST /pacientes/{id}/consentimientos` | 403 | 403 | 201 |
| `GET /pacientes/{id}/odontograma/piezas/{pieza}/historial` | 200 | 200 | 200 |
| `PUT /pacientes/{id}/odontograma/piezas/{pieza}` | 403 | 403 | 200 |

- **Por qué**: RN-CL-02 limita la edición de la ficha al odontólogo y da lectura informativa a recepción; `admin` supervisa. R8 exige que la decisión viva en el backend.
- **Implementación**: `Depends(require_role(...))` existente; el endpoint de escritura recibe el `Usuario` para tomar el autor.

### D7 — Privacidad y R9

- El texto de evolución, la versión de consentimiento y los estados/observaciones nunca se pasan por query string ni se escriben en logs. Solo se loguean IDs operativos si hace falta.
- Los schemas de salida no exponen datos de otros pacientes ni credenciales.
- Los errores usan la forma única `{error: {code, message}}` y no incluyen texto clínico.
- El frontend no pone diagnóstico ni texto en la URL; la navegación usa `pacienteId` y `pieza`.

### D8 — Frontend dentro de la ficha existente

Se reutiliza `/app/odontograma/:pacienteId` y se agregan tres secciones debajo del odontograma: Evolución, Consentimiento e Historial por pieza. No se crea una ruta nueva.

- **Por qué**: el odontólogo ya entra a esa ficha; una ruta nueva duplicaría la carga del paciente y el header.
- **UI**: tabs o acordeones con los tokens de `design-system/tokens.css` revisión 1; el odontograma conserva sus colores de estado actuales. El formulario de alta solo se muestra a `odontologo`; `admin` y `recepcion` ven listas en modo lectura.
- **Historial**: al seleccionar una pieza se muestra una línea de tiempo con `estado_anterior → estado_nuevo`, observación, autor y fecha.
- **Sin `any`**, componentes `PascalCase`, `tsc`/`eslint`/`build` en verde (R7).

### D9 — Tests TDD

- Schemas: `extra="forbid"`, texto/versión no vacíos, autor no declarable, `HallazgoOut` con autor.
- Servicio: evolución con autor del JWT, consentimiento duplicado 409, upsert escribe historial, historial ordenado, paciente borrado 404.
- Router: matriz RBAC (401/403/201/200), 405 en métodos no soportados, 422 en pieza inválida.
- Migración: upgrade/downgrade y triggers con SQL directo; sin `tenant_id`.
- Integración con PostgreSQL migrado y sembrado; suite completa dos veces.

## Risks / Trade-offs

- [Historial crece sin límite] → es el costo de la trazabilidad clínica; se indexa por hallazgo y fecha y se pagina la lectura si hiciera falta.
- [Doble escritura snapshot + historial] → ambas ocurren en la misma transacción; un test verifica atomicidad y que un fallo no deje historial sin snapshot.
- [Autor nulo en filas heredadas] → se documenta y se completa en la próxima actualización; no se inventa autor.
- [Consentimiento sin texto ni revocación] → el alcance académico solo pide versión/fecha/autor; se registra como pregunta abierta.
- [Número de migración] → `0007` es tentativo; se confirma con `alembic heads` antes de implementar.
- [Datos clínicos en logs] → tests con `caplog` y revisión de que los `logger` no reciban payloads clínicos.
- [Mockups no aprobados bloquean apply] → la política `system-and-mockups` exige aprobación explícita antes de implementar.

## Migration Plan

1. Confirmar `alembic heads`; ajustar `down_revision` si C-10 ya tomó `0006`.
2. `alembic upgrade head` en local; verificar tablas, columna, índices y triggers.
3. Ejecutar `alembic downgrade -1` y volver a `upgrade head` para probar reversibilidad.
4. Correr la suite de integración con PostgreSQL migrado y sembrado.
5. Rollback de producción: `alembic downgrade` a la revisión anterior; no hay datos que migrar hacia atrás porque las tablas nuevas son de solo alta.

## Open Questions

- `CHANGES.md` cita "KB 06 (US-020)", pero `knowledge-base/06_funcionalidades.md` solo llega a US-011 y no existe US-020. ¿Se debe crear esa historia de usuario en la KB o corregir la referencia? No cambia el alcance de este change.
- La KB no define el texto ni la vigencia del consentimiento informado. ¿Se guarda el texto firmado, se referencia un documento externo o alcanza con la versión? Afecta solo el contenido, no el contrato actual.
- ¿Se permite volver a firmar la misma versión tras una revocación? Hoy `UNIQUE(paciente_id, version)` lo impide; si se necesita, la revocación sería otra versión.
- ¿La `fecha` de la evolución es la del registro (servidor) o puede ser una fecha clínica retroactiva cargada por el odontólogo? Hoy se usa la del servidor y el cliente no la declara; si se necesita retroactividad, se agrega `fecha_clinica` sin cambiar el autor.
- ¿La evolución clínica debe vincularse opcionalmente a un `Turno`? `CHANGES.md` no lo pide; se deja fuera para no inventar la relación.
- ¿La recepción puede leer el texto completo de la evolución o solo metadatos? RN-CL-02 dice "lectura informativa"; se interpreta como lectura completa de la ficha, sujeta a revisión humana.

## UI Mockups

- Design system revision: 1
- Decision: yes (project policy)
- Mockups: openspec/changes/c-11-ficha-clinica-avanzada/mockups/
- Approval: approved (2026-11-05, by user)
- Preview: rendered (2026-11-05, mockups/previews/*-390x844.png y *-1440x900.png)
- Visual verify: pending

### Pantallas y estados que requieren mockup

1. **Ficha clínica del paciente — shell**
   - Desktop 1440×900 y mobile 390×844.
   - Header con nombre/DNI del paciente, tabs o acordeones: Odontograma, Evolución, Consentimiento, Historial por pieza.
   - Estado con datos y estado vacío inicial (paciente sin evoluciones ni consentimientos).
   - Estado de carga y error de carga de la ficha.

2. **Evolución clínica**
   - Lista cronológica con fecha, autor y texto.
   - Formulario de alta visible solo para `odontologo` (textarea, contador de caracteres, botón guardar).
   - Estados: vacío ("Sin evoluciones registradas"), guardando, éxito, error de red, error 403, modo lectura para `admin`/`recepcion`.
   - Desktop y mobile.

3. **Consentimiento informado**
   - Lista de versiones con versión, fecha y autor.
   - Formulario de alta solo para `odontologo` (versión, fecha automática, autor automático mostrado como texto no editable).
   - Estados: vacío ("Sin consentimiento registrado"), versión duplicada (409), guardando, éxito, modo lectura.
   - Desktop y mobile.

4. **Historial por pieza**
   - Selector de pieza o pieza seleccionada desde el odontograma.
   - Línea de tiempo: `estado_anterior → estado_nuevo`, observación, autor y fecha.
   - Estados: pieza sin cambios ("La pieza no tiene cambios registrados"), carga, error, pieza inválida, modo lectura.
   - Desktop y mobile.

5. **Panel de hallazgo actualizado**
   - Panel de la pieza seleccionada con estado, observación, autor y fecha del último cambio.
   - Estado editable (odontólogo) y estado de solo lectura (admin/recepción).
   - Desktop y mobile.

6. **Estados transversales**
   - Banners de error 401/403/404/409/422 con la forma única de error.
   - Confirmación de guardado (toast o inline).
   - Foco visible, contraste y `prefers-reduced-motion` según `tokens.css`.

Los mockups se crearán en la fase siguiente como HTML/CSS local en `mockups/`, importando `design-system/tokens.css` y `brand.js`, con capturas en `mockups/previews/` a 390×844 y 1440×900.
