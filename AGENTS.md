# Sistema Odontológico Multi-Sillón (AR) — Instrucciones para Agentes

> Este archivo (y su copia `CLAUDE.md`) es lo PRIMERO que todo agente lee al entrar al repo.
> Generado a partir de `knowledge-base/` y `CHANGES.md`. No editar a mano sin re-sincronizar ambos archivos.

---

## Stack Tecnológico

| Capa | Tecnología | Versión |
|------|------------|---------|
| Frontend | React + TypeScript + Vite + Zustand + Tailwind | React 18, TS 5 |
| Backend | Python + FastAPI + SQLAlchemy + Alembic | Python 3.12+, FastAPI 0.11x |
| Persistencia | PostgreSQL (índices relacionales estándar) | PG 15+ |
| Infra local | Docker / Docker Compose (api + web + postgres) | Compose v2 |
| Auth | JWT Bearer estándar con roles (`admin`, `recepcion`, `odontologo`) | — |
| Comunicación / Cobros | Click-to-Chat WhatsApp (`wa.me/`), cobros y señas directos en caja | — |

Detalle completo: [knowledge-base/02_descripcion_general.md](knowledge-base/02_descripcion_general.md)

---

## Base de Conocimiento

La fuente de verdad del dominio vive en `knowledge-base/`. **Leé el archivo relevante ANTES de implementar.**

| Archivo | Cuándo leerlo |
|---------|---------------|
| [01_vision_y_objetivos.md](knowledge-base/01_vision_y_objetivos.md) | Entender propósito, alcance del MVP académico y actores |
| [02_descripcion_general.md](knowledge-base/02_descripcion_general.md) | Stack, arquitectura modular y endpoints de la API |
| [03_actores_y_roles.md](knowledge-base/03_actores_y_roles.md) | Auth, RBAC, permisos y rutas públicas |
| [04_modelo_de_datos.md](knowledge-base/04_modelo_de_datos.md) | Entidades relacionales, atributos, índices y seed |
| [05_reglas_de_negocio.md](knowledge-base/05_reglas_de_negocio.md) | Reglas codificadas (RN-AG, RN-CL, RN-CJ, RN-SEG, RN-G) |
| [06_funcionalidades.md](knowledge-base/06_funcionalidades.md) | Historias de usuario por épica y criterios de aceptación |
| [07_flujos_principales.md](knowledge-base/07_flujos_principales.md) | Flujos E2E de reserva, atención, odontograma y caja |
| [08_arquitectura_propuesta.md](knowledge-base/08_arquitectura_propuesta.md) | Patrones, estructura de carpetas, seguridad y env vars |
| [09_decisiones_y_supuestos.md](knowledge-base/09_decisiones_y_supuestos.md) | Decisiones DD-01 a DD-07 y supuestos operativos |
| [10_preguntas_abiertas.md](knowledge-base/10_preguntas_abiertas.md) | Decisiones fundacionales cerradas y detalles de implementación |

---

## Skills Disponibles

Skills instaladas a nivel proyecto (`.agents/skills/`), mapeadas por rol. Cargá la skill del contexto ANTES de escribir código.

| Agente | Rol | Skills que carga |
|--------|-----|------------------|
| **Backend Core** | FastAPI modular, JWT, Alembic, Postgres | `fastapi-templates`, `postgresql-table-design`, `supabase-postgres-best-practices`, `async-python-patterns` |
| **Backend Aux** | Contratos de API, endpoints y validaciones | `api-and-interface-design`, `async-python-patterns` |
| **Frontend** | React+Vite, reserva online, agenda multi-sillón, odontograma | `vercel-react-best-practices`, `tailwind-design-system` |
| **Calidad** | Testing unitario y E2E | `playwright-cli` |
| **Auditoría** | Cobertura de reglas de negocio y reglas duras | `business-rule-coverage-auditor` |

> **Skill propia `business-rule-coverage-auditor`**: audita la cobertura de las reglas RN-* y R1–R13 en specs/tasks/tests/código. Se activa al preparar o revisar cualquier change y antes de archivar. Entradas: KB (05, 04, 06, 07), AGENTS.md, artefactos del change y tests. Salida: matriz de cobertura + ambigüedades + conflictos + propuestas + revisión crítica. La skill es de solo lectura: no modifica artefactos; las propuestas se aplican en un paso posterior. Fuente versionada: `.agents/skills/business-rule-coverage-auditor/SKILL.md`.

---

## Roadmap de Changes

El plan de implementación académico simplificado está en [CHANGES.md](CHANGES.md). Resumen:

- **Total**: 8 changes atómicos organizados para desarrollo incremental:
  - `C-01-foundation-setup` [x] (Completado y archivado)
  - `C-02-core-models-seed` [x] (Completado y archivado): Entidades SQLAlchemy, migraciones Alembic y seed inicial (sillones, usuarios y profesionales).
  - `C-03-auth-jwt-roles` [x] (Completado y archivado): Login JWT Bearer y dependencias de autorización RBAC (`admin`, `recepcion`, `odontologo`).
  - `C-04-agenda-servicio-antisolapamiento`: Capa de servicios y endpoints de turnos con validación estricta de solapamiento (sillón y profesional) + tests unitarios.
  - `C-05-agenda-frontend-interna`: Visualización de agenda en columnas por sillón, creación y cambio de estados de turnos en React.
  - `C-06-reserva-online-publica`: Portal público `/reservar` sin login, consulta de turnos por token y enlace directo a WhatsApp (`wa.me/`).
  - `C-07-clinica-odontograma`: Gestión de pacientes, ficha médica y odontograma interactivo esquemático FDI (piezas 11 a 48).
  - `C-08-caja-movimientos-balance`: Registro de ingresos/egresos, señas vinculadas a turnos y arqueo diario de caja.

**Antes de cualquier `/opsx:propose`**: leé [CHANGES.md](CHANGES.md), identificá las dependencias del change y los archivos de "Leer antes".

---

## Reglas Duras (específicas del proyecto)

Son contrato; romperlas es un defecto. Formato `NUNCA X → hacer Y`:

- **R1**: NUNCA schema Pydantic sin `extra='forbid'` → rechazar campos no declarados.
- **R2**: NUNCA modelo ni query con `tenant_id` → el sistema es mono-consultorio enfocado en multi-sillón (2 a 3 sillones físicos).
- **R3**: NUNCA UPDATE/DELETE físico en caja → trazabilidad obligatoria con movimientos de ingreso/egreso compensatorios (RN-CJ-02).
- **R4**: NUNCA cobro de turno sin registrar medio de pago y usuario responsable en caja (RN-CJ-01).
- **R5**: NUNCA código sin type hints + `snake_case`, y NUNCA cambio de schema sin migración Alembic.
- **R6**: NUNCA turno creado o reprogramado sin validación antisolapamiento en la capa de servicios + test de conflicto obligatorio (RN-AG-01).
- **R7**: NUNCA `any` → tipado estricto (`tsconfig` strict); componentes en `PascalCase`.
- **R8**: NUNCA confiar en el frontend para permisos → el RBAC se cumple en el backend, la UI solo oculta o deshabilita cosméticamente.
- **R9**: NUNCA datos sensibles de salud en logs ni en parámetros de URL (RN-SEG-01).
- **R10**: Superficies públicas en español rioplatense y montos en ARS.
- **R11**: NUNCA commitear ni pushear sin pedido explícito → los cambios quedan en working tree.
- **R12**: Commits en formato conventional (`feat:`, `fix:`, `chore:`…) sin co-autoría IA.
- **R13**: NUNCA borrado físico en tablas de negocio (`Paciente`, `Turno`, `Profesional`, `Sillon`) → borrado lógico con `deleted_at`.

---

## Flujo de Trabajo

```
0. Tras `git pull`, actualizar la base (ver abajo)  → antes de tests/backend
1. Leer la KB relevante (knowledge-base/)        → entender el dominio
2. Identificar el change en CHANGES.md           → respetar dependencias
3. /opsx:propose C-NN-nombre                     → proposal + design + specs + tasks
4. Implementar las tasks (cargando skills)       → respetando las reglas duras
5. /opsx:archive C-NN-nombre + marcar [x]        → cerrar el change
```

### Puesta al día del entorno local (obligatorio después de un `git pull`)

Si el pull trae migraciones nuevas (o no sabés si las trae), antes de levantar el backend o correr tests de integración:

```powershell
cd backend
alembic upgrade head
```

- Es idempotente: si la base ya está al día, no hace nada.
- Datos de demo opcionales (también idempotente): `python -m app.db.seed`.
- Si falla la conexión, verificá `DATABASE_URL` y que PostgreSQL esté corriendo.
- No corras `alembic -c backend/alembic.ini` desde la raíz: el cwd canónico es `backend/`.

Un agente NO debe declarar el entorno listo ni correr tests de integración sin haber aplicado `alembic upgrade head` cuando el pull incluyó migraciones.

Aplicar TODAS las reglas duras en cada paso. Ante conflicto entre la KB y este archivo, las reglas duras prevalecen.
