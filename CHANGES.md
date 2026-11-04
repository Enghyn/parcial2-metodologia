# CHANGES — Secuencia de Implementación

> Índice canónico de los changes del **Sistema Odontológico Multi-Sillón (AR)** para el parcial académico de **Metodología de Desarrollo de Sistemas**.
> Cada change es atómico, auto-contenido y se implementa con TDD.
> **MVP base**: C-01 a C-08 (archivados). **Expansión**: C-09a a C-21.
> Los changes de hardening/calidad (C-02b, C-04b, C-06b, chore-quality, traceability) ya están archivados y no suman al conteo funcional.

---

## Cómo usar este documento

1. Identificar el change y verificar que sus dependencias estén `[x]`.
2. Leer los documentos de `knowledge-base/` indicados en "Leer antes".
3. Ejecutar `/opsx:propose <nombre-del-change>`.
4. Implementar respetando [`AGENTS.md`](AGENTS.md).
5. Archivar con `/opsx:archive <nombre-del-change>` y marcar `[x]`.

---

## Reglas de la expansión

- **Mono-consultorio**: sin `tenant_id` ni multi-sucursal (R2).
- **Sin requisitos externos**: pagos, facturación, notificaciones y QR se resuelven con adapters simulados y datos reales en la base.
- **Puerta abierta**: `Cobrador`, `Facturador` y `Notificador` son interfaces; un proveedor real se agrega después sin tocar el dominio.
- **Sin Redis/Celery**: `BackgroundTasks` y ejecución local.
- **Estados clínicos**: se mantienen los 6 de la KB; no se adoptan los 18 del roadmap viejo.
- **Numeración de migraciones**: tentativa; cada propose confirma la última versión real.

---

## Fases

| Fase | Changes |
|---|---|
| 0 — Base | C-01, C-02 |
| 1 — Auth | C-03 |
| 2 — Núcleo MVP base | C-04 a C-08 |
| 3 — Profundizar núcleo | C-09a, C-09b, C-10, C-11, C-12 |
| 4 — Facturación y clínica | C-13a, C-13b, C-14, C-15, C-16, C-17 |
| 5 — Portal y administración | C-18, C-19, C-20, C-21 |

---

## Árbol de dependencias

```
C-01 foundation
└─ C-02 core-models
   └─ C-03 auth
      ├─ C-04 agenda-servicio
      │  └─ C-05 agenda-frontend
      │     └─ C-09a agenda-dominio
      │        ├─ C-09b agenda-semanal
      │        ├─ C-10 reserva-avanzada
      │        └─ C-14 notificaciones
      │             └─ C-15 lista-espera
      ├─ C-06 reserva-publica ── C-10, C-14
      ├─ C-07 clinica ── C-11 ficha-avanzada
      ├─ C-08 caja ── C-12 caja-cierre
      ├─ C-11 + C-12 ── C-13a OS
      │                 ├─ C-13b comprobante
      │                 └─ C-16 presupuestos (también C-11/C-12)
      │                    └─ C-17 pagos (también C-12)
      │                       └─ C-18 portal (también C-10/C-16)
      ├─ C-03 ── C-19 admin
      ├─ C-20 auditoría/export (C-03, C-12, C-13a, C-16, C-18, C-19)
      └─ C-21 reportes (C-09a, C-12, C-13a, C-16, C-17)
```

**Cierre del MVP expandido:** C-01 a C-21. C-20 y C-21 son el cierre transversal (auditoría/export y reportes).

---

## Lista de Changes

### C-01: `foundation-setup` [x]
Backend FastAPI + frontend Vite/React + Compose + CI inicial. Layout actual `backend/` y `frontend/`.

### C-02: `core-models-seed` [x]
Nueve modelos SQLAlchemy (mono-tenant), migración `0002`, seed idempotente. Depende C-01.

### C-03: `auth-jwt-roles` [x]
Login JWT, `/auth/me`, RBAC (`admin`, `recepcion`, `odontologo`). Depende C-02.

### C-04: `agenda-servicio-antisolapamiento` [x]
Servicio y endpoints de turnos/bloqueos, antisolapamiento en servicio, 409, RBAC. Depende C-03.

### C-05: `agenda-frontend-interna` [x]
Agenda diaria por sillón, alta de turno, cambio de estado, login/logout. Depende C-04.

### C-06: `reserva-online-publica` [x]
Portal `/reservar`, disponibilidad, reserva con token, consulta/cancelación, WhatsApp click-to-chat. Depende C-04.

### C-07: `clinica-odontograma` [x]
Pacientes, odontograma FDI de 6 estados, upsert por pieza, RBAC y UI. Depende C-05.

### C-08: `caja-movimientos-balance` [x]
Libro append-only, alta de ingreso/egreso con usuario del JWT, listado y resumen diario. Depende C-05.

---

### C-09a: `agenda-dominio-avanzado`
- **Estado:** `[ ]`
- **Alcance:**
  - Reprogramación de turno con validación de solapamiento (excluyendo el propio turno).
  - Sobreturnos: flag, motivo obligatorio y autorizador; se permiten solapamientos deliberados.
  - Ventana mínima de cancelación configurable.
  - Estado `ausente` (no-show) en el catálogo y en la migración.
  - Migración `0004`: columnas de sobreturno, autorizador y `CHECK` de estado ampliado.
  - Tests de reprogramación, sobreturno autorizado, cancelación fuera de ventana y `ausente`.
- **Dependencias:** C-04, C-05.
- **Leer antes:** KB 05 (RN-AG-01/05/06), KB 06 (US-002), KB 07 (Flujo 4).
- **Gobernanza:** MEDIO.
- **Comando:** `/opsx:propose C-09a-agenda-dominio-avanzado`

### C-09b: `agenda-vista-semanal`
- **Estado:** `[ ]`
- **Alcance:** grilla semanal 7 días × 3 sillones, filtros por profesional, performance y estados visuales; consume C-09a.
- **Dependencias:** C-05, C-09a.
- **Leer antes:** KB 06 (US-001), KB 08 (frontend).
- **Gobernanza:** MEDIO.

### C-10: `reserva-publica-avanzada`
- **Estado:** `[ ]`
- **Alcance:**
  - QR local para `/reservar` y `/p/turno/:token`.
  - Pre-reserva con expiración y liberación automática.
  - Reprogramación pública con token y validación de huecos.
  - Rate-limit local; sin captcha externo.
  - Migración `0005` para expiración/origen si hace falta.
- **Dependencias:** C-06, C-09a.
- **Leer antes:** KB 05 (RN-AG-06/07), KB 07 (Flujo 1).
- **Gobernanza:** MEDIO.

### C-11: `ficha-clinica-avanzada`
- **Estado:** `[ ]`
- **Alcance:**
  - Evolución clínica por paciente (fecha, autor, texto).
  - Consentimiento informado (versión, fecha, autor).
  - Autor/fecha por hallazgo y historial de cambios por pieza.
  - Se mantienen los 6 estados de la KB.
  - Migración `0006` para evolución/consentimiento/autor.
- **Dependencias:** C-07.
- **Leer antes:** KB 04 (Odontograma), KB 05 (RN-CL-01/02), KB 06 (US-020).
- **Gobernanza:** CRÍTICO.

### C-12: `caja-cierre-cuenta-corriente`
- **Estado:** `[ ]`
- **Alcance:**
  - Cierre diario con aprobación de `admin` y bloqueo del período.
  - Cuenta corriente por paciente y saldo derivado.
  - Ajustes auditados; nunca update/delete del libro.
  - Export CSV del libro/cierre.
  - Migración `0007` para cierre/cuenta corriente.
- **Dependencias:** C-08.
- **Leer antes:** KB 04 (MovimientoCaja), KB 05 (RN-CJ-01/02/04), KB 06 (US-030/032).
- **Gobernanza:** CRÍTICO.

### C-13a: `os-nomenclador-cobertura`
- **Estado:** `[ ]`
- **Alcance:**
  - Catálogo de obras sociales y convenios.
  - Nomenclador de prácticas, aranceles y copago.
  - Afiliación del paciente y cálculo de cobertura.
  - Datos manuales; sin validación online externa.
  - Migración `0008`.
- **Dependencias:** C-11, C-12.
- **Leer antes:** KB 04 (OS/Nomenclador), KB 05 (RN-CJ-05), KB 06 (US-033).
- **Gobernanza:** MEDIO.

### C-13b: `comprobante-manual`
- **Estado:** `[ ]`
- **Alcance:**
  - Modelo `Comprobante` vinculado a movimiento/presupuesto.
  - `Facturador` + `FacturadorManual`; sin ARCA.
  - Estado pendiente/emitido/anulado; numeración manual.
  - Migración `0009`.
- **Dependencias:** C-13a, C-12.
- **Leer antes:** KB 04 (Comprobante), KB 05 (RN-CJ-05).
- **Gobernanza:** MEDIO.

### C-14: `notificaciones-simuladas`
- **Estado:** `[ ]`
- **Alcance:**
  - `Notificador` + `NotificadorSimulado` (BD/consola).
  - Plantillas de confirmación, recordatorio 24 h/2 h y lista de espera.
  - Link `wa.me`; reintentos locales; sin Meta API.
  - Migración `0010` para `Notificacion`.
- **Dependencias:** C-06, C-09a.
- **Leer antes:** KB 05 (RN-G-01), KB 06 (US-010).
- **Gobernanza:** MEDIO.

### C-15: `lista-espera`
- **Estado:** `[ ]`
- **Alcance:**
  - Lista de espera con preferencias y orden por compatibilidad/antigüedad.
  - Al cancelar, oferta automática con expiración y aceptación.
  - Usa C-14 para notificar; sin workers externos.
  - Migración `0011`.
- **Dependencias:** C-09a, C-10, C-14.
- **Leer antes:** KB 04 (ListaEspera), KB 05 (RN-AG-09), KB 06 (US-011), KB 07 (Flujo 4).
- **Gobernanza:** MEDIO.

### C-16: `presupuestos`
- **Estado:** `[ ]`
- **Alcance:**
  - `Presupuesto` + ítems, total y cobertura OS/copago.
  - Estados borrador/enviado/aprobado/rechazado/cobrado.
  - Aprobación online con token y firma simple.
  - Migración `0012`.
- **Dependencias:** C-11, C-12, C-13a.
- **Leer antes:** KB 04 (Presupuesto), KB 05 (RN-CL-03), KB 06 (US-021), KB 07 (Flujo 3).
- **Gobernanza:** ALTO.

### C-17: `pagos-simulados`
- **Estado:** `[ ]`
- **Alcance:**
  - `Pago`/`IntentoPago` con estados pendiente/aprobado/rechazado.
  - `Cobrador` + `CobradorSimulado`; sin Mercado Pago.
  - Confirmación idempotente: crea **un** `MovimientoCaja` real y actualiza turno/presupuesto.
  - Conciliación desde caja y confirmación desde el portal (C-18).
  - Migración `0013`.
- **Dependencias:** C-12, C-16.
- **Leer antes:** KB 05 (RN-CJ-01/02/03), KB 07 (Flujo 3).
- **Gobernanza:** CRÍTICO.

### C-18: `portal-publico`
- **Estado:** `[ ]`
- **Alcance:**
  - `/reservar` con QR (C-10), `/p/turno/:token`, `/p/presupuesto/:token`, `/p/pagar/:token`.
  - Marca única del consultorio; sin slug ni multi-tenant.
  - Página de pago simulado y confirmación.
  - Sin migración.
- **Dependencias:** C-10, C-16, C-17.
- **Leer antes:** KB 03 (rutas públicas), KB 07 (Flujo 1/3), KB 10.
- **Gobernanza:** MEDIO.

### C-19: `admin-crud`
- **Estado:** `[ ]`
- **Alcance:**
  - CRUD de usuarios con roles y activo.
  - CRUD de sillones.
  - CRUD de profesionales (matrícula, especialidad, duración, vínculo a usuario).
  - Baja lógica; no desactivar el último admin.
  - Sin migración.
- **Dependencias:** C-03.
- **Leer antes:** KB 03 (matriz RBAC), KB 04 (Usuario/Profesional/Sillon).
- **Gobernanza:** MEDIO/ALTO.

### C-20: `auditoria-export`
- **Estado:** `[ ]`
- **Alcance:**
  - Modelo `Auditoria` (quién, cuándo, recurso, acción, diff).
  - Hooks en escrituras sensibles (turnos, caja, presupuestos, odontograma).
  - Visor paginado y export CSV con enmascarado.
  - Migración `0014`.
- **Dependencias:** C-03, C-12, C-13a, C-16, C-18, C-19.
- **Leer antes:** KB 03, KB 05 (RN-SEG), KB 04 (Transversal).
- **Gobernanza:** CRÍTICO.

### C-21: `reportes`
- **Estado:** `[ ]`
- **Alcance:**
  - Ocupación por sillón/profesional.
  - Facturación por medio/OS.
  - Ausentismo y recupero.
  - Filtros por rango y export CSV.
  - Sin migración (consultas de lectura).
- **Dependencias:** C-09a, C-12, C-13a, C-16, C-17.
- **Leer antes:** KB 06 (US-041), KB 04 (Turno/MovimientoCaja), KB 09.
- **Gobernanza:** MEDIO.

---

## Trazabilidad con el roadmap viejo (22 changes)

| Viejo | Nuevo |
|---|---|
| C-01 foundation | C-01 |
| C-02 core-models-tenancy | C-02 (mono-tenant) |
| C-03 auth-rbac | C-03 |
| C-04 roles-auditoría-export | C-20 |
| C-05 agenda-núcleo | C-04 + C-09a |
| C-06 reserva-online | C-06 + C-10 |
| C-07 WhatsApp | C-14 (simulado) |
| C-08 agenda-frontend | C-05 + C-09b |
| C-09 ficha-odontograma | C-07 + C-11 |
| C-10 caja-cuenta-corriente | C-08 + C-12 |
| C-11 OS/nomenclador/comprobante | C-13a + C-13b |
| C-12 reportes | C-21 |
| C-13 lista de espera | C-15 |
| C-14 presupuestos | C-16 |
| C-15 clínica-frontend | C-11 + C-18 |
| C-16 Mercado Pago | C-17 (simulado) |
| C-17 portal público | C-18 |
| C-18 a C-22 | Fuera de alcance / fase futura |

---

## Definición de terminado (por change)

- Tests nuevos en verde y suite completa en verde dos veces seguidas.
- `ruff check src test` y frontend lint/tsc/build en verde.
- `openspec validate <change> --strict` y `openspec validate --all`.
- `business-rule-coverage-auditor` pasado y matriz actualizada.
- Change archivado y checklist marcado.
- Sin `git push --force`; commits conventional (R12).
