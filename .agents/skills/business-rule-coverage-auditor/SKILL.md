---
name: business-rule-coverage-auditor
description: Audits coverage of business rules (RN-*) and hard rules (R1–R13) across specs, tasks, tests, and code of the dental clinic project. Use whenever the user mentions business rules, RN-AG, RN-CL, RN-CJ, RN-SEG, RN-G, rule coverage, audit, "qué reglas están cubiertas", "faltan tests", "revisar reglas", "auditoría de reglas", or prepares/reviews any change (proposal, design, spec, tasks) in this repo — even if they don't explicitly say "audit". Always use this skill before archiving a change or when asked for a critical review.
---

# Business Rule Coverage Auditor

## Overview

This skill audits **whether each business rule and hard rule of the Sistema Odontológico Multi-Sillón (AR) is actually covered** by the project's artifacts: knowledge base, specs, tasks, tests, and (optionally) code. It does not implement anything; it **detects gaps, ambiguities, and conflicts** and proposes concrete additions.

It is the project's tool for the "revisión crítica" required by the TP: find a real omission, show before/after, and cite the source that corrects it.

## When to Use

- Preparing or reviewing any change (`proposal.md`, `design.md`, `spec.md`, `tasks.md`).
- Before archiving a change, to confirm coverage.
- When asked "what rules are covered / missing", "are there untested rules", "audit rules".
- Periodic domain audit of the whole project (transversal).
- When a new rule is added to the KB and you need to know the impact.

## Inputs Required

Always read these **before** producing the audit (do not guess):

| Input | Path | Why |
|-------|------|-----|
| Business rules | `knowledge-base/05_reglas_de_negocio.md` | Source of RN-AG, RN-CL, RN-CJ, RN-SEG, RN-G |
| Hard rules | `AGENTS.md` (section "Reglas Duras") | R1–R13 (binding) |
| Actors/auth | `knowledge-base/03_actores_y_roles.md` | RBAC rules |
| Data model | `knowledge-base/04_modelo_de_datos.md` | Entities/indexes that back rules |
| User stories | `knowledge-base/06_funcionalidades.md` | Acceptance criteria |
| Flows | `knowledge-base/07_flujos_principales.md` | E2E paths |
| Change artifacts | `openspec/changes/<name>/` | proposal/design/spec/tasks |
| Tests (if exist) | `backend/tests/`, `frontend/` | Actual coverage |

If an input is missing, **record it as a gap**, do not invent content.

## Procedure

Follow these steps in order. Do not skip.

### Step 1 — Extract the rule catalog
Build a table of every rule to audit:
- `RN-AG-01..RN-AG-06` (agenda)
- `RN-CL-01` (clínica/odontograma)
- `RN-CJ-01`, `RN-CJ-02` (caja)
- `RN-SEG-01` (datos sensibles)
- `RN-G-01` (WhatsApp click-to-chat)
- `R1..R13` (reglas duras de AGENTS.md)

For each rule record: **ID, short text, source (file + section), type (business/hard)**.

### Step 2 — Extract candidate coverage
For the scope (a single change, or the whole project), collect from:
- `spec.md` scenarios (Given/When/Then or bullet scenarios)
- `tasks.md` checklist items
- Test files (pytest/vitest) — test names and assertions
- Code (optional, if available) — service/repository functions

For each candidate, note **which rule ID it claims to cover** (explicitly or by intent).

### Step 3 — Build the coverage matrix
Cross rule ↔ artifact. Mark status:
- ✅ **Covered** — at least one scenario/test/code path exercises the rule, with the expected outcome (HTTP code, state, error).
- ⚠️ **Partial** — mentioned but missing an edge case, or no explicit verification.
- ❌ **Not covered** — no artifact references it.
- ➖ **N/A** — rule does not apply to this scope (justify).

### Step 4 — Detect ambiguities
Flag rules whose wording admits multiple interpretations and has no decided source. Examples from this project:
- "Duración del turno según prestación (variable por configuración, no fija global)" — *¿la configuración es por prestación o por profesional?* No decided → open question.
- "Cancelación/reprogramación con antelación mínima configurable" — *¿quién configura, admin o profesional?* Not decided.
- "La seña puede ser no reembolsable" — *¿cuándo se retiene, en qué estados?* Not decided.

For each ambiguity: state the rule, the two readings, and a proposed decision + where to record it (`knowledge-base/10_preguntas_abiertas.md`).

### Step 5 — Detect conflicts
Find pairs that contradict:
- Rule vs rule (e.g., "borrado lógico con deleted_at" R13 vs a spec that proposes hard delete).
- Rule vs design (e.g., a design that stores `tenant_id` violating R2).
- Rule vs code (if code available).
List each conflict with **both sources** and which one wins (hard rules R1–R13 prevail over KB per AGENTS.md).

### Step 6 — Propose missing coverage
For every ❌ and ⚠️, propose concrete additions:
- A scenario in Given/When/Then with expected HTTP code / state.
- A test case name (pytest/vitest) and what it asserts.
- The verification criterion to add to `tasks.md`.

Never invent domain rules. If a gap implies a new rule, record it as an open question, not as a decision.

### Step 7 — Produce the report
Use the output format below. End with a "Revisión crítica" section: at least one omission/error found (or a documented edge-case probe if none found).

## Output Format

```markdown
# Auditoría de cobertura de reglas — <scope>

**Fecha:** YYYY-MM-DD
**Scope:** <change name | "proyecto completo">
**Fuentes leídas:** <list>

## 1. Catálogo de reglas auditadas
| ID | Texto (resumido) | Fuente | Tipo |

## 2. Matriz de cobertura
| Regla | Artefacto que la cubre | Estado | Verificación |

## 3. Ambigüedades detectadas
- RN-xx: <regla> → lectura A / lectura B → propuesta → dónde registrar

## 4. Conflictos detectados
- <regla A> vs <regla B/diseño/código>: ... → prevalece ...

## 5. Cobertura faltante propuesta
### 5.1 Escenarios (Given/When/Then)
### 5.2 Casos de test
### 5.3 Criterios para tasks.md

## 6. Resumen cuantitativo
- Reglas auditadas: N
- ✅ cubiertas: X (p%)
- ⚠️ parciales: Y
- ❌ sin cobertura: Z

## 7. Revisión crítica
- Omisión/error detectado: <descripción>
- Cómo se detectó: <método>
- Fuente que permitió corregir: <archivo/sección>
- Antes: <texto original>
- Después: <texto corregido>
```

If no defect is found in the initial run, probe an edge case (e.g., a cancelled turn in the same slot, or a rule with no test) and document the result without inventing an error.

## Scope Selection

Ask or infer the scope before auditing:
- **Single change**: audit only that change's artifacts (faster, focused).
- **Project-wide**: audit all `openspec/changes/` + tests + KB (slower, transversal).

Default to **single change** if a change name is given; otherwise ask.

## Rules (binding)

- **Never invent domain rules.** Proposals must cite RN-xx or R-x. If no source exists, mark as "decisión de dominio a justificar" and record as open question.
- **Hard rules R1–R13 prevail** over KB in conflicts (per AGENTS.md).
- **Never mark a rule as covered without evidence** (scenario/test/code path). "Mentioned in a doc" ≠ covered.
- **Never modify artifacts during the audit.** This skill is read-only + proposal. Implementation is a separate step.
- **Always read the source files**, do not rely on memory or prior summaries.
- **Spanish rioplatense** for all output (project convention R10).

## Red Flags

- Marking ✅ without a concrete scenario/test/code reference.
- Proposing a scenario that contradicts a hard rule (R1–R13).
- Inventing a business rule not present in the KB.
- Auditing from memory instead of reading the files.
- Modifying artifacts during the audit (this skill is read-only).

## Verification

After running the audit:
- [ ] Every rule in the catalog has a status (✅/⚠️/❌/➖).
- [ ] Every ❌/⚠️ has at least one concrete proposal.
- [ ] Every proposal cites a source rule (RN-xx or R-x).
- [ ] Ambiguities are recorded as open questions, not resolved.
- [ ] Conflicts state which rule prevails and why.
- [ ] "Revisión crítica" section is present with before/after (or documented edge-case probe).
- [ ] Output is in Spanish rioplatense.
- [ ] No artifact was modified by this skill.

## Example (condensed)

**Scope:** C-04 (agenda).

**Catalog (excerpt):**
| RN-AG-01 | Un sillón/profesional no puede tener dos turnos superpuestos | 05 §Reglas | business |
| RN-AG-02 | Duración variable según prestación | 05 §Reglas | business |

**Matrix (excerpt):**
| RN-AG-01 | C-04 spec "Crear turno en hueco libre" | ⚠️ parcial | Falta caso de solapamiento de profesional en distinto sillón |
| RN-AG-02 | (ninguno) | ❌ | No hay escenario ni test de duración |

**Proposed edge case:**
> Given un turno existente en Sillón 1 (Prof. A, 10:00–10:30)
> When se crea un turno en Sillón 2 (Prof. A, 10:15–10:45)
> Then 409 Conflict (RN-AG-01, profesional)

**Critical review:**
- Omission: el spec original no incluía el caso de solapamiento de profesional en distinto sillón.
- Source: RN-AG-01 ("un profesional tampoco").
- Before: "Crear turno en hueco libre → 201."
- After: añadido escenario de conflicto por profesional → 409.