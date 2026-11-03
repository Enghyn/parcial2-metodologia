# Ficha de investigación — Skill propia y MCP

**Proyecto:** Sistema Odontológico Multi-Sillón (AR)
**Fecha:** 2026-10-14
**Equipo:** (completar apellidos)
**Estado:** Borrador — sección MCP pendiente de verificación.

---

## 1. Necesidad detectada

El proyecto tiene reglas de negocio densas (RN-AG-01..06, RN-CL-01, RN-CJ-01/02, RN-SEG-01, RN-G-01) y reglas duras (R1–R13) repartidas entre `knowledge-base/` y `AGENTS.md`. Hoy no existe un control sistemático de que cada regla tenga cobertura en specs, tasks, tests y código. Esto genera riesgo de archivar changes con reglas sin verificar (especialmente en agenda y caja).

## 2. Change elegido

**C-04 `agenda-servicio-antisolapamiento`** (pendiente según `CHANGES.md`). Es el change con más reglas de negocio y el que exige una suite exhaustiva de casos de solapamiento. La skill se puede usar también de forma transversal sobre cualquier change.

> Si en el entorno real todos los changes ya están implementados, usar la skill de forma transversal (auditoría periódica) o definir un change nuevo `C-09` de mantenimiento.

## 3. Skill creadora

- **Nombre:** `skill-creator`
- **Fuente:** skill instalada en el entorno (`.config/opencode/skills/skill-creator`), basada en la skill oficial de Anthropic para crear skills.
- **Compatibilidad:** agente OpenCode (este entorno). Genera `SKILL.md` con frontmatter YAML + instrucciones en Markdown.
- **Cómo se verificó:** invocada con `skill` tool; estructura generada revisada y adaptada al dominio.

## 4. Diseño de la skill propia

- **Nombre:** `business-rule-coverage-auditor`
- **Ubicación:** `.agents/skills/business-rule-coverage-auditor/SKILL.md`
- **Propósito:** auditar la cobertura de reglas RN-* y R1–R13 en specs/tasks/tests/código; detectar ambigüedades, conflictos y casos de borde faltantes; proponer adiciones. Solo lectura (no modifica artefactos).
- **Cuándo se activa:** al preparar o revisar cualquier change; antes de archivar; auditoría periódica.
- **Entradas:** `knowledge-base/05,04,06,07`, `AGENTS.md`, artefactos del change, tests.
- **Salida:** catálogo de reglas, matriz de cobertura, ambigüedades, conflictos, cobertura faltante propuesta, resumen cuantitativo, revisión crítica.
- **Criterios de revisión:** cada ✅ con evidencia concreta; propuestas citan RN-xx/R-x; ambigüedades como preguntas abiertas; salida en español rioplatense.

## 5. Comparación de servidores MCP (pendiente de verificación)

| Aspecto | MCP A — Context7 | MCP B — (a definir) |
|---|---|---|
| Propósito | Consulta de docs del stack (FastAPI, SQLAlchemy, React) | (completar) |
| Capacidades | `resolve-library-id`, `query-docs` | (completar) |
| Compatibilidad | OpenCode (ya instalado) | (completar) |
| Instalación | Sin credenciales | (completar) |
| Permisos/costos | Solo lectura de docs públicas, sin costo | (completar) |

**Elección tentativa:** Context7 (sin secretos, útil para verificar sintaxis en los escenarios generados).

> Completar el MCP B y la verificación real antes de la entrega. Registrar cualquier problema de acceso/compatibilidad.

## 6. Pasos de instalación/configuración MCP (pendiente)

- (Completar según documentación del servidor elegido y del cliente.)
- Verificación de conexión: ejecutar al menos una herramienta real y guardar evidencia (solicitud + resultado).

## 7. Archivos de la fundación a actualizar

- `.agents/skills/business-rule-coverage-auditor/SKILL.md` (creado)
- `.atl/skill-registry.md` (registrado)
- `AGENTS.md` y `CLAUDE.md` (actualizados con fila y nota de uso)
- `docs/skills-mcp/investigacion.md` (esta ficha)
- `docs/skills-mcp/aplicacion.md` (informe, a completar tras la integración)

## 8. Fuentes (URL y fecha de consulta)

- Enunciado TP "Skills y MCP – Metodología I" (PDF, 2026-10-14).
- `AGENTS.md` / `CLAUDE.md` del proyecto (reglas duras R1–R13).
- `knowledge-base/05_reglas_de_negocio.md` (RN-*).
- Documentación de `skill-creator` (entorno local).
- (Completar URLs de Context7 / MCP B con fecha de consulta.)

## Pendientes registrados

- Completar comparación y verificación del MCP.
- Ejecutar la skill sobre un change real y guardar evidencia (punto 8 del TP).
- Completar `docs/skills-mcp/aplicacion.md`.