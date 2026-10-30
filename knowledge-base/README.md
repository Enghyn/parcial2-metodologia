# Sistema Odontológico Multi-Sillón — Base de Conocimiento

Base de conocimiento canónica generada y optimizada para el proyecto académico de **Metodología de Desarrollo de Sistemas**. Define las especificaciones de arquitectura, modelo de datos, reglas de negocio y funcionalidades del sistema odontológico.

---

## Índice de Archivos

| Archivo | Contenido |
|---|---|
| [01_vision_y_objetivos.md](01_vision_y_objetivos.md) | Propósito del sistema, objetivos por actor, alcance del MVP académico y métricas de éxito. |
| [02_descripcion_general.md](02_descripcion_general.md) | Stack tecnológico, arquitectura del monolito modular y estructura de módulos de la API. |
| [03_actores_y_roles.md](03_actores_y_roles.md) | Actores (paciente, recepción, odontólogo, admin), matriz de permisos RBAC y superficies pública y privada. |
| [04_modelo_de_datos.md](04_modelo_de_datos.md) | Diagrama ERD, 8 entidades relacionales simplificadas, reglas de integridad y datos semilla iniciales. |
| [05_reglas_de_negocio.md](05_reglas_de_negocio.md) | Reglas codificadas (`RN-AG`, `RN-CL`, `RN-CJ`, `RN-SEG`, `RN-G`) con foco en antisolapamiento y trazabilidad. |
| [06_funcionalidades.md](06_funcionalidades.md) | Historias de usuario organizadas en 5 épicas clave con criterios de aceptación verificables. |
| [07_flujos_principales.md](07_flujos_principales.md) | Flujos E2E: reserva pública, atención clínica con odontograma, cobro/cierre de caja y cancelación. |
| [08_arquitectura_propuesta.md](08_arquitectura_propuesta.md) | Patrones de software, árbol de directorios del proyecto, seguridad JWT y variables de entorno. |
| [09_decisiones_y_supuestos.md](09_decisiones_y_supuestos.md) | Decisiones de diseño (`DD-01` a `DD-07`) y supuestos operativos del consultorio. |
| [10_preguntas_abiertas.md](10_preguntas_abiertas.md) | Registro de decisiones fundacionales cerradas y detalles menores de implementación. |

---

## Resumen Ejecutivo

Sistema de gestión para consultorio odontológico con **2 a 3 sillones físicos**, desarrollado sobre un monolito modular con **FastAPI + SQLAlchemy + PostgreSQL** en backend y una SPA en **React + Vite + TypeScript + Tailwind CSS** en frontend.

El sistema se enfoca en resolver los problemas esenciales del consultorio:
1. **Agenda con antisolapamiento estricto** que impide superposiciones entre sillones o profesionales.
2. **Reserva online autónoma** para pacientes sin necesidad de login.
3. **Ficha clínica con odontograma esquemático interactivo** basado en nomenclatura internacional FDI (piezas 11 a 48).
4. **Control y arqueo diario de caja** con trazabilidad de medios de pago.
5. **Comunicación ágil** mediante enlaces directos a WhatsApp (`wa.me/`).
