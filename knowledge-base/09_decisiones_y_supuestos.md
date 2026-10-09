# Decisiones y Supuestos

## Decisiones documentadas

### DD-01 — Monolito modular (no microservicios)
**Decisión**: FastAPI monolítico con módulos agenda/clínica/caja/notificaciones + React SPA + Postgres + Redis en un Docker Compose.
**Contexto**: piloto chico (1–5 consultorios, <50 usuarios) y prioridad velocidad de entrega.
**Alternativas consideradas**: microservicios por dominio; serverless; schema-por-tenant.
**Justificación**: deploys simples, transacciones ACID para antisolapamiento y caja, un solo repo para iterar.
**Trade-offs aceptados**: escalado vertical en v1; RLS y multi-sede quedan como deuda documentada.

### DD-02 — Python FastAPI + SQLAlchemy + PostgreSQL + Redis
**Decisión**: stack backend cerrado del gate (Python 3.12, FastAPI, JWT, SQLAlchemy 2.0, Postgres 15+, Redis 7+, Docker).
**Contexto**: decisión del orquestador, no re-preguntada.
**Alternativas consideradas**: Node/Nest, Django monolítico.
**Justificación**: FastAPI da validación Pydantic + OpenAPI gratis (útil para API fase 2); SQLAlchemy 2.0 + Alembic cubren migraciones multi-tenant; Redis ya resuelve WA/colas sin Kafka.
**Trade-offs aceptados**: equipo debe conocer async SQLAlchemy y exclusion constraints de Postgres.

### DD-03 — React + TypeScript + Vite
**Decisión**: SPA React 18 + TS + Vite para app interna y portal público.
**Contexto**: decisión cerrada; portal debe ser mobile-first y SEO básico por consultorio.
**Alternativas consideradas**: Next.js SSR, plantillas server-side.
**Justificación**: una sola SPA con dos superficies (privada con JWT, pública sin auth) sale más rápido; SSR/SEO avanzado pasa a fase 2.
**Trade-offs aceptados**: SEO del portal limitado en v1.

### DD-04 — Mercado Pago en el MVP
**Decisión**: cobro online (link/seña) con Mercado Pago en v1, conciliado por webhook.
**Contexto**: gate final del discovery (2026-10-01): MP va en MVP.
**Alternativas consideradas**: solo efectivo/transferencia en v1.
**Justificación**: la seña online sostiene la antelación de cancelación y el recupero; MP es el medio local dominante.
**Trade-offs aceptados**: dependencia de com Âu MP + conciliar estados pendientes hasta IPN.

### DD-05 — ARCA en fase 2 con diseño preparado
**Decisión**: entidad `Comprobante` + adapter `Facturador(manual)` en v1; emisión electrónica ARCA en fase 2 sin cambiar caja.
**Contexto**: gate final: ARCA diseñada pero diferida.
**Alternativas consideradas**: ARCA en MVP; sin comprobante en v1.
**Justificación**: la FE frena el MVP (certificados, homologación, RI); el adapter evita conciliar en planillas y deja el camino abierto.
**Trade-offs aceptados**: conciliación manual hasta fase 2; puede frenar a clínicas RI (riesgo discovery §9).

### DD-06 — Sillón obligatorio + antisolapamiento desde día 1
**Decisión**: `sillon_id` NOT NULL en Turno + exclusion constraints por sillón y profesional.
**Contexto**: restricción discovery §9 y segmento 2–3 sillones.
**Alternativas consideradas**: sillón opcional con UI simple.
**Justificación**: el doble-booking por sillón es el problema central; postergarlo es deuda carísima.
**Trade-offs aceptados**: la UI de consultorios de 1 sillón carga un campo "obvio".

### DD-07 — Pricing por sillón en ARS
**Decisión**: precio publicado en ARS escalado por sillones (referencia: Dentally cobra por sillón; DentalSoft $30–60k, DentalSaaS $59–349k — discovery §A).
**Contexto**: oportunidad detectada (ningún AR combina todo en un precio).
**Alternativas consideradas**: por usuario, por turno, freemium.
**Justificación**: el sillón mide capacidad real del consultorio y alinea costo con valor (ocupación).
**Trade-offs aceptados**: validar elasticidad en piloto; cupo WA aparte por costo por mensaje.

## Supuestos inferidos

### SU-01 — El paciente prefiere el link antes que escribir por WA
**Supuesto**: la reserva en 4 pasos sustituye el mensaje manual.
**Origen**: discovery §9 (supuesto sin probar).
**Riesgo si es falso**: baja adopción del portal; la agenda se sigue cargando por teléfono.
**Cómo validar**: métrica M-06 (≥60% turnos por link/QR) en piloto; test A/B link vs botón WA.

### SU-02 — El consultorio mantiene disponibilidad y precios/OS actualizados
**Supuesto**: admin/recepción cargan horarios, bloqueos, aranceles y convenios.
**Origen**: discovery §9.
**Riesgo si es falso**: huecos falsos, cobros erróneos, desconfianza.
**Cómo validar**: onboarding guiado + alerta de "agenda sin configurar"; auditar huecos publicados vs reales semana 1.

### SU-03 — Validación OS online generalizable
**Supuesto**: se puede validar cobertura con todas las OS como hace DentalTec con 15+.
**Origen**: discovery §9 (solo DentalTec lo evidenció).
**Riesgo si es falso**: la cobertura v1 queda manual/tabla y el diferencial "OS+FE en un paso" se retrasa.
**Cómo validar**: demo con DentalTec como referencia; en v1 asumir tabla y medir tasa de débitos.

### SU-04 — Costo WA escalable dentro del plan
**Supuesto**: ~USD 0,026 por recordatorio (dato DentalSoft, discovery §8) cabe en el pricing por sillón con cupo.
**Origen**: ficha dentalsoft.md.
**Riesgo si es falso**: a escala, WA erosiona margen.
**Cómo validar**: cupo por plan + alerta 80%; medir mensajes/turno en piloto.

### SU-05 — Claims comerciales de vendors
**Supuesto**: cifras como "-82% ausencias" (DentalSoft), "45M citas" (Dentalink) son marketing sin auditoría.
**Origen**: fichas sources + discovery §C.
**Riesgo si es falso**: dimensionar metas irreales (M-02 usa −30% conservador).
**Cómo validar**: no usarlas como compromiso; medir línea base propia por consultorio.
