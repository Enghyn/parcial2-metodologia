# Discovery — Sistema odontológico con turnos/agenda (Argentina)

**Fecha**: 2026-10-01
**Fuentes investigadas**: 23 sistemas verificados (8 Argentina + 6 LATAM + 9 internacionales). Fecha de consulta de todas las fuentes: 2026-10-01.
**Notas por competidor**: `sources/` (5 prioritarios para demo).
**Decisiones del gate final (2026-10-01)**: resumen confirmado por el usuario; cobro online (Mercado Pago link/seña) va en el MVP; facturación ARCA se diseña preparada pero se implementa en fase 2; segmento día 1 recomendado: consultorio 2–3 sillones (a confirmar en KB).

## 1. Problema que resuelve

Los consultorios y clínicas odontológicas argentinas coordinan turnos por WhatsApp/papel o con sistemas parciales: agenda por un lado, facturación y obras sociales por otro. Eso genera dobles reservas por sillón, ausentismo sin recupero (30–40% declarado por vendors), presupuestos que no se cierran ni se cobran, y conciliación manual entre caja, Mercado Pago, obras sociales y facturación. Ningún sistema local combina agenda multi-sillón + odontograma + obras sociales/nomenclador + ARCA + Mercado Pago + WhatsApp automático en un solo precio publicado (ver §4 y tabla comparativa).

## 2. Usuarios / roles

- **Paciente**: reserva online 24/7 sin llamar, confirma/cancela por WhatsApp, paga seña online, aprueba presupuestos.
- **Secretaria/recepción**: ve agenda día/semana por sillón y profesional, confirma turnos, cobra, gestiona lista de espera y ausentes.
- **Odontólogo**: registra ficha, odontograma, planes y evolución; ve su agenda y producción.
- **Administrador/dueño**: configura sillones, profesionales, OS y aranceles; mira ocupación, facturación y ausentismo; exporta datos.
- **(Fase 2) Círculo/federación**: valida prácticas y liquida (modelo DentalTec, no MVP).

## 3. Casos de uso

1. Como paciente, quiero reservar un turno online en 4 pasos para no llamar ni escribir por WhatsApp.
2. Como secretaria, quiero ver la agenda del día por sillón y profesional para evitar solapamientos y reubicar sobreturnos.
3. Como paciente, quiero confirmar o cancelar por WhatsApp para liberar el horario a tiempo.
4. Como odontólogo, quiero cargar odontograma y presupuesto en la misma visita para que recepción lo cobre sin re-cargar datos.
5. Como administrador, quiero cobrar con Mercado Pago (link/seña) y conciliar con obras sociales para cerrar caja sin planillas.
6. Como administrador, quiero recuperar ausentes e inactivos automáticamente para subir ocupación.

## 4. Competidores / soluciones existentes

Ver **Sección A (tabla comparativa de 17)** y **Sección B (matriz ponderada)** al final de este documento. Resumen:
directos AR — DentalSaaS (lo más completo: OS+nomenclador+auditoría), DentalSoft (mejor captación web+SEO+precio), DoctorYa (ARCA+OS barato), DentalTec (validación OS real-time institucional), Odonthia (freemium+IA); referencia LATAM — Doctocliq (USD 19–49, mejor costo/función), Dentalink (líder multicentro, a cotizar); UX internacional — Curve, tab32, Dentally. Notas de los 5 prioritarios: `sources/`.

## 5. Funcionalidades necesarias (MVP)

Agenda multi-profesional y **multi-sillón** con duración variable, bloqueos, sobreturnos y antisolapamiento; reserva online 24/7 con link/QR; confirmación/cancelación/reprogramación (paciente autónomo + WhatsApp); recordatorios automáticos WhatsApp; **lista de espera que auto-rellena**; odontograma + ficha + presupuestos con aprobación online; caja + **cobro online Mercado Pago (link/seña)** + cuenta corriente y recupero de deudas; gestión de obras sociales con nomenclador; reportes de ocupación, facturación y ausentismo; roles/permisos + auditoría + exportación. Facturación electrónica ARCA: **diseño preparado (entidad Comprobante + adapter Facturador), implementación en fase 2** — decisión del gate, ver §10.

## 6. Funcionalidades opcionales (post-MVP)

Periodontograma avanzado; fichas de ortodoncia/implanto/prótesis; imágenes con visor y segunda opinión por IA; campañas y recupero automatizado de inactivos; API pública + sincronización Google Calendar bidireccional; multi-sucursal enterprise; app móvil nativa; recepcionista virtual IA 24h.

## 7. Reglas de negocio

- Un sillón no puede tener dos turnos superpuestos; un profesional tampoco.
- Duración del turno según prestación (variable por configuración, no fija global).
- Cancelación/reprogramación con antelación mínima configurable; la seña puede ser no reembolsable.
- Todo movimiento de caja deja traza (quién, cuándo, desde dónde) y es exportable.
- Los datos de salud requieren consentimiento y control de acceso por rol (Ley 25.326 — ningún competidor la declara; es diferencial).

## 8. Integraciones

MVP: WhatsApp Business API (recordatorios + confirmación), Mercado Pago (link/seña), sitio web/portal propio con SEO. Fase 2: ARCA (factura electrónica), Google Calendar, API pública. Cada integración es una dependencia con costo y riesgo (ej. WhatsApp cobra ~USD 0,026 por recordatorio según evidencia DentalSoft) — cotizar antes de prometer volumen incluido.

## 9. Restricciones

SaaS en la nube, multi-dispositivo (el paciente reserva desde el celular); español rioplatense; precios en ARS publicados; sin servidores locales; modelo de datos con sillón desde el día 1 aunque la UI arranque simple.

## 10. Riesgos

- **Supuesto sin probar**: que el paciente prefiera el link de reserva antes que escribir por WhatsApp por costumbre — no validado con usuarios reales.
- **Supuesto sin probar**: que el consultorio mantenga disponibilidad y precios/OS actualizados; si no, el sistema muestra huecos falsos.
- **Riesgo fiscal**: diferir ARCA alivia el MVP pero obliga a conciliar manual hasta fase 2 y puede frenar a clínicas RI — mitigado con entidad Comprobante + adapter desde día 1.
- **Riesgo costo WhatsApp**: el envío automático escala con costo por mensaje — definir cupo por plan.
- **Riesgo obras sociales**: solo DentalTec evidenció validación online; asumir validación automática con todas las OS es supuesto, no hecho.

## 11. Preguntas abiertas

- ¿Segmento día 1: independiente 1 sillón, consultorio 2–3 sillones (recomendado) o clínica multi-sede?
- ¿ARCA en fase 2 con qué prioridad exacta (primera feature post-MVP o después de campañas)?
- ¿Login de paciente o alcanza nombre + DNI + teléfono por turno?

---

## Sección A. Tabla comparativa (17 sistemas, relevancia AR descendente)

| # | Sistema (origen) | Odonto real | Agenda / sillón | Online + WA | Odontograma / Perio | OS AR + ARCA | Precio 2026-10-01 | Adopción |
|---|---|---|---|---|---|---|---|---|
| 1 | DentalSoft (AR) | Sí + web | Sí, sobreturnos c/antisolapamiento, GCal | Sí 4 pasos / auto en Pro | Sí 18 estados / perio No evid. | Sí OS / ARCA No evid. | Gratis 6m, $30k, $60k | +300 clínicas (vendor) |
| 2 | DentalSaaS (AR) | Sí total | Sí, detección solapamiento comprobada | Portal / WA auto + IA add-on | Sí / Sí SVG | Sí OS+nomenclador / ARCA No evid. | $59k / $149k / $349k | Empresa 25 años |
| 3 | DoctorYa (AR) | Parcial + odontograma | Sí simultáneos, duración x especialidad | Sí / WA auto CONFIRMAR | Sí / perio No | Sí copagos / Sí ARCA | $9k / $25k / $90k* | Testimonios |
| 4 | DentalTec (AR) | Sí institucional | Integrada + WA / detalle No evid. | Confirmación WA | Sí básico | Sí 15+ OS real-time / Sí ARCA | No publicado | 2.000+ prof., 30+ instit. |
| 5 | Odonthia (AR) | Sí | No evidenciado | Kit marca / WA en pagos | Sí / perio No evid. | No evidenciado | $0 / $20,9k / $46,9k | s/d |
| 6 | Docturno (AR) | No (salud gral) | Sí, sobreturnos comprobado | Sí 24/7 + bot WA (extra) | No evidenciado | Parcial / Sí AFIP + MP | $20–30k +IVA | 22,1M turnos |
| 7 | Doctocliq (PE) | Sí | Multi-doctor/sede, GCal | Sí / WA+SMS | Sí FDI/ADA + perio | FE PE/MX/CO | Gratis, USD 19/29/49 | +3.500 doctores |
| 8 | Dentalink (CL) | Sí + IA | Sí sillones vista global, sobreagenda | Sí / WA + IA 24/7 | Sí + perio + orto | Convenios gen. / AR No | Cotización | 15k clientes, 45M citas |
| 9 | SOMOSDENTO (AR) | Sí | Multi-prof. | Portal URL propia | Sí | ARCA A/B/C (claim) | No publicado | Testimonios |
| 10 | Dentiqa (LATAM) | Sí + CRM/IA | No evidenciado detalle | Chatbot IA WA | Sí + perio | No evidenciado | USD 89 / 149 | s/d |
| 11 | AgendaPro (CL) | No | Genérica multisede | Sí QR/FB/Google + WA | No evidenciado | No | $13,9k–$314,9k | 20k negocios |
| 12 | Doctoralia (EU→MX/BR) | No (marketplace) | Multi-especialista | Sí + lista espera inteligente | No evidenciado | MX CFDI / AR No | MX $1.350–2.370 | 29k especialistas MX |
| 13 | tab32 (USA) | Sí cloud | Sí + ASAP/waitlist | AutoRemind 2-vías | Sí + perio + IA | No (USA) | USD 125→225, trial 14d | 1.000+ prácticas |
| 14 | Open Dental (USA) | Sí open-source | Sí multisede/sillón + ASAP | Web Sched + SMS $0,04 | Sí 3D + perio | No | USD 199→149 | Capterra 4,6 |
| 15 | Curve (USA) | Sí cloud | Sí + SmartFill | Sí 24/7 + text-to-pay | Sí + perio + IA | No | Cotización | 80k+ profesionales |
| 16 | Dentally (UK) | Sí cloud | Chair-utilisation, multisite | Portal (no Starter) | Chart + Vision RX | UK NHS / AR No | £125–510 x sillones | 50k+ usuarios |
| 17 | CareStack (USA) | Sí cloud Azure | Sí multisede + kiosk | Sí portal + 2-way | Sí + perio + eRx | No | Cotización | 2.000+ dentistas |

*DoctorYa tercer plan rotulado "Argenti $90.000" textual. Descartados con evidencia: Odontotech (feria), Siro (CRO India), OdontoSystem (operadora BR), TurnosYa (sin marca activa).*

## Sección B. Matriz de puntuación (turnos 25% · clínica 20% · integraciones 15% · admin 15% · paciente 10% · seguridad 10% · precio 5%)

| Sistema | Turnos | Clínica | Integ. | Admin | Pac. | Seg. | Precio | Total |
|---|---|---|---|---|---|---|---|---|
| DentalSaaS AR | 4 | 5 | 3 | 4 | 4 | 4 | 3 | **4,00** |
| Dentalink CL | 5 | 5 | 3 | 4 | 4 | 3 | 1 | **4,05** |
| Curve USA | 5 | 4 | 3 | 4 | 5 | 4 | 1 | **4,05** |
| DentalSoft AR | 4 | 4 | 3 | 4 | 5 | 3 | 5 | **3,90** |
| tab32 USA | 4 | 4 | 4 | 3 | 4 | 5 | 3 | **3,90** |
| Doctocliq PE | 4 | 4 | 3 | 3 | 4 | 3 | 4 | **3,60** |
| Open Dental USA | 3 | 4 | 5 | 3 | 2 | 4 | 4 | **3,55** |
| DoctorYa AR | 3 | 3 | 2 | 4 | 3 | 2 | 5 | **3,00** |
| DentalTec AR | 2 | 2 | 2 | 5 | 2 | 4 | 1 | **2,60** |

## Sección C. Análisis competitivo

**Estándar (si falta, fuera):** agenda día/semana/mes por profesional, reserva online, recordatorio WA/email, confirmación/cancelación, odontograma, ficha + presupuestos, caja básica, roles. **Diferenciadores reales comprobados:** antisolapamiento (DentalSaaS, DentalSoft), vista por sillón (Dentalink, Simples), lista de espera auto-relleno (Curve, Doctoralia, tab32 — ningún AR la evidencia), verificación OS real-time (solo DentalTec), liquidación + laboratorio + auditoría (solo DentalSaaS), IA agéndica/transcripcional (Dentalink, Doctocliq, Odonthia), precio ARS publicado (DentalSoft, DoctorYa, Odonthia). **Vacíos AR:** nadie combina OS+nomenclador+ARCA+MP+WA en un precio; reprogramación autónoma casi inexistente; periodonto/planes multifase/firma en 2–3; exportación/auditoría/Ley 25.326 casi nulas; WA auto con costo extra; ARCA y gestión OS en productos distintos. **Oportunidades:** lista de espera por WA, verificador OS + FE en un paso, link/seña MP + recupero, presupuesto aprobable online en 1 click, web/portal incluido, confianza (auditoría + exportación + consentimiento), pricing por sillón en ARS.

## Sección D. Recomendación

**5 demos:** DentalSaaS, DentalSoft, Dentalink, Doctocliq, DentalTec. **3 UX:** Curve (Sidekick + SmartFill), tab32 (pricing + trial + migración), Dentally (precio por sillón). **MVP:** imprescindibles del §5; diferenciadores v1 (lista de espera WA, OS+FE en un paso a futuro, MP link/seña, presupuesto online, web incluida); postergados del §6.
