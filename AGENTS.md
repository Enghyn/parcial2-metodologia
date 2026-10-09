# Sistema Odontológico Multi-Sillón (AR) — Instrucciones para Agentes

> Este archivo (y su copia `CLAUDE.md`) es lo PRIMERO que todo agente lee al entrar al repo.
> Generado a partir de `knowledge-base/` y `CHANGES.md`. No editar a mano sin re-sincronizar ambos archivos.

---

## Stack Tecnológico

| Capa | Tecnología | Versión |
|------|------------|---------|
| Frontend | React + TypeScript + Vite + Zustand + Tailwind | React 18, TS 5 |
| Backend | Python + FastAPI + SQLAlchemy + Alembic | Python 3.12+, FastAPI 0.11x |
| Persistencia | PostgreSQL (con `btree_gist`) | PG 15+ |
| Colas/Jobs | Redis (RQ/Celery) | Redis 7+ |
| Infra local | Docker / Docker Compose (api + web + postgres + redis + worker) | — |
| Auth | JWT (access corto + refresh rotado, claims `tenant_id`) | — |
| Integraciones | WhatsApp Business API, Mercado Pago (links + webhooks), web/portal propio (MVP); ARCA + Google Calendar (fase 2) | — |

Detalle completo: [knowledge-base/02_descripcion_general.md](knowledge-base/02_descripcion_general.md)

---

## Base de Conocimiento

La fuente de verdad del dominio vive en `knowledge-base/`. **Leé el archivo relevante ANTES de implementar.**

| Archivo | Cuándo leerlo |
|---------|---------------|
| [01_vision_y_objetivos.md](knowledge-base/01_vision_y_objetivos.md) | Entender propósito y alcance |
| [03_actores_y_roles.md](knowledge-base/03_actores_y_roles.md) | Auth, RBAC, permisos |
| [04_modelo_de_datos.md](knowledge-base/04_modelo_de_datos.md) | Entidades, ERD, migraciones |
| [05_reglas_de_negocio.md](knowledge-base/05_reglas_de_negocio.md) | Reglas codificadas (RN-XX) |
| [06_funcionalidades.md](knowledge-base/06_funcionalidades.md) | Historias de usuario por épica |
| [07_flujos_principales.md](knowledge-base/07_flujos_principales.md) | Flujos E2E |
| [08_arquitectura_propuesta.md](knowledge-base/08_arquitectura_propuesta.md) | Patrones, estructura, env vars |
| [10_preguntas_abiertas.md](knowledge-base/10_preguntas_abiertas.md) | ⚠️ Inconsistencias a resolver ANTES de codear |

> ⚠️ Resolver las preguntas de prioridad **Alta** de `10_preguntas_abiertas.md` antes de arrancar el primer change.

Discovery previo (mercado, comparativa 17 sistemas, MVP): [docs/discovery/discovery.md](docs/discovery/discovery.md)

---

## Skills Disponibles

Skills instaladas a nivel proyecto (`.agents/skills/`), mapeadas por rol. Cargá la skill del contexto ANTES de escribir código.

| Agente | Rol | Skills que carga |
|--------|-----|------------------|
| **Backend Core** | FastAPI modular, JWT, Alembic, Postgres | `fastapi-templates`, `postgresql-table-design`, `supabase-postgres-best-practices`, `async-python-patterns` |
| **Backend Aux** | Integraciones, contratos, webhooks | `api-and-interface-design`, `async-python-patterns` |
| **Frontend** | React+Vite, reserva online, agenda, odontograma | `vercel-react-best-practices`, `tailwind-design-system` |
| **Calidad** | Testing E2E y estrategia | `playwright-cli` |

> Los compact rules de cada skill los resuelve el orquestador desde `.atl/skill-registry.md` (generado por `skill-registry`; no versionado — no está en el repo). Esta tabla solo mapea skill→rol.

---

## Roadmap de Changes

El plan de implementación completo está en [CHANGES.md](CHANGES.md). Resumen:

- **Total**: 22 changes en 5 fases (0 cimientos, 1 auth/confianza, 2 imprescindibles MVP, 3 diferenciadores v1, 4 fase 2).
- **Camino crítico** (11): `C-01 → C-02 → C-03 → C-05 → C-06 → C-09 → C-10 → C-11 → C-14 → C-16 → C-17`.
- **Cierre del MVP**: changes C-01–C-17 + 5 flujos E2E verificables (ver "Cobertura del MVP" en CHANGES.md).
- **Primer change**: `C-01-foundation-setup` → arrancar con `/opsx:propose C-01-foundation-setup`.

**Antes de cualquier `/opsx:propose`**: leé [CHANGES.md](CHANGES.md), identificá las dependencias del change y los archivos de "Leer antes".

---

## Reglas Duras (específicas del proyecto)

No hay `~/.claude/CLAUDE.md` global en este entorno: todo lo de abajo vive acá. Son contrato; romperlas es un defecto. Formato `NUNCA X → hacer Y`:

- **R1**: NUNCA schema Pydantic sin `extra='forbid'` → rechazar campos no declarados.
- **R2**: NUNCA query sin filtro `tenant_id` → ningún dato cruza de consultorio (RN-SEG-01).
- **R3**: NUNCA UPDATE/DELETE físico en caja → solo anulación con contra-asiento vinculado (RN-CJ-01).
- **R4**: NUNCA cambiar estado por callback del frontend (MP) → solo webhook con firma verificada (RN-CJ-03).
- **R5**: NUNCA código sin type hints + `snake_case`, y NUNCA cambio de schema sin migración Alembic.
- **R6**: NUNCA turno sin garantía antisolapamiento a nivel DB → `EXCLUDE USING gist` por sillón y profesional + test de conflicto (RN-AG-01).
- **R7**: NUNCA `any` → tipado estricto (`tsconfig` strict); componentes en `PascalCase`.
- **R8**: NUNCA confiar en el frontend para permisos → el RBAC se cumple en el backend, la UI solo oculta (cosmético).
- **R9**: NUNCA datos de salud en logs ni WhatsApp → solo día/hora/profesional (RN-G-03, Ley 25.326).
- **R10**: Superficies públicas en rioplatense y precios en ARS (RN-G-02).
- **R11**: NUNCA commitear ni pushear sin pedido explícito → los cambios quedan en working tree.
- **R12**: Commits en formato conventional (`feat:`, `fix:`, `chore:`…) sin co-autoría IA.
- **R13**: NUNCA borrado físico en tablas de negocio → borrado lógico con `deleted_at` + `deleted_by`, restaurable por `admin`; purga solo explícita y auditada (RN-SEG-06).

---

## Flujo de Trabajo

```
1. Leer la KB relevante (knowledge-base/)        → entender el dominio
2. Identificar el change en CHANGES.md           → respetar dependencias
3. /opsx:propose C-NN-nombre                     → proposal + design + specs + tasks
4. Implementar las tasks (cargando skills)       → respetando las reglas duras
5. /opsx:archive C-NN-nombre + marcar [x]        → cerrar el change
```

Aplicar TODAS las reglas duras en cada paso. Ante conflicto entre la KB y este archivo, las reglas duras prevalecen.
