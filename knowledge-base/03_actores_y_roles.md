# Actores y Roles

## Actores del sistema

| Actor | Descripción | Cómo interactúa |
|---|---|---|
| Paciente | Persona que recibe atención; puede no tener cuenta en v1 | Portal público `/reservar/:slug` (reserva sin login: nombre+DNI+teléfono) + WhatsApp (confirma/cancela, aprueba presupuesto, paga link MP) |
| Secretaria / recepción | Opera agenda, cobra y atiende mostrador/teléfono | SPA autenticada: agenda día/semana por sillón y profesional, turnos, lista de espera, caja, reportes operativos |
| Odontólogo | Profesional clínico del consultorio | SPA autenticada: su agenda, ficha, odontograma, presupuestos, evolución y producción propia |
| Administrador / dueño | Gestiona el consultorio (tenant) | SPA autenticada: configuración (sillones, profesionales, OS, aranceles), caja, reportes, auditoría, exportación |
| Sistema / jobs (actor técnico) | Workers Redis + webhooks | Envía recordatorios WA, expira ofertas de lista de espera, concilia webhooks MP/WA sin intervención |
| (Fase 2) Círculo / federación | Validador institucional de OS | API/validación externa (modelo DentalTec); no es usuario del SaaS en v1 |

Segmento día 1: consultorio de 2–3 sillones (dato obligatorio desde el modelo). Multi-sede enterprise y app nativa quedan fuera de v1.

## RBAC — Matriz de permisos

Roles por consultorio (tenant): `admin`, `odontologo`, `recepcion`. El paciente NO es rol interno en v1 (actor público). Todo permiso se evalúa con `(tenant_id, rol, recurso)`.

| Rol → Recurso | Pacientes/Ficha | Odontograma | Turnos/Agenda | Lista de espera | Presupuestos | Caja/MP | OS/Nomenclador | Comprobantes (v1 manual) | Configuración | Reportes | Auditoría/Export |
|---|---|---|---|---|---|---|---|---|---|---|---|
| `admin` (dueño) | CRUD | CRUD | CRUD | CRUD | CRUD | CRUD + cierre | CRUD | CRUD | CRUD | ver todo | ver + exportar |
| `recepcion` (secretaria) | CRU (sin borrar; sin ver datos sensibles fuera de rol*) | ver (sin editar) | CRUD (crear/reprogramar/cancelar/sobreturno) | CRUD + ofrecer | crear/ver/cobrar (no cambia plan clínico) | cobrar + movimientos (no anular sin admin) | ver + aplicar cobertura | crear (manual) | ver (no editar) | ver operativos | ver (no exportar sensible) |
| `odontologo` | CRU (sus pacientes) | CRUD (sus pacientes) | ver + proponer (pide a recepción el sobreturno) | ver | CRUD (plan clínico) | ver (no cobra) | ver | ver | — | ver producción propia | — |
| público (sin auth) | crear-se (auto-reserva) | — | crear (reserva) / cancelar-reprogramar propia con token | anotarse | aprobar propia con token | pagar link | — | — | — | — | — |

\* Datos de salud con consentimiento y acceso por rol (Ley 25.326): la ficha/odontograma solo la edita el odontólogo; recepción ve lo mínimo operativo. Trazabilidad total: cada escritura guarda quién/cuándo/desde dónde.

## Rutas públicas

Sin autenticación (rate-limit + captcha + token por turno donde aplique):

- `GET /reservar/:slug` — portal del consultorio (reserva online 24/7, SEO).
- `GET /api/v1/public/disponibilidad/:slug` — huecos disponibles.
- `POST /api/v1/public/reservar/:slug` — crea turno (nombre + DNI + teléfono).
- `GET /p/turno/:token` — detalle de turno (confirmar / cancelar / reprogramar).
- `POST /api/v1/public/turnos/:token/confirmar|juar|cancelar|reprogramar`.
- `GET /p/presupuesto/:token` — ver y aprobar presupuesto online.
- `POST /api/v1/public/presupuestos/:token/aprobar`.
- `GET /p/pagar/:token` — link/seña Mercado Pago.
- `POST /api/v1/webhooks/whatsapp` — entrantes y estados WA (firma Meta).
- `POST /api/v1/webhooks/mercadopago` — IPN de cobros (firma MP).
- Todo lo demás (`/app/*`, `/api/v1/*` interno) exige JWT + `tenant_id`.
