# Sistema odontológico SaaS multi-tenant (AR) — Base de Conocimiento

Base de conocimiento generada por `kb-creator` (modo interactivo, Q&A cerrada por el orquestador) a partir de `docs/discovery/discovery.md`, `docs/discovery/sources/` (5 fichas) y las decisiones del gate 2026-10-01. Stack real: Python + FastAPI + SQLAlchemy + PostgreSQL + Redis + Docker / React + TypeScript + Vite.

## Índice de Archivos

| Archivo | Contenido |
|---------|-----------|
| [01_vision_y_objetivos.md](01_vision_y_objetivos.md) | Propósito, objetivos por actor, alcance v1.0, fuera de alcance, métricas M-01–M-07 |
| [02_descripcion_general.md](02_descripcion_general.md) | Stack real, arquitectura monolito modular + ASCII, integraciones WA/MP/web, endpoints por recurso |
| [03_actores_y_roles.md](03_actores_y_roles.md) | Actores, matriz RBAC admin/recepción/odontólogo, rutas públicas `/reservar/:slug` |
| [04_modelo_de_datos.md](04_modelo_de_datos.md) | Dominios, ERD textual, 14 entidades con tipos/relaciones/índices, seed mínima |
| [05_reglas_de_negocio.md](05_reglas_de_negocio.md) | RN-AG/RN-CL/RN-CJ/RN-SEG/RN-G: antisolapamiento, duración variable, seña, trazabilidad, Ley 25.326 |
| [06_funcionalidades.md](06_funcionalidades.md) | Épicas A–F, US-001–US-057 con criterios de aceptación; MVP vs fase 2 |
| [07_flujos_principales.md](07_flujos_principales.md) | Reserva online, confirmación WA, atención+presupuesto+cobro MP, auto-relleno, cierre de caja |
| [08_arquitectura_propuesta.md](08_arquitectura_propuesta.md) | Patrones, árbol backend/frontend, seguridad JWT/RBAC/secrets, env vars |
| [09_decisiones_y_supuestos.md](09_decisiones_y_supuestos.md) | DD-01–DD-07 (monolito, MP en MVP, ARCA fase 2 con adapter, pricing por sillón), SU-01–SU-05 |
| [10_preguntas_abiertas.md](10_preguntas_abiertas.md) | 9 preguntas priorizadas (login paciente, prioridad ARCA, validación OS, costo WA) |

## Quick Start para Desarrolladores

1. Entender el dominio → [01](01_vision_y_objetivos.md), [03](03_actores_y_roles.md)
2. Entender los datos → [04](04_modelo_de_datos.md)
3. Entender las reglas → [05](05_reglas_de_negocio.md)
4. Entender la arquitectura → [02](02_descripcion_general.md), [08](08_arquitectura_propuesta.md)
5. Implementar → [07](07_flujos_principales.md), [06](06_funcionalidades.md)
6. Antes de codificar → [10](10_preguntas_abiertas.md)

## Resumen Ejecutivo

SaaS multi-tenant para consultorios odontológicos argentinos (foco 2–3 sillones) que unifica agenda antisolapada, reserva online, WhatsApp, odontograma, Mercado Pago y obras sociales donde ningún competidor local lo hace en un solo precio. MVP en monolito modular FastAPI + React con ARCA preparada vía adapter para fase 2. Diferenciales v1: sillón obligatorio con antisolapamiento, lista de espera con auto-relleno y trazabilidad total con mirada Ley 25.326.
