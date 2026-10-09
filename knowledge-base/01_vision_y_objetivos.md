# Visión y Objetivos

## Propósito del sistema

**Eliminar la coordinación manual de los consultorios odontológicos argentinos (WhatsApp/papel y sistemas parciales) con un SaaS multi-tenant que unifica agenda multi-sillón, clínica, cobros y obras sociales en un solo precio publicado.**

Los consultorios y clínicas AR coordinan turnos por WhatsApp/papel o con sistemas parciales (agenda separada de facturación y obras sociales). Eso genera dobles reservas por sillón, ausentismo sin recupero (30–40% declarado por vendors), presupuestos que no se cierran ni se cobran, y conciliación manual entre caja, Mercado Pago, obras sociales y facturación. Ningún competidor local combina agenda multi-sillón + odontograma + OS/nomenclador + ARCA + Mercado Pago + WhatsApp automático en un solo precio publicado (discovery §§1, 4, C). Este sistema ocupa ese vacío, empezando por el segmento día 1: consultorio de 2–3 sillones.

## Objetivos por actor

| Actor | Objetivo principal | Objetivos secundarios |
|---|---|---|
| Paciente | Reservar/confirmar/cancelar sin llamar, 24/7 | Pagar seña online; aprobar presupuestos online; recibir recordatorios |
| Secretaria / recepción | Operar la agenda del día sin solapamientos ni planillas | Confirmar turnos, cobrar, gestionar lista de espera y ausentes |
| Odontólogo | Registrar ficha + odontograma + presupuesto en la misma visita | Ver su agenda y su producción |
| Administrador / dueño | Cerrar caja y medir el negocio sin conciliación manual | Configurar sillones/OS/aranceles; ver ocupación, facturación, ausentismo; exportar |

## Alcance v1.0

- Agenda multi-profesional y multi-sillón con duración variable por prestación, bloqueos, sobreturnos y antisolapamiento (sillón + profesional).
- Reserva online 24/7 con link/QR por consultorio, sin login obligatorio en v1 (nombre + DNI + teléfono).
- Confirmación / cancelación / reprogramación autónoma por el paciente + recordatorios automáticos por WhatsApp Business API.
- Lista de espera con auto-relleno ante cancelaciones.
- Odontograma + ficha clínica + presupuestos con aprobación online.
- Caja + cobro online Mercado Pago (link/seña) + cuenta corriente + recupero de deudas.
- Obras sociales con nomenclador y copagos.
- Roles/permisos + auditoría + exportación de datos.
- Reportes de ocupación, facturación y ausentismo.
- ARCA: diseño preparado (entidad `Comprobante` + adapter `Facturador` con implementación `Manual` en v1), implementación electrónica en fase 2.

## Fuera de alcance

- Periodontograma avanzado y fichas de especialidad (orto/implanto/prótesis).
- Imágenes con visor y segunda opinión por IA.
- Campañas y recupero automatizado de inactivos (más allá de lista de espera + recupero de deudas v1).
- API pública y sincronización bidireccional con Google Calendar.
- Multi-sucursal enterprise (multi-sede como red; v1 es multi-tenant de consultorios independientes).
- App móvil nativa; recepcionista virtual IA 24h.
- Facturación electrónica ARCA automática (fase 2); validación online de OS en tiempo real tipo DentalTec (supuesto, no MVP).
- Rol Círculo/federación (liquidación institucional).

## Métricas de éxito

| # | Métrica | Meta piloto (1–5 consultorios) | Fuente |
|---|---|---|---|
| M-01 | Dobles reservas por sillón | 0 en 3 meses (antisolapamiento efectivo) | Auditoría + reportes |
| M-02 | Ausentismo (no-show sin aviso) | −30% vs línea base del consultorio | Reporte ausentismo |
| M-03 | Huecos cancelados rellenados vía lista de espera | ≥40% de cancelaciones reubicadas | Log lista de espera |
| M-04 | Presupuestos aprobados online | ≥50% de presupuestos emitidos se aprueban/cobran en 7 días | Estado presupuesto |
| M-05 | Tiempo de cierre de caja diario | <15 min sin planillas externas | Operación recepción |
| M-06 | Reserva online autónoma | ≥60% de turnos nuevos entran por link/QR (no por teléfono) | Origen del turno |
| M-07 | Disponibilidad SaaS piloto | ≥99% mensual | Monitoreo |
