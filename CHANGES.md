# CHANGES — Secuencia de Implementación

> Índice canónico de todos los changes del proyecto **Sistema odontológico multi-sillón (Argentina, SaaS multi-tenant)**.
> Cada change es atómico: un agente puede implementarlo en una sesión (~4-6 horas).
> **Leer este archivo antes de ejecutar cualquier `/opsx:propose`.**
> Orden alineado con el MVP recomendado en la sección D del informe de Discovery (`docs/discovery/discovery.md`): primero imprescindibles del §5, luego diferenciadores v1 de D, finalmente postergados del §6. ARCA queda en fase 2 por decisión DD-05. Redacción en español formal, con criterio crítico: se distingue entre **funcionalidad comprobada** (evidenciada en demo, tabla §A o código) y **afirmación comercial del proveedor** (cifra de vendor sin auditoría, p. ej. «−82 % ausencias», «45 M citas», «+300 clínicas» — ver SU-05; no se usan como compromiso).
> Excepción de orden por dependencia: C-10 (caja, imprescindible) → C-14 (presupuestos, diferenciador). La caja ya no depende de presupuestos (se invirtió la dependencia de la versión anterior) para que todo lo imprescindible preceda a los diferenciadores; presupuestos necesita caja y OS existentes para total/copago y link MP.

---

## Cómo usar este documento

1. Identificar el change a implementar (verificar que sus dependencias están en `openspec/changes/archive/`).
2. Leer los docs de la knowledge-base indicados en "Leer antes".
3. Ejecutar `/opsx:propose <nombre-del-change>`.
4. Al terminar el change, archivarlo con `/opsx:archive <nombre-del-change>`.
5. Marcar el checkbox `[x]` en este archivo.

---

## Cobertura del MVP

> Trazabilidad exhaustiva §5 + D → changes. Todo ítem del §5 y todo diferenciador v1 de D está contenido en el cierre MVP (C-01–C-17). Todo postergado del §6 está en fase 2 (C-18–C-22).

### Imprescindibles del §5 → change(s)

| # | Ítem §5 (discovery.md §5) | Change(s) | Notas |
|---|---|---|---|
| §5.1 | Agenda multi-profesional y multi-sillón con duración variable, bloqueos, sobreturnos y antisolapamiento | C-05 `agenda-nucleo-antisolapamiento`, C-08 `agenda-frontend-interna` | Núcleo + SPA interna; US-001–US-003 |
| §5.2 | Reserva online 24/7 con link/QR | C-06 `reserva-online-publica` | Link + **QR explícito** (SVG/PNG por `/reservar/:slug` y por `/p/turno/:token`); US-004 |
| §5.3 | Confirmación / cancelación / reprogramación (paciente autónomo + WhatsApp) | C-06 `reserva-online-publica`, C-07 `whatsapp-notificaciones` | Token público + webhook WA; US-005, Flujo 2 |
| §5.4 | Recordatorios automáticos WhatsApp | C-07 `whatsapp-notificaciones` | T-24 h / T-2 h, plantillas Meta, cupo; US-010 |
| §5.5 | Lista de espera que auto-rellena | C-13 `lista-espera-auto-relleno` | Doble naturaleza: figura en §5 (imprescindible) y en D (diferenciador v1) — se implementa en FASE 3 como primer diferenciador por depender de C-05+C-07; US-011 |
| §5.6 | Odontograma + ficha + presupuestos con aprobación online (base clínica) | C-09 `ficha-odontograma` (base imprescindible) + C-14 `presupuestos-aprobacion-online` (diferenciador, ver fila D.4) | Base clínica en MVP-puro; aprobación 1-click en diferenciadores; US-020/US-021 |
| §5.7 | Caja + cobro online Mercado Pago (link/seña) + cuenta corriente y recupero de deudas | C-10 `caja-trazable-cuenta-corriente` (imprescindible) + C-16 `cobros-mercadopago` (diferenciador, ver fila D.3) | Caja/cuenta corriente imprescindible; MP link/seña diferenciador por gate; US-030/US-032 + US-031 |
| §5.8 | Gestión de obras sociales con nomenclador | C-11 `os-nomenclador-comprobante-manual` | Tabla manual v1 (online real-time es supuesto SU-03); US-033 |
| §5.9 | Reportes de ocupación, facturación y ausentismo | C-12 `reportes-ocupacion-facturacion` | SQL directo v1; US-041 |
| §5.10 | Roles / permisos + auditoría + exportación | C-04 `roles-auditoria-exportacion` | Transversal de confianza, Ley 25.326; US-040 |
| §5.11 | Facturación electrónica ARCA: diseño preparado (Comprobante + adapter), implementación fase 2 | C-11 `os-nomenclador-comprobante-manual` (entidad `Comprobante` + `Facturador(manual)`) + C-21 `arca-facturacion-electronica` (fase 2) | Decisión de gate vigente; DD-05/RN-CJ-05; US-034/US-057 |

### Diferenciadores v1 de D (línea 118) → change(s)

| # | Diferenciador v1 (sección D) | Change(s) | Notas |
|---|---|---|---|
| D.1 | Lista de espera WA | C-13 `lista-espera-auto-relleno` | Ningún AR la evidencia — hipótesis a validar, no paridad (§C) |
| D.2 | OS+FE en un paso a futuro | C-11 (base manual ARCA-preparada) + C-21 (emisión ARCA real, fase 2 prioritaria) | v1 solo diseño preparado; emisión real post-MVP |
| D.3 | MP link/seña | C-16 `cobros-mercadopago` | Medio local dominante DD-04; solo IPN verificado cambia estado |
| D.4 | Presupuesto online | C-14 `presupuestos-aprobacion-online` + C-15 `clinica-frontend` | Aprobación 1-click con firma simple v1 |
| D.5 | Web incluida (portal) | C-17 `portal-web-publico` | `/reservar/:slug`, `/p/*`; SEO básico v1; cierra el MVP |

### Postergados del §6 → fase 2

| # | Ítem §6 | Change(s) fase 2 |
|---|---|---|
| §6.1 | Periodontograma avanzado | C-18 (parte) |
| §6.2 | Fichas de ortodoncia/implanto/prótesis | C-18 (parte) |
| §6.3 | Planes de tratamiento multifase | C-18 (parte) — **postergado (no figura en §5/§6, se fija aquí)**. No hay base en KB (US-*) para un plan básico MVP: US-020/US-021 no mencionan multifase; US-050 lo reserva a fase 2. Por decisión explícita queda en fase 2. |
| §6.4 | Imágenes con visor y segunda opinión por IA | C-19 (parte) |
| §6.5 | Campañas y recupero automatizado de inactivos | C-19 (parte) |
| §6.6 | API pública + sincronización Google Calendar bidireccional | C-20 (parte) |
| §6.7 | Multi-sucursal enterprise | C-20 (parte) |
| §6.8 | App móvil nativa | C-22 (parte) |
| §6.9 | Recepcionista virtual IA 24 h | C-22 (parte) |

### Definición de cierre MVP

> **El MVP cierra con los changes: C-01, C-02, C-03, C-04, C-05, C-06, C-07, C-08, C-09, C-10, C-11, C-12, C-13, C-14, C-15, C-16, C-17.**
> Criterio verificable: los flujos E2E Flujo 1 (reserva link/QR → confirmación), Flujo 2 (recordatorio WA → confirmar/cancelar), Flujo 3 (atención → odontograma → presupuesto online → pago MP → caja + comprobante manual), Flujo 4 (cancelación → lista de espera auto-relleno → turno) y Flujo 5 (cierre diario + reportes) funcionan en el tenant `demo` con 3 sillones, sin ARCA real (comprobante manual pendiente de FE) y con WA/MP degradados sin bloquear (RN-G-01).

---

## Árbol de dependencias

```
C-01 foundation-setup
  └── C-02 core-models-tenancy
        └── C-03 auth-rbac
              ├── C-04 roles-auditoria-exportacion
              └── C-05 agenda-nucleo-antisolapamiento     ← desbloquea agenda y caja
                    ├── C-06 reserva-online-publica (link+QR)
                    │     └── C-17 portal-web-publico      ← cierra el MVP
                    ├── C-07 whatsapp-notificaciones
                    │     └── C-13 lista-espera-auto-relleno  ← primer diferenciador
                    ├── C-08 agenda-frontend-interna
                    └── C-09 ficha-odontograma
                          └── C-10 caja-trazable-cuenta-corriente
                                ├── C-11 os-nomenclador-comprobante-manual
                                │     └── C-21 arca-facturacion-electronica [FASE 2, prioritaria]
                                ├── C-12 reportes-ocupacion-facturacion (base)
                                └── C-14 presupuestos-aprobacion-online  ← diferenciador (excepción orden: tras caja+OS)
                                      ├── C-15 clinica-frontend
                                      └── C-16 cobros-mercadopago
                                            ├── C-12 (cierre: reportes con MP)
                                            └── C-17 (cierre: portal con pago)
FASE 2 (tras C-17 ✓, sin orden interno salvo C-21 prioritaria):
  C-18 especialidades-avanzadas (C-09) · C-19 imagenes-ia-campanas (C-09)
  C-20 api-gcal-multisucursal (C-05,C-06) · C-22 app-nativa-recepcionista-ia (C-07,C-17)
```

### Paralelismo por fase

> Cada "gate" es un punto de sincronización. Los changes dentro de un grupo pueden ejecutarse en paralelo.

```
GATE 0: ninguna
  → C-01 foundation-setup (solo)

GATE 1: C-01 ✓
  → C-02 core-models-tenancy (solo)

GATE 2: C-02 ✓
  → C-03 auth-rbac (solo)

GATE 3: C-03 ✓                     ← PRIMER FORK (2 ramas)
  → C-04 roles-auditoria-exportacion    [Agente C]
  → C-05 agenda-nucleo-antisolapamiento [Agente A]

GATE 4: C-05 ✓                     ← FORK agenda pública + clínica
  → C-06 reserva-online-publica         [Agente A]
  → C-07 whatsapp-notificaciones        [Agente C]
  → C-09 ficha-odontograma              [Agente B]

GATE 5: C-06 + C-07 ✓
  → C-08 agenda-frontend-interna        [Agente A — si C-06 ✓]
  → C-09 (continúa)                     [Agente B]
  → C-13 lista-espera-auto-relleno      [Agente C]

GATE 6: C-09 ✓                      ← FORK caja/OS
  → C-10 caja-trazable-cuenta-corriente [Agente A]
  → C-08 (cierre)                       [Agente A — en paralelo si capacidad]
  → C-04 (cierre si restaba)            [Agente C]

GATE 7: C-10 ✓
  → C-11 os-nomenclador-comprobante-manual [Agente B]
  → C-12 reportes-ocupacion-facturacion (base sin MP) [Agente A]

GATE 8: C-10 + C-11 ✓               ← FORK diferenciadores (excepción orden aplicada)
  → C-14 presupuestos-aprobacion-online [Agente B]
  → C-12 (cierre)                       [Agente A]

GATE 9: C-14 ✓
  → C-15 clinica-frontend               [Agente B]
  → C-16 cobros-mercadopago             [Agente A]

GATE 10: C-06 + C-14 + C-16 ✓
  → C-17 portal-web-publico             [Agente C]
  → C-12 (cierre con MP)                [Agente A — si C-16 ✓]

GATE 11: MVP cerrado (C-17 ✓)        ← FORK FASE 2 (todo paralelo, sin orden interno)
  → C-18 especialidades-avanzadas       [Agente B]
  → C-19 imagenes-ia-campanas           [Agente C]
  → C-20 api-gcal-multisucursal         [Agente A]
  → C-21 arca-facturacion-electronica   [Agente A — si C-11 ✓, prioritaria post-MVP]
  → C-22 app-nativa-recepcionista-ia    [Agente C — si C-17 ✓]
```

### Camino crítico (11 changes — mínimo irreducible)

```
C-01 → C-02 → C-03 → C-05 → C-06 → C-09 → C-10 → C-11 → C-14 → C-16 → C-17
```

*Nota crítica: C-04 (roles/auditoría) corre en paralelo en GATE 3 pero es obligatoria antes del piloto con datos reales (Ley 25.326) aunque no esté en la cadena lineal. C-07 (WhatsApp) y C-13 (lista de espera) no figuran en la cadena lineal porque el MVP puede operar con confirmación manual si WA cae (RN-G-01, flujo degradado); no obstante, sin C-07 no se cumple la promesa de ausentismo del MVP. C-08 y C-12/C-15 son paralelizables y cierran fuera de la cadena. Fase 2 (C-18–C-22) queda fuera del camino crítico por definición.*

### Plan óptimo con 3 agentes

```
Paso │ Agente A (Backend Core)              │ Agente B (Backend Aux + Clínica/OS)          │ Agente C (Integraciones + Frontend)
─────┼──────────────────────────────────────┼──────────────────────────────────────────────┼─────────────────────────────────────────
  1  │ C-01 foundation-setup                │ —                                            │ —
  2  │ C-02 core-models-tenancy             │ —                                            │ —
  3  │ C-03 auth-rbac                       │ —                                            │ —
  4  │ C-05 agenda-nucleo                   │ C-09 ficha-odontograma                     │ C-04 roles-auditoria-exportacion
  5  │ C-06 reserva-link-QR                 │ C-09 (cierre)                              │ C-07 whatsapp-notificaciones
  6  │ C-08 agenda-frontend-interna         │ C-10 caja-cuenta-corriente (inicio)        │ C-13 lista-espera-auto-relleno
  7  │ C-10 (cierre)                        │ C-11 os-nomenclador-comprobante            │ C-13 (cierre)
  8  │ C-12 reportes (base)                 │ C-14 presupuestos                          │ C-08 apoyo / C-17 prep.
  9  │ C-16 cobros-mercadopago              │ C-15 clinica-frontend                      │ C-17 portal-web-publico
 10  │ C-16 (cierre) + C-12 (cierre MP)     │ C-15 (cierre)                              │ C-17 (cierre)
 11  │ C-20 api-gcal-multisucursal          │ C-18 especialidades-avanzadas              │ C-19 imagenes-ia-campanas
 12  │ C-21 arca-electronica (prioritaria)   │ —                                            │ C-22 app-nativa-recepcionista-ia
```

---

## FASE 0 — Cimientos

### [C-01] `foundation-setup`
- **Estado**: `[x]` pendiente
- **Scope**: Scaffolding completo del monolito modular + infraestructura base
  - Estructura `backend/app/{core,modules/{agenda,lista_espera,clinica,caja,os,notificaciones,admin},adapters,db,workers}` + `frontend/src/{app,features,shared}` según `08_arquitectura_propuesta.md` §Estructura
  - `backend`: FastAPI mínima con `GET /api/health`, Alembic inicializado, `core/` con settings (pydantic-settings), logger, handler de errores, middlewares base
  - `frontend`: Vite + React 18 + TypeScript + Zustand + Tailwind; router con superficies `/app/*` (privada) y `/reservar/*`, `/p/*` (pública)
  - `docker-compose.yml`: api + web + postgres 15+ (con `btree_gist`) + redis 7+ (+ worker RQ/Celery)
  - `.env.example` por sub-proyecto con las 15 variables de §Variables (`DATABASE_URL`, `REDIS_URL`, `JWT_SECRET`, `WA_*`, `MP_*`, `FACTURADOR_MODO=manual`, `ARCA_*` vacías fase 2, `CORS_ORIGINS`); sin secretos hardcodeados
  - CI GitHub Actions: jobs paralelos backend (ruff + pytest) y frontend (tsc + eslint)
  - Tests: health check, carga de settings, conexión DB/Redis en compose
- **Dependencias**: ninguna
- **Governance**: BAJO
- **Leer antes**:
  - `knowledge-base/01_vision_y_objetivos.md` (qué es el sistema y por qué existe)
  - `knowledge-base/02_descripcion_general.md` §Stack
  - `knowledge-base/08_arquitectura_propuesta.md` §Estructura de directorios
  - `knowledge-base/09_decisiones_y_supuestos.md` §DD-01, DD-02, DD-03

---

### [C-02] `core-models-tenancy`
- **Estado**: `[ ]` pendiente
- **Scope**: Modelos base multi-tenant + migraciones iniciales + seed mínimo
  - Modelos: `Tenant` (con `slug` único URL-safe, `plan` por_sillon v1, `cupo_wa_mensual`, `config_cancelacion:jsonb`), `Usuario` (`(tenant_id,email)` único, `rol` enum, `profesional_id?`), `Profesional` (matrícula, `duracion_default_min`, `agenda:jsonb`), `Sillon` (nombre único por tenant), `Paciente` (`(tenant_id,dni)` único, teléfono E.164, `consentimiento:jsonb`, `origen`)
  - `AuditMixin` (`is_active`, `created_at`, `updated_at`, `deleted_at`); `BaseRepository[T]` + `UnitOfWork`; filtro obligatorio por `tenant_id` en sesión (sin RLS en v1 — deuda declarada)
  - Migración 001 (Alembic): tablas core + índices (`slug`, `(tenant_id,rol)`, `(tenant_id,dni)`, `(tenant_id,telefono)`); extensión `btree_gist` habilitada para C-05
  - Seed mínimo: tenant `demo` (`slug=demo`), 1 admin, 1 recepción, 2 profesionales, 3 sillones («Sillón 1–3»)
  - Tests: unicidad slug/email/dni por tenant, aislamiento `tenant_id` (ningún query cruza consultorios — RN-SEG-01)
- **Dependencias**: C-01
- **Governance**: CRITICO
- **Leer antes**:
  - `knowledge-base/04_modelo_de_datos.md` §Tenant, §Usuario, §Profesional, §Sillon, §Paciente
  - `knowledge-base/05_reglas_de_negocio.md` §RN-SEG-01, §RN-AG-03
  - `knowledge-base/08_arquitectura_propuesta.md` §Patrones (RBAC por tenant, Exclusion constraint)
  - `knowledge-base/09_decisiones_y_supuestos.md` §DD-06, §DD-07

---

## FASE 1 — Autenticación y transversal de confianza (imprescindible §5.10)

### [C-03] `auth-rbac`
- **Estado**: `[ ]` pendiente
- **Scope**: Autenticación JWT + RBAC por tenant (matriz enforced en API)
  - `POST /api/v1/auth/login` — JWT access corto + refresh; rate-limit 5/60 s por IP+email; `POST /api/v1/auth/refresh` con rotación + blacklist; `POST /api/v1/auth/logout`; `GET /api/v1/auth/me`
  - Claims JWT: `sub`, `tenant_id`, `roles`, `email`, `jti`, `type`, `iat`, `exp`; refresh en cookie HttpOnly (secure, samesite=lax); signing keys por env con rotación documentada
  - Dependencia FastAPI `require(rol, recurso)` que aplica la matriz de `03_actores_y_roles.md` (admin/odontologo/recepcion/público); enforcement en backend, chequeo frontend solo cosmético
  - Paciente v1 sin JWT: opera con tokens públicos UUID (se crean en C-06/C-14; aquí solo el contrato `token_publico` + expiración + revocación — RN-SEG-04)
  - Migración 002: `refresh_blacklist(message_id, jti, exp)`, campos `profesional_id` si faltaban
  - Tests: login/refresh/logout, token expirado, aislamiento por tenant, matriz de permisos (recepción no edita odontograma — RN-CL-02; odontólogo no cobra — matriz)
- **Dependencias**: C-02
- **Governance**: CRITICO
- **Leer antes**:
  - `knowledge-base/03_actores_y_roles.md` §RBAC — Matriz de permisos
  - `knowledge-base/05_reglas_de_negocio.md` §RN-SEG-01, §RN-SEG-04, §RN-SEG-05
  - `knowledge-base/07_flujos_principales.md` §Flujo 1 (actor público sin login)
  - `knowledge-base/08_arquitectura_propuesta.md` §Seguridad

---

### [C-04] `roles-auditoria-exportacion`
- **Estado**: `[ ]` pendiente
- **Scope**: Gestión de usuarios/roles + auditoría trazable + exportación con resguardo (confianza/Ley 25.326 — diferencial declarado, ningún competidor la declara: discovery §7/§C, funcionalidad a comprobar en piloto, no afirmación comercial)
  - CRUD `Tenant/Usuario/Profesional/Sillon` (solo `admin`; recepción ve sin editar); asignación `usuario ↔ profesional` (si es odontólogo)
  - Modelo `Auditoria(quien, tenant_id, cuando, que, recurso_id, desde_donde, diff)`; hook automático en escrituras sensibles (turnos, caja, presupuestos, odontograma — RN-SEG-03); visor paginado + exportación CSV
  - Exportación CSV de turnos/caja/pacientes con enmascarado de PHI (pregunta abierta §10: formato CSV + enmascarado; v1: CSV con columnas sensibles solo para `admin`)
  - Endpoints: `/api/v1/admin/usuarios`, `/api/v1/admin/auditoria`, `/api/v1/admin/export/{recurso}.csv`
  - Tests: matriz enforced en API+UI, auditoría registra sobreturno/anulación/aprobación, exportación no expone PHI a `recepcion`
- **Dependencias**: C-03
- **Governance**: CRITICO
- **Leer antes**:
  - `knowledge-base/03_actores_y_roles.md` §RBAC — Matriz de permisos
  - `knowledge-base/05_reglas_de_negocio.md` §RN-SEG-02, §RN-SEG-03, §RN-CJ-01
  - `knowledge-base/04_modelo_de_datos.md` §Transversal (Auditoría, Consentimiento)
  - `knowledge-base/10_preguntas_abiertas.md` (exportación CSV + enmascarado PHI)

---

## FASE 2 — Imprescindibles MVP (§5 sin diferenciadores)

> Todos los imprescindibles del §5 antes que los diferenciadores v1. Caja (C-10) y OS (C-11) preceden a presupuestos/MP por dependencia técnica declarada arriba.

### [C-05] `agenda-nucleo-antisolapamiento`
- **Estado**: `[ ]` pendiente
- **Scope**: Núcleo de agenda con garantía a nivel DB contra doble reserva (problema central — discovery §7; antisolapamiento **comprobado** en DentalSaaS/DentalSoft según §C, a re-comprobar en piloto propio)
  - Modelos: `Turno` (con `sillon_id NOT NULL` — DD-06, `profesional_id NOT NULL`, `inicio/fin`, `duracion_min` variable, `estado` 8 valores, `origen`, `token_publico UUID`, `sena_monto/estado`), `Bloqueo` (sillón y/o profesional, como turno a efectos de huecos — RN-AG-04)
  - Exclusion constraints Postgres `EXCLUDE USING gist` por `(sillon_id, rango)` y `(profesional_id, rango)` excluyendo `cancelado/reprogramado` + chequeo en servicio (carrera doble-reserva); `fin = inicio + duración`; sobreturno explícito (flag + motivo + autorizador auditado — RN-AG-05)
  - Endpoints internos: `CRUD /api/v1/turnos`, `POST /api/v1/turnos/:id/{confirmar,cancelar,reprogramar}`, `CRUD /api/v1/bloqueos`, `GET /api/v1/agenda/dia|semana` (columnas por sillón, filtro profesional, bloqueos diferenciados, sobreturnos marcados; <2 s con 3 sillones × 30 turnos)
  - Cancelación con antelación configurable por tenant (default 12 h — RN-AG-06); fuera de término deriva a recepción + seña no reembolsable (RN-CJ-02)
  - Migración 003: tablas agenda + constraints + índices (`(tenant_id,inicio)`, `(sillon_id,inicio)`, `(profesional_id,inicio)`, `token_publico`)
  - Tests: solapamiento sillón y profesional rechazado con mensaje de conflicto, duración variable por prestación, bloqueo ocupa hueco, sobreturno auditado
- **Dependencias**: C-03
- **Governance**: CRITICO
- **Leer antes**:
  - `knowledge-base/04_modelo_de_datos.md` §Turno, §Bloqueo, §Sillon
  - `knowledge-base/05_reglas_de_negocio.md` §RN-AG-01 a RN-AG-06
  - `knowledge-base/06_funcionalidades.md` §Épica A (US-001, US-002, US-003)
  - `knowledge-base/09_decisiones_y_supuestos.md` §DD-06

---

### [C-06] `reserva-online-publica`
- **Estado**: `[ ]` pendiente
- **Scope**: API pública de reserva en 4 pasos sin login + link/QR explícito (supuesto SU-01 sin validar: «el paciente prefiere el link» — a medir con M-06 ≥60 % por link/QR; no prometerlo como hecho)
  - `GET /api/v1/public/disponibilidad/:slug` (prestación → duración; filtros profesional/sillón; descuenta turnos + bloqueos; RN-AG-01/02/04); `POST /api/v1/public/reservar/:slug` (nombre+DNI+teléfono E.164 → pre-reserva 15 min — RN-AG-07)
  - **QR explícito (§5 «link/QR»)**: `GET /api/v1/public/sitios/:slug/qr.(svg|png)` con URL de reserva + `GET /api/v1/turnos/:id/qr` con `/p/turno/:token`; QR imprimible para mostrador/folleto; `origen=linkQR` registrado en Paciente/Turno; sin QR el ítem §5.2 queda incompleto
  - `GET /p/turno/:token` + `POST /api/v1/public/turnos/:token/{confirmar,cancelar,reprogramar}` (reprogramación propone huecos equivalentes; respeta antelación o deriva a recepción — RN-AG-06/08; cada liberación dispara lista de espera — RN-AG-09)
  - Rate-limit + captcha en `/public/*`; firmas verificadas en webhooks (RN-SEG-05); error 409 con huecos alternativos si el hueco se tomó en el ínterin; 422 si teléfono inválido (turno no creado)
  - WA caído: turno igual creado + reintento con backoff + alerta (RN-G-01); idempotencia por `message_id`
  - Migración 004: `token_publico`, `oferta_*` si faltaban; tabla `webhook_event(event_id UNIQUE, procesado_at)`
  - Tests: reserva E2E sin login, QR escaneable resuelve a URL válida, pre-reserva expira, 409 con alternativas, tokens revocables sin exponer IDs internos
- **Dependencias**: C-05
- **Governance**: ALTO
- **Leer antes**:
  - `knowledge-base/03_actores_y_roles.md` §Rutas públicas
  - `knowledge-base/05_reglas_de_negocio.md` §RN-AG-06, §RN-AG-07, §RN-AG-08, §RN-SEG-04, §RN-SEG-05
  - `knowledge-base/06_funcionalidades.md` §US-004, §US-005
  - `knowledge-base/07_flujos_principales.md` §Flujo 1, §Flujo 2

---

### [C-07] `whatsapp-notificaciones`
- **Estado**: `[ ]` pendiente
- **Scope**: Adapter WA + jobs de recordatorio/confirmación (costo ~USD 0,026/mensaje según evidencia DentalSoft — discovery §8: **dato de vendor, a cotizar antes de prometer volumen**; cupo por plan + alerta 80 %)
  - `adapters/whatsapp.py` (interfaz `Notificador`; mock en tests); plantillas aprobadas Meta en rioplatense (recordatorio 24 h/2 h, confirmación, oferta lista de espera); modelo `Notificacion(turno_id, canal WA, plantilla, estado enviado/entregado/leído)` visible en agenda
  - Workers Redis (RQ/Celery): `recordatorios T-24h/T-2h`, expiración de ofertas, conciliación; reintentos con backoff + alerta (RN-G-01); sin PHI más allá de día/hora/profesional (RN-G-03)
  - `POST /api/v1/webhooks/whatsapp` (firma Meta verificada, idempotencia por `message_id`): respuesta Confirmar/Cancelar cambia el estado del turno (RN-AG-08); no-show → `ausente` (alimenta ausentismo + recupero)
  - Variables `WA_TOKEN`, `WA_PHONE_ID`, `WA_WEBHOOK_VERIFY`, `TENANT_DEFAULT_CANCEL_HS`, `LISTA_ESPERA_OFERTA_MIN`; cupo `cupo_wa_mensual` por tenant
  - Tests: envío con WA caído no bloquea reserva, webhook duplicado idempotente, estados visibles, cupo + alerta
- **Dependencias**: C-05
- **Governance**: ALTO
- **Leer antes**:
  - `knowledge-base/04_modelo_de_datos.md` §Transversal (Notificación/WA)
  - `knowledge-base/05_reglas_de_negocio.md` §RN-AG-08, §RN-G-01, §RN-G-03
  - `knowledge-base/06_funcionalidades.md` §US-010
  - `knowledge-base/07_flujos_principales.md` §Flujo 2
  - `knowledge-base/08_arquitectura_propuesta.md` §Patrones (Adapter, Jobs/colas, Webhooks idempotentes)

---

### [C-08] `agenda-frontend-interna`
- **Estado**: `[ ]` pendiente
- **Scope**: SPA interna de agenda día/semana por sillón (recepción/odontólogo/admin)
  - Vistas día (default) y semana con columnas por sillón, filtro profesional, bloqueos diferenciados, sobreturnos marcados; crear turno con duración auto por prestación/profesional (editable) y rechazo con mensaje de conflicto (RN-AG-01/02/03/05)
  - Acciones: confirmar/cancelar/reprogramar, gestión de bloqueos, log de ofrecimientos de lista de espera visible (preparado para C-13)
  - Consume `GET /api/v1/agenda/*`, `CRUD /api/v1/turnos|bloqueos`; RBAC cosmético (enforcement real en C-03)
  - Tests frontend: render <2 s con 3 sillones × 30 turnos, solapamiento muestra conflicto, sobreturno exige motivo
- **Dependencias**: C-05, C-06
- **Governance**: MEDIO
- **Leer antes**:
  - `knowledge-base/06_funcionalidades.md` §US-001, §US-002, §US-003
  - `knowledge-base/07_flujos_principales.md` §Flujo 1, §Flujo 4
  - `knowledge-base/08_arquitectura_propuesta.md` §Estructura frontend (features/agenda)
  - `knowledge-base/03_actores_y_roles.md` §RBAC — Matriz de permisos

---

### [C-09] `ficha-odontograma`
- **Estado**: `[ ]` pendiente
- **Scope**: Ficha clínica + odontograma por pieza (base clínica imprescindible del §5.6; 18 estados tipo DentalSoft según §A: **vocabulario declarado por vendor, a validar pieza por pieza en piloto**)
  - Modelos: `Odontograma(paciente_id UNIQUE, updated_by, updated_at)` + `HallazgoPieza(odontograma_id, pieza FDI 11–48, cara?, estado vocabulario cerrado 18, fecha, observacion)`; `Ficha/Evolucion(paciente_id, fecha, autor, texto)`; consentimiento obligatorio antes de cargar salud (RN-CL-04, Ley 25.326)
  - Solo `odontologo` edita (RN-CL-02); recepción ve resumen operativo; cada hallazgo con fecha y autor (RN-CL-01)
  - Endpoints: `CRUD /api/v1/pacientes`, `GET|PUT /api/v1/pacientes/:id/odontograma`, `POST /api/v1/pacientes/:id/evolucion`, `POST /api/v1/pacientes/:id/consentimiento`
  - Migración 005: tablas clínica + índices (`(odontograma_id,pieza)`); sin PHI en logs/WA (RN-G-03)
  - Tests: pieza FDI inválida rechazada, rol recepción no edita, sin consentimiento no carga salud
- **Dependencias**: C-03
- **Governance**: CRITICO
- **Leer antes**:
  - `knowledge-base/04_modelo_de_datos.md` §Paciente, §Odontograma
  - `knowledge-base/05_reglas_de_negocio.md` §RN-CL-01, §RN-CL-02, §RN-CL-04, §RN-SEG-02
  - `knowledge-base/06_funcionalidades.md` §US-020
  - `knowledge-base/09_decisiones_y_supuestos.md` §SU-05 (claims de vendors)

---

### [C-10] `caja-trazable-cuenta-corriente`
- **Estado**: `[ ]` pendiente
- **Scope**: Caja con trazabilidad total + cierre diario + cuenta corriente (sin planillas; imprescindible §5.7-base, sin MP que es C-16)
  - Modelo `MovimientoCaja(fecha, tipo ingreso/egreso, medio efectivo/mp_link/mp_terminal/transferencia/os, monto>0, turno_id?, presupuesto_id?, usuario_id, origen, concepto, anulacion_de?)`; prohibido UPDATE destructivo: solo anulación con contra-asiento vinculado (RN-CJ-01)
  - Cierre diario: suma por medio, conteo de efectivo físico, descuadre visible con ajuste auditado, aprobación `admin`, exportación CSV; webhook MP tardío entra al día siguiente sin reabrir cierre aprobado
  - Cuenta corriente por paciente como única fuente de deuda (RN-CJ-04): saldo derivado, listado de morosos con antigüedad, acción de recupero (WA + link MP cuando C-16 exista; v1 recupero manual auditado) auditada
  - Endpoints: `CRUD /api/v1/caja/movimientos`, `POST /api/v1/caja/movimientos/:id/anular`, `POST /api/v1/caja/cierre`, `GET /api/v1/cuenta-corriente/:paciente_id`, `GET /api/v1/cuenta-corriente/morosos`
  - Migración 006: tablas caja + índices (`(tenant_id,fecha)`, `(medio,fecha)`); Tests: borrado físico imposible, anulación enlazada, cierre no reabrible
- **Dependencias**: C-05
- **Governance**: CRITICO
- **Leer antes**:
  - `knowledge-base/04_modelo_de_datos.md` §MovimientoCaja
  - `knowledge-base/05_reglas_de_negocio.md` §RN-CJ-01, §RN-CJ-04
  - `knowledge-base/06_funcionalidades.md` §US-030, §US-032
  - `knowledge-base/07_flujos_principales.md` §Flujo 5

---

### [C-11] `os-nomenclador-comprobante-manual`
- **Estado**: `[ ]` pendiente
- **Scope**: Obras sociales con nomenclador + comprobante manual ARCA-preparado (base del «OS+FE en un paso» futuro; validación online real-time **no** en v1: solo DentalTec la evidenció — discovery §9/SU-03, v1 tabla manual)
  - Modelos: `ObraSocial(nombre, codigo, activa)` (catálogo global + convenios por tenant), `Nomenclador(obra_social_id, codigo p. ej. 01.01, practica, arancel, copago?, vigencia_desde)` con unicidad `(obra_social_id, codigo, vigencia_desde)` + búsqueda trigram en `practica`; afiliación `Paciente(obra_social_id, nro_afiliado)`; copago calculado automático en turno/presupuesto
  - Modelo `Comprobante(movimiento_id?, tipo recibo/factura_manual, numero?, emisor=manual, payload:jsonb fiscal, cae?, estado pendiente/emitido/anulado)` + `adapters/facturador.py` (`Facturador.emitir(manual)` en v1; en C-21 se añade `arca` sin tocar caja — DD-05/RN-CJ-05); conciliación manual visible (pendiente de FE) como mitigación del riesgo fiscal
  - Endpoints: `CRUD /api/v1/os`, `GET /api/v1/nomenclador/buscar?q=`, `POST /api/v1/turnos|presupuestos/:id/aplicar-cobertura`, `CRUD /api/v1/comprobantes`
  - Migración 007: tablas OS/nomenclador/comprobante + índices; seed: catálogo OS nacional mínimo + 20 prácticas; Tests: cobertura calcula copago, comprobante manual no bloquea caja
- **Dependencias**: C-10
- **Governance**: MEDIO
- **Leer antes**:
  - `knowledge-base/04_modelo_de_datos.md` §ObraSocial/Nomenclador, §Comprobante
  - `knowledge-base/05_reglas_de_negocio.md` §RN-CJ-05
  - `knowledge-base/06_funcionalidades.md` §US-033, §US-034
  - `knowledge-base/09_decisiones_y_supuestos.md` §DD-05, §SU-03

---

### [C-12] `reportes-ocupacion-facturacion`
- **Estado**: `[ ]` pendiente
- **Scope**: Reportes de ocupación, facturación y ausentismo para decidir precios y horarios (SQL directo sin warehouse en v1 — deuda declarada; cifras de vendors no son meta: M-02 usa −30 % conservador, no el «−82 %» comercial — SU-05)
  - 3 reportes con rango de fechas + comparativa semanal, exportables: ocupación por sillón/profesional, facturación por medio (efectivo/MP/OS), ausentismo (tasa + recupero); línea base propia por consultorio (validar SU-01/SU-04 con datos piloto)
  - Endpoints: `GET /api/v1/reportes/{ocupacion,facturacion,ausentismo}?desde=&hasta=`; permisos: dueño todo, recepción operativos, odontólogo producción propia
  - Tests: rangos y comparativas correctos, permisos por rol, exportación
- **Dependencias**: C-05, C-10
- **Governance**: MEDIO
- **Leer antes**:
  - `knowledge-base/06_funcionalidades.md` §US-041
  - `knowledge-base/05_reglas_de_negocio.md` §RN-CJ-01
  - `knowledge-base/04_modelo_de_datos.md` §Turno, §MovimientoCaja
  - `knowledge-base/09_decisiones_y_supuestos.md` §SU-01, §SU-04, §SU-05

---

## FASE 3 — Diferenciadores v1 (D: lista de espera, presupuesto online, MP, OS+FE futuro, web)

> Los changes C-13, C-14, C-16 y C-17 son los diferenciadores que ningún competidor AR combina en un precio (discovery §C): lista de espera con auto-relleno por WA (ningún AR la evidencia — oportunidad, no hecho), presupuesto aprobable en 1 click, MP link/seña y portal incluido. El «verificador OS + FE en un paso» queda como diseño preparado en C-11 y emisión real en C-21.

### [C-13] `lista-espera-auto-relleno`
- **Estado**: `[ ]` pendiente
- **Scope**: Lista de espera con auto-relleno por WhatsApp (diferenciador v1 D.1 y a la vez §5.5 — oportunidad detectada en Curve/Doctoralia/tab32 según §C; **ningún AR la evidencia**: tratarlo como hipótesis a validar, no como paridad)
  - Modelo `ListaEspera(paciente_id, prestacion, profesional_id?, preferencia:jsonb, estado activa/ofrecida/aceptada/vencida/cancelada, oferta_turno_id?, oferta_expira_at?)`; orden por compatibilidad + antigüedad (RN-AG-09)
  - Al cancelar: búsqueda de compatibles → oferta por WA al primero (`ofrecida`, expira 60 min default) con link de aceptación; si vence/rechaza pasa al siguiente; si acepta crea el Turno vinculado (`aceptada`); doble aceptación simultánea: gana la primera por antisolapamiento, la otra recibe alternativa
  - Endpoints: `CRUD /api/v1/lista-espera`, `POST /api/v1/lista-espera/:id/ofrecer`, jobs de expiración; log visible en agenda
  - Tests: auto-relleno E2E cancelación → oferta → aceptación → turno creado; expiración en cadena; concurrencia
- **Dependencias**: C-05, C-07
- **Governance**: MEDIO
- **Leer antes**:
  - `knowledge-base/04_modelo_de_datos.md` §ListaEspera
  - `knowledge-base/05_reglas_de_negocio.md` §RN-AG-09
  - `knowledge-base/06_funcionalidades.md` §US-011
  - `knowledge-base/07_flujos_principales.md` §Flujo 4

---

### [C-14] `presupuestos-aprobacion-online`
- **Estado**: `[ ]` pendiente
- **Scope**: Presupuestos con aprobación online en 1 click + enlace a cobro (diferenciador v1 D.4)
  - Modelos: `Presupuesto(paciente_id, odontologo_id, estado borrador/enviado/aprobado/rechazado/parcialmente_cobrado/cobrado, total, sena_requerida?, token_publico UNIQUE, valido_hasta)` + `ItemPresupuesto(nomenclador_id?, descripcion, cantidad, precio_unit, cobertura_os?)`; total = suma de ítems; transiciones válidas enforced (RN-CL-03)
  - Armado desde odontograma (C-09) + nomenclador/copago de C-11 (excepción de orden: necesita caja C-10 y OS C-11 previas); `enviado` genera link `/p/presupuesto/:token` por WA; aprobación registra quién/cuándo/IP como firma simple v1
  - Al aprobar con seña: genera link MP automáticamente (llama a C-16; si MP cae, presupuesto queda `aprobado` pendiente de link — RN-G-01)
  - Endpoints: `CRUD /api/v1/presupuestos`, `POST /api/v1/presupuestos/:id/enviar`, `GET /p/presupuesto/:token`, `POST /api/v1/public/presupuestos/:token/aprobar|rechazar`
  - Migración 008: tablas presupuesto + `token_publico`; Tests: total automático, transición inválida rechazada, aprobación audita IP
- **Dependencias**: C-09, C-10, C-11
- **Governance**: ALTO
- **Leer antes**:
  - `knowledge-base/04_modelo_de_datos.md` §Presupuesto
  - `knowledge-base/05_reglas_de_negocio.md` §RN-CL-03, §RN-CJ-03
  - `knowledge-base/06_funcionalidades.md` §US-021
  - `knowledge-base/07_flujos_principales.md` §Flujo 3

---

### [C-15] `clinica-frontend`
- **Estado**: `[ ]` pendiente
- **Scope**: SPA clínica: ficha, odontograma SVG adulto/infantil, presupuestos
  - Odontograma SVG por pieza FDI con 18 estados, fecha y autor por hallazgo; solo `odontologo` edita (botones ocultos por rol); evolución y consentimiento
  - Presupuestos: armado desde odontograma/nomenclador, total automático, `valido_hasta`, envío por WA, estado y aprobación visibles; recepción ve resumen operativo para cobrar sin re-cargar datos
  - Consume endpoints de C-09/C-14; Tests: edición bloqueada por rol, SVG renderiza 32+20 piezas, presupuesto muestra total y cobertura
- **Dependencias**: C-09, C-14
- **Governance**: MEDIO
- **Leer antes**:
  - `knowledge-base/06_funcionalidades.md` §US-020, §US-021
  - `knowledge-base/08_arquitectura_propuesta.md` §Estructura frontend (features/clinica)
  - `knowledge-base/03_actores_y_roles.md` §RBAC — Matriz de permisos
  - `knowledge-base/05_reglas_de_negocio.md` §RN-CL-01, §RN-CL-02

---

### [C-16] `cobros-mercadopago`
- **Estado**: `[ ]` pendiente
- **Scope**: Cobro online Mercado Pago link/seña conciliado por webhook (diferenciador v1 D.3; medio local dominante — DD-04; estados pendientes hasta IPN por diseño, no por fallo)
  - `adapters/mercadopago.py` (interfaz `Cobrador`; mock en tests); modelo `CobroMP(turno_id?, presupuesto_id?, monto, link, estado pendiente/aprobado/rechazado, mp_payment_id UNIQUE)`; link por turno/presupuesto (`POST /api/v1/cobros/mp-link`)
  - `POST /api/v1/webhooks/mercadopago` (firma `MP_WEBHOOK_SECRET` verificada, idempotente): cambia Turno/Presupuesto a `cobrado/señado` + crea `MovimientoCaja` solo con IPN verificado, nunca por callback frontend (RN-CJ-03)
  - Seña no reembolsable configurable (por tenant/prestación — pregunta abierta §10); devolución solo `admin`; pago sin webhook: estado `pendiente` con conciliación manual visible; monto distinto: alerta de descuadre + ajuste auditado (nunca edita el movimiento)
  - Tests: firma inválida rechazada, IPN duplicado idempotente, frontend callback no cambia estado
- **Dependencias**: C-10, C-14
- **Governance**: CRITICO
- **Leer antes**:
  - `knowledge-base/05_reglas_de_negocio.md` §RN-CJ-02, §RN-CJ-03, §RN-G-01
  - `knowledge-base/06_funcionalidades.md` §US-031
  - `knowledge-base/07_flujos_principales.md` §Flujo 3 (pasos 3–4)
  - `knowledge-base/08_arquitectura_propuesta.md` §Patrones (Adapter Cobrador, Webhooks idempotentes)
  - `knowledge-base/09_decisiones_y_supuestos.md` §DD-04

---

### [C-17] `portal-web-publico`
- **Estado**: `[ ]` pendiente
- **Scope**: Portal público del consultorio incluido (web/portal — diferenciador v1 D.5; SEO básico en v1, avanzado en fase 2 — DD-03)
  - Rutas: `GET /reservar/:slug` (reserva 4 pasos mobile-first: prestación → profesional/sillón → horario → datos, con QR alternativo de C-06), `GET /p/turno/:token` (confirmar/cancelar/reprogramar), `GET /p/presupuesto/:token` (ver/aprobar/rechazar), `GET /p/pagar/:token` (MP); consume C-06/C-14/C-16; rate-limit + captcha; español rioplatense, precios ARS (RN-G-02)
  - Marca por tenant (`slug`, nombre, horarios); sin login (pregunta abierta §10: login pasa a fase 2 si se decide)
  - Tests E2E mínimos del flujo reserva → cobro (deuda: e2e completos en fase 2): reserva → confirmación WA → atención → presupuesto → pago MP → caja
- **Dependencias**: C-06, C-07, C-14, C-16
- **Governance**: MEDIO
- **Leer antes**:
  - `knowledge-base/03_actores_y_roles.md` §Rutas públicas
  - `knowledge-base/07_flujos_principales.md` §Flujo 1, §Flujo 3
  - `knowledge-base/08_arquitectura_propuesta.md` §DD-03, §Estructura frontend (reserva-publica)
  - `knowledge-base/06_funcionalidades.md` §US-004, §US-005, §US-021

---

## FASE 4 — Post-MVP / Fase 2 (postergados §6 + ARCA)

> Todo lo de esta fase depende del MVP cerrado (C-17 ✓). Sin orden interno obligatorio salvo C-21 prioritaria post-MVP (pregunta abierta §10: afecta a clínicas RI del piloto). Cada change mantiene adapters sin tocar caja (DD-05) y fracaso degradado (RN-G-01).

### [C-18] `especialidades-avanzadas`
- **Estado**: `[ ]` pendiente
- **Scope**: Periodontograma avanzado + fichas de ortodoncia/implanto/prótesis + planes multifase [FASE 2 — incluye el postergado «planes de tratamiento multifase» que no figura en §5/§6 y se fija aquí]
  - Modelos: `Periodontograma(paciente_id, sextante, profundidad_bolsa, sangrado, movilidad, recesión)` + `FichaEspecialidad(tipo orto/implanto/protesis, plan_multifase:jsonb, firma)`; extiende C-09 sin romper odontograma base
  - Endpoints: `CRUD /api/v1/periodontograma/:paciente_id`, `CRUD /api/v1/especialidades/*`; frontend: chart perio SVG + planes multifase; solo `odontologo` edita
  - Migración 009; Tests: sondaje válido, plan multifase versionado
- **Dependencias**: C-09, C-17
- **Governance**: MEDIO
- **Leer antes**:
  - `knowledge-base/04_modelo_de_datos.md` §Odontograma
  - `knowledge-base/06_funcionalidades.md` §US-050
  - `knowledge-base/08_arquitectura_propuesta.md` §Deuda documentada
  - `knowledge-base/10_preguntas_abiertas.md` (segmento día 1)

---

### [C-19] `imagenes-ia-campanas`
- **Estado**: `[ ]` pendiente
- **Scope**: Imágenes con visor + segunda opinión por IA + campañas de inactivos [FASE 2]
  - Visor DICOM/JPG (Rx panorámica/periapical) asociado a pieza; anotaciones; `opinion_ia:jsonb` marcada explícitamente como **segunda opinión sin validez diagnóstica** (no prometer precisión clínica: afirmaciones de IA de vendors — Dentalink/Doctocliq/Odonthia §C — son comerciales hasta validar)
  - Campañas: segmento de inactivos/ausentes → envío WA masivo con cupo y opt-out (extiende C-07/C-13); `Campana(segmento, plantilla, envios, conversiones)`; recupero auditado
  - Endpoints: `POST /api/v1/imagenes`, `GET /api/v1/imagenes/:id`, `POST /api/v1/imagenes/:id/opinion-ia`, `CRUD /api/v1/campanas`
  - Tests: PHI solo con auth, IA no bloquea flujo clínico, campaña respeta opt-out y cupo
- **Dependencias**: C-09, C-17
- **Governance**: ALTO
- **Leer antes**:
  - `knowledge-base/06_funcionalidades.md` §US-051, §US-052
  - `knowledge-base/05_reglas_de_negocio.md` §RN-SEG-02, §RN-G-03
  - `knowledge-base/09_decisiones_y_supuestos.md` §SU-04, §SU-05
  - `knowledge-base/04_modelo_de_datos.md` §Paciente, §Transversal

---

### [C-20] `api-gcal-multisucursal`
- **Estado**: `[ ]` pendiente
- **Scope**: API pública + Google Calendar bidireccional + base multi-sucursal enterprise [FASE 2]
  - API pública versionada (`/api/v2/*`, OpenAPI gratis por FastAPI — DD-02): API keys por tenant, scopes, rate-limit, webhooks salientes de turnos/caja; sincronización GCal bidireccional (crear/editar/cancelar con idempotencia; conflictos: gana el antisolapamiento local — RN-AG-01)
  - Multi-sucursal: `Sede(tenant_id, nombre, direccion)` + `Sillon.sede_id?`, `Turno.sede_id?`; v1: tenants separados por sede (pregunta abierta §10); este change añade sede única con migración reversible
  - Migración 010: `sedes`, `api_keys`, `gcal_sync`; Tests: sync idempotente, API no expone otros tenants
- **Dependencias**: C-05, C-06, C-17
- **Governance**: ALTO
- **Leer antes**:
  - `knowledge-base/06_funcionalidades.md` §US-053, §US-054
  - `knowledge-base/08_arquitectura_propuesta.md` §Patrones (Adapter, RBAC por tenant)
  - `knowledge-base/10_preguntas_abiertas.md` (multi-sucursal: tenant único vs separados)
  - `knowledge-base/05_reglas_de_negocio.md` §RN-AG-01, §RN-SEG-01

---

### [C-21] `arca-facturacion-electronica`
- **Estado**: `[ ]` pendiente
- **Scope**: Facturación electrónica ARCA vía adapter + validación OS online [FASE 2, primera candidata post-MVP]
  - `adapters/facturador.py`: `Facturador(arca)` (WSFE: CUIT, cert, key, endpoint por `ARCA_*`) que emite sobre `Comprobante` de C-11 y completa `cae`; `FACTURADOR_MODO=arca` por tenant; sin cambios en caja (DD-05); homologación y certificados documentados; conciliación pendiente → emitida visible
  - Validación OS online (modelo DentalTec 15+ OS real-time — **caso institucional comprobado solo en DentalTec**; generalizarlo es supuesto SU-03: implementar como conector por OS con fallback a tabla manual)
  - Endpoints: `POST /api/v1/comprobantes/:id/emitir-arca`, `GET /api/v1/comprobantes/pendientes-fe`, `POST /api/v1/os/:id/validar-cobertura`
  - Tests: emisión mock ARCA, CAE persistido, fallback manual si ARCA cae (RN-G-01)
- **Dependencias**: C-10, C-11
- **Governance**: CRITICO
- **Leer antes**:
  - `knowledge-base/04_modelo_de_datos.md` §Comprobante
  - `knowledge-base/05_reglas_de_negocio.md` §RN-CJ-05, §RN-G-01
  - `knowledge-base/06_funcionalidades.md` §US-057, §US-034
  - `knowledge-base/09_decisiones_y_supuestos.md` §DD-05, §SU-03
  - `knowledge-base/10_preguntas_abiertas.md` (prioridad ARCA post-MVP)

---

### [C-22] `app-nativa-recepcionista-ia`
- **Estado**: `[ ]` pendiente
- **Scope**: App móvil nativa + recepcionista virtual IA 24 h (evolución de US-010) [FASE 2, última]
  - App nativa (paciente: reserva/gestión/pago; consultorio: agenda lite) compartiendo API de C-20; push + deep links a `/p/*`; depende de que el portal (C-17) ya valide conversión (no construirla antes de validar SU-01)
  - Recepcionista IA: bot conversacional sobre WA que resuelve reserva/confirmación/reprogramación llamando a C-06/C-13; límites explícitos (deriva a humano fuera de confianza; sin diagnósticos; sin PHI en prompts más allá de lo operativo — RN-G-03); «24/7» de vendors (Dentalink WA+IA — §C) es **afirmación comercial hasta medir resolución sin humano en piloto**
  - Endpoints: `POST /api/v1/ia/recepcionista/mensaje`, panel de supervisión y takeover humano; Tests: handoff correcto, sin alucinación de huecos (solo huecos reales de C-06)
- **Dependencias**: C-07, C-17
- **Governance**: ALTO
- **Leer antes**:
  - `knowledge-base/06_funcionalidades.md` §US-055, §US-056
  - `knowledge-base/07_flujos_principales.md` §Flujo 1, §Flujo 2, §Flujo 4
  - `knowledge-base/05_reglas_de_negocio.md` §RN-AG-07, §RN-AG-08, §RN-G-03
  - `knowledge-base/09_decisiones_y_supuestos.md` §SU-01, §SU-05
