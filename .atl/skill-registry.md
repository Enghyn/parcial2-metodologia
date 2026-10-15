# Skill Registry

**Delegator use only.** Any agent that launches sub-agents reads this registry to resolve compact rules, then injects them directly into sub-agent prompts. Sub-agents do NOT read this registry or individual SKILL.md files.

Scope: **project-local only** — every skill below lives in `.agents/skills/` in this repo. Global user-home skill dirs contain only orchestrator machinery and are intentionally excluded.

## Project Skills (scope: project, location: `.agents/skills/`)

| Trigger | Skill | Path |
|---------|-------|------|
| Writing, reviewing, or refactoring React/Next.js code — components, pages, data fetching, bundle optimization, performance improvements | vercel-react-best-practices | .agents/skills/vercel-react-best-practices/SKILL.md |
| Creating component libraries, implementing design systems, or standardizing UI patterns (Tailwind v4) | tailwind-design-system | .agents/skills/tailwind-design-system/SKILL.md |
| Writing or changing anything in Postgres (tables, schema, migrations, RLS, indexes, triggers, functions, queues/jobs, pgvector, restores) or diagnosing slow queries, CPU, timeouts, EXPLAIN, connections, locking, bloat, wrong-tenant rows | supabase-postgres-best-practices | .agents/skills/supabase-postgres-best-practices/SKILL.md |
| Designing or reviewing a PostgreSQL-specific schema — types, keys, constraints, indexes, partitioning, zero-downtime changes | postgresql-table-design | .agents/skills/postgresql-table-design/SKILL.md |
| Building new FastAPI applications or setting up backend API projects | fastapi-templates | .agents/skills/fastapi-templates/SKILL.md |
| Building async APIs, concurrent systems, or I/O-bound applications requiring non-blocking operations | async-python-patterns | .agents/skills/async-python-patterns/SKILL.md |
| Designing APIs, module boundaries, or any public interface — REST/GraphQL endpoints, type contracts, frontend/backend boundaries | api-and-interface-design | .agents/skills/api-and-interface-design/SKILL.md |
| Automating browser interactions, testing web pages, working with Playwright tests | playwright-cli | .agents/skills/playwright-cli/SKILL.md |

## Compact Rules

Pre-digested rules per skill. Delegators copy matching blocks into sub-agent prompts as `## Project Standards (auto-resolved)`.

### vercel-react-best-practices
- Fetch in parallel with Promise.all — never await in loops; start promises early, await late in the branch where used
- No barrel-file imports — import modules directly; next/dynamic for heavy components; load analytics/third-party after hydration; preload on hover/focus
- Stream with <Suspense> boundaries; dedupe client fetches with SWR; dedupe global event listeners (passive for scroll)
- Memoize expensive subtrees via extracted memoized components (not useMemo for primitives); derive state during render, not in effects; functional setState for stable callbacks
- Never define components inside components; put interaction logic in event handlers; startTransition/useDeferredValue for non-urgent renders; ternary (not &&) for conditionals
- Server: React.cache() per-request dedup + LRU cross-request; hoist static I/O to module level; never share mutable module state across requests; minimize client-component props/serialization
- Gotcha: shared module state and duplicate RSC-prop serialization silently bloat bundles — read rule files under rules/ for the exact pattern

### tailwind-design-system
- Tailwind v4 only: CSS-first config — `@import "tailwindcss"` + `@theme` in CSS; NO tailwind.config.ts, NO `@tailwind base` directives
- Tokens: semantic colors in OKLCH (--color-primary, etc.), radius (--radius-*), animations (--animate-* with @keyframes inside @theme)
- Dark mode: `@custom-variant dark (&:where(.dark, .dark *))` + `.dark {}` token overrides — never `darkMode: "class"` config
- Component layering: base styles → variants → sizes → states → overrides; brand → semantic → component token hierarchy
- Base layer: `* @apply border-border`; `body @apply bg-background text-foreground antialiased`
- Read references/details.md when the quick patterns are insufficient
- Gotcha: v3 patterns (config file, require("tailwindcss-animate")) silently fail in v4 — use CSS @keyframes + @starting-style

### supabase-postgres-best-practices
- Load BEFORE any Postgres change — even a one-column change or a single query
- Queries: add missing indexes for filters/joins/sorts; prefer composite (leftmost-prefix), covering (INCLUDE), partial (WHERE hot subset) indexes; match index type to operator
- Connections: always pool (transaction mode for serverless); respect connection limits; set idle timeouts; prefer prepared statements
- Security: RLS on every multi-tenant table + tests verifying isolation; keep policies sargable (no per-row function calls); least-privilege grants
- Schema: PK on reference tables; lowercase snake_case identifiers; index every FK manually; CHECK constraints; partition huge time-series tables
- Concurrency: short transactions; SKIP LOCKED for queues; advisory locks for cooperative work; consistent lock order against deadlocks
- Data access: batch inserts; upsert via ON CONFLICT; keyset/cursor pagination (not OFFSET at scale); eliminate N+1
- Diagnose with EXPLAIN ANALYZE + pg_stat_statements; run VACUUM/ANALYZE; watch bloat and lock waits; one rule file per topic under references/

### postgresql-table-design
- PK: `BIGINT GENERATED ALWAYS AS IDENTITY`; UUID only for distributed/opaque IDs (uuidv7 on PG18+ or gen_random_uuid())
- Normalize to 3NF first; denormalize only for measured hot reads with proven join pain
- NOT NULL everywhere semantically required + DEFAULTs; money = NUMERIC, time = TIMESTAMPTZ, strings = TEXT (+CHECK length cap); never timestamp/serial/money/varchar(n)/char(n)/timetz
- Index every FK column manually (PG does NOT auto-index FKs); composite leftmost-prefix with most-selective-first; expression indexes must match the query expression exactly
- No-overlap (agenda anti-solape): `EXCLUDE USING gist (sillon_id WITH =, periodo WITH &&)` — needs a GiST-capable range type
- UNIQUE allows multiple NULLs — use `UNIQUE NULLS NOT DISTINCT` (PG15+) to permit only one NULL
- ENUM types only for small stable sets; else TEXT+CHECK or lookup table; JSONB (not JSON) + GIN for semi-structured attributes only
- snake_case unquoted identifiers (unquoted folds to lowercase); identity/sequence gaps are normal — never "fix"; partition (RANGE/LIST/HASH) only beyond ~100M rows; details in references/details.md

### fastapi-templates
- Layout: app/{api/v1/endpoints, core(config/security/database), models, schemas(pydantic), services, repositories} + main.py; versioned routers (/api/v1)
- All handlers async; DB sessions via yield-based get_db Depends DI; auth/config as dependencies, never globals
- Never block the loop in handlers — delegate CPU/blocking I/O to workers (see async-python-patterns)
- Validate in/out with Pydantic schemas (separate input vs output models); consistent error responses; idempotent webhooks (see api-and-interface-design)
- Alembic migration for every schema change; JWT auth scoped per role
- Tests: httpx AsyncClient + app.dependency_overrides[get_db] against an isolated test DB; worked patterns in references/details.md

### async-python-patterns
- Stay fully sync OR fully async within a call path — never mix (hidden blocking)
- Concurrency: asyncio.gather(*tasks) for independent I/O; create_task for background work; never time.sleep() in async (await asyncio.sleep); CPU work → asyncio.to_thread()
- Timeout every external call: asyncio.wait_for(coro, timeout); bulk work with gather(return_exceptions=True) + filter failures
- Cancellation: catch asyncio.CancelledError for cleanup, then re-raise to propagate
- Never await inside sync code (SyntaxError) — enter via asyncio.run(); test with pytest-asyncio @pytest.mark.asyncio
- Reminders/campaigns/reconciliation run in workers (Redis), never blocking API handlers
- Advanced patterns (streams, queues, backpressure, shutdown) live in references/details.md

### api-and-interface-design
- Contract first: typed input/output schemas before implementation; the types ARE the documentation
- One error shape everywhere: {error:{code, message, details?}} + fixed status map (400/401/403/404/409/422/500; never leak internals on 500)
- Validate at boundaries only (route handlers, forms, env, third-party responses — always untrusted); internal code trusts types
- REST: plural nouns, no verbs; PATCH = partial update; every list paginated (page/pageSize + totals); camelCase fields; booleans is/has/can; enums UPPER_SNAKE
- Extend, don't break: new fields optional/additive (Hyrum's Law — every observable behavior is a contract); plan deprecation at design time
- Idempotent state-changing endpoints: client-generated key once per intent; claim atomically via unique constraint (never check-then-insert); same-key+different-body → 422; deliberate in-flight response (409/wait/202); retention ≥ longest retry/DLQ replay
- No queue gives exactly-once across consumer crash — design at-least-once + idempotent handlers

### playwright-cli
- Flow: open [url] → snapshot (refs e1, e2…) → click/fill/press/type on refs → snapshot to verify → close; find "text" greps large snapshots
- Prefer snapshot refs (click e15, fill e5 "x" --submit); CSS/role/getByTestId locators also work
- Efficiency: --mobile for lighter pages; scoped/--depth snapshots; --raw to pipe eval/cookie/snapshot into jq/files/diff
- Auth/persistence: state-save/state-load auth.json; cookie/local/session storage get/set/clear commands
- Mocks/debug: route patterns with --status/--body; console/requests/tracing-start|stop; recording-start|stop emits Playwright code
- Sessions: -s=name for parallel browsers; close-all/kill-all cleanup; open --browser/--device/--persistent/--profile; attach --cdp for existing Chrome/Edge
- Windows URLs with &: `playwright-cli --% goto "…?a=1&b=2"` in PowerShell, `^&` in cmd.exe
- Allowed tools: Bash(playwright-cli:*) / Bash(npx playwright:*) only; attach screenshots/videos to PRs via gh --attach (see references/)

## Project Conventions

| File | Path | Notes |
|------|------|-------|
| AGENTS.md | AGENTS.md | Index — references knowledge-base/ files and CHANGES.md below; hard rules R1–R13 are binding |
| CLAUDE.md | CLAUDE.md | Mirror of AGENTS.md (agent entry point) |
| CHANGES.md | CHANGES.md | Implementation roadmap, referenced by AGENTS.md |
| 01_vision_y_objetivos.md | knowledge-base/01_vision_y_objetivos.md | Referenced by AGENTS.md |
| 02_descripcion_general.md | knowledge-base/02_descripcion_general.md | Referenced by AGENTS.md (stack detail) |
| 03_actores_y_roles.md | knowledge-base/03_actores_y_roles.md | Referenced by AGENTS.md (auth/RBAC) |
| 04_modelo_de_datos.md | knowledge-base/04_modelo_de_datos.md | Referenced by AGENTS.md (entities/ERD) |
| 05_reglas_de_negocio.md | knowledge-base/05_reglas_de_negocio.md | Referenced by AGENTS.md (RN-XX rules) |
| 06_funcionalidades.md | knowledge-base/06_funcionalidades.md | Referenced by AGENTS.md (user stories) |
| 07_flujos_principales.md | knowledge-base/07_flujos_principales.md | Referenced by AGENTS.md (E2E flows) |
| 08_arquitectura_propuesta.md | knowledge-base/08_arquitectura_propuesta.md | Referenced by AGENTS.md (patterns/env) |
| 09_decisiones_y_supuestos.md | knowledge-base/09_decisiones_y_supuestos.md | Knowledge base |
| 10_preguntas_abiertas.md | knowledge-base/10_preguntas_abiertas.md | Referenced by AGENTS.md (blockers before coding) |
| README.md | knowledge-base/README.md | Knowledge-base index |

Read the convention files listed above for project-specific patterns and rules. All referenced paths have been extracted — no need to read index files to discover more.
