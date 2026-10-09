# Preguntas Abiertas

## Inconsistencias detectadas

Ninguna contradicción dura entre discovery.md, las 5 fichas y el gate; solo puntos a cerrar antes de codificar.

## Preguntas abiertas (priorizadas)

| Prioridad | Pregunta | Bloquea | Decisor |
|---|---|---|---|
| Alta | ¿Login de paciente o alcanza nombre + DNI + teléfono por turno? (v1 propone sin login + token; login pasaría a fase 2) | Sprint 1 (modelo Paciente + rutas públicas) | Product Owner |
| Alta | ¿Prioridad exacta de ARCA post-MVP: primera feature fase 2 o después de campañas/API? (afecta a clínicas RI del piloto) | Plan fase 2 / captación RI | Product Owner |
| Alta | ¿Segmento día 1 cerrado en consultorio 2–3 sillones? (recomendado; UI y pricing por sillón lo asumen) | Sprint 1 (seed + UI agenda) | Product Owner |
| Media | ¿Validación de OS online en v1 (tabla manual) o integración real-time con alguna OS? (solo DentalTec la evidenció) | Sprint 2 (módulo OS) | Equipo + consultorios piloto |
| Media | ¿Costo de WhatsApp a escala: cupo incluido por plan y precio del excedente? (~USD 0,026/mensaje) | Pricing / Sprint 2 (jobs WA) | Admin/negocio |
| Media | ¿Seña no reembolsable por default o configurable por prestación? (RN-CJ-02 la deja configurable) | Sprint 2 (caja/MP) | Product Owner |
| Baja | ¿Consentimiento digital con qué validez (token+IP vs firma manuscrita)? (v1: token+IP como firma simple) | Antes de operar datos reales | Legal / Product Owner |
| Baja | ¿Exportación con qué formato y resguardo (CSV + enmascarado de PHI)? | Sprint 3 (auditoría/export) | Tech Lead |
| Baja | ¿Multi-sucursal como tenant único con sedes o tenants separados? (v1: tenants separados) | Fase 2 | Product Owner |

Supuestos dudosos derivados a este archivo (detalle en `09_decisiones_y_supuestos.md` SU-01–SU-05): preferencia link vs WA manual; consultorio mantiene disponibilidad; validación OS generalizable; costo WA a escala; claims de vendors sin auditoría.
