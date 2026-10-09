# Funcionalidades

Organizadas por **épica** y luego por **historia de usuario** (`US-NNN`). Marca **[MVP]** vs **[FASE 2]**. Cada US cita sus reglas.

## Épica A: Agenda multi-sillón [MVP]

### US-001 — Ver agenda día/semana por sillón y profesional
**Como** secretaria **Quiero** ver la agenda del día/semana cruzando sillón × profesional **Para** evitar solapamientos y reubicar sobreturnos.
**Criterios de aceptación**:
- [ ] Vista día (default) y semana con columnas por sillón y filtro por profesional.
- [ ] Bloqueos visibles diferenciados; sobreturnos marcados.
- [ ] Carga <2 s con 3 sillones × 30 turnos/día.
**Reglas relacionadas**: RN-AG-01, RN-AG-03, RN-AG-04

### US-002 — Crear turno con duración variable y antisolapamiento
**Como** secretaria **Quiero** crear un turno eligiendo prestación (duración auto) + sillón + profesional **Para** no reservar de más ni de menos.
**Criterios de aceptación**:
- [ ] La duración se propone por prestación/profesional y es editable.
- [ ] Si hay solapamiento de sillón o profesional, rechazo con mensaje que indica el conflicto.
- [ ] Sobreturno solo con motivo + auditoría.
**Reglas relacionadas**: RN-AG-01, RN-AG-02, RN-AG-03, RN-AG-05, RN-SEG-03

### US-003 — Bloqueos de agenda
**Como** admin **Quiero** bloquear sillón/profesional por rango (feriado, licencia) **Para** que no se ofrezcan huecos falsos.
**Criterios de aceptación**:
- [ ] El bloqueo ocupa el hueco en disponibilidad pública e interna.
- [ ] Crear/borrar bloqueo queda auditado.
**Reglas relacionadas**: RN-AG-04

### US-004 — Reserva online 24/7 con link/QR [MVP]
**Como** paciente **Quiero** reservar en 4 pasos (prestación → profesional/sillón → horario → mis datos) **Para** no llamar ni escribir.
**Criterios de aceptación**:
- [ ] Portal `/reservar/:slug` mobile-first, sin login (nombre+DNI+teléfono).
- [ ] Pre-reserva del hueco 15 min; confirmación inmediata + token por WA/SMS.
- [ ] Rate-limit + captcha; solo huecos reales (descuenta bloqueos y turnos).
**Reglas relacionadas**: RN-AG-07, RN-SEG-04, RN-SEG-05

### US-005 — Confirmar / cancelar / reprogramar (autónomo + WA) [MVP]
**Como** paciente **Quiero** confirmar, cancelar o reprogramar desde el link o por WhatsApp **Para** liberar el horario a tiempo.
**Criterios de aceptación**:
- [ ] Botones con token único; reprogramación propone huecos equivalentes.
- [ ] Respeta antelación configurable; fuera de término deriva a recepción.
- [ ] Cada cambio dispara RN-AG-09 (auto-relleno) si libera hueco.
**Reglas relacionadas**: RN-AG-06, RN-AG-08, RN-AG-09, RN-CJ-02

## Épica B: Notificaciones y lista de espera [MVP]

### US-010 — Recordatorios automáticos WhatsApp
**Como** sistema **Quiero** enviar recordatorio 24 h y 2 h antes con botones Confirmar/Cancelar **Para** bajar el ausentismo.
**Criterios de aceptación**:
- [ ] Plantillas aprobadas Meta en rioplatense; estados (enviado/entregado/leído) visibles.
- [ ] Respuesta por WA cambia el estado del turno (RN-AG-08).
- [ ] Cupo por plan con alerta al 80% (costo ~USD 0,026/mensaje, discovery §8).
**Reglas relacionadas**: RN-AG-08, RN-G-01, RN-G-03

### US-011 — Lista de espera con auto-relleno
**Como** secretaria **Quiero** que al cancelarse un turno el sistema ofrezca el hueco por WA al primero compatible **Para** subir ocupación sin llamar uno por uno.
**Criterios de aceptación**:
- [ ] Orden por compatibilidad + antigüedad; oferta con expiración (default 60 min).
- [ ] Si vence/rechaza, pasa al siguiente automáticamente; si acepta, crea el turno.
- [ ] Log visible de ofrecimientos (diferencial: ningún AR lo evidencia, discovery §C).
**Reglas relacionadas**: RN-AG-09

## Épica C: Clínica y presupuestos [MVP]

### US-020 — Ficha + odontograma en la visita
**Como** odontólogo **Quiero** cargar hallazgos por pieza (18 estados) y evolución **Para** que recepción cobre sin re-cargar datos.
**Criterios de aceptación**:
- [ ] Odontograma SVG adulto/infantil, piezas FDI, con fecha y autor por hallazgo.
- [ ] Solo `odontologo` edita; recepción ve resumen operativo.
**Reglas relacionadas**: RN-CL-01, RN-CL-02, RN-SEG-02

### US-021 — Presupuesto con aprobación online
**Como** odontólogo **Quiero** armar el presupuesto desde el odontograma/nomenclador **Para** que el paciente lo apruebe en 1 click.
**Criterios de aceptación**:
- [ ] Ítems con precio, cantidad y cobertura OS; total automático; `valido_hasta`.
- [ ] Link con token: ver/aprobar/rechazar; aprobación registra quién/cuándo/IP.
- [ ] Al aprobar con seña, genera link MP automáticamente.
**Reglas relacionadas**: RN-CL-03, RN-CJ-03

## Épica D: Caja, MP y OS [MVP]

### US-030 — Caja con trazabilidad + cierre diario
**Como** secretaria **Quiero** registrar ingresos/egresos y cerrar caja del día **Para** conciliar sin planillas.
**Criterios de aceptación**:
- [ ] Medios: efectivo, MP link/terminal, transferencia, OS; sin borrado (solo anulación).
- [ ] Cierre diario con descuadre visible; exportación CSV.
**Reglas relacionadas**: RN-CJ-01

### US-031 — Cobro online Mercado Pago (link/seña)
**Como** paciente **Quiero** pagar la seña o el tratamiento con un link **Para** asegurar mi turno.
**Criterios de aceptación**:
- [ ] Link por turno/presupuesto; webhook IPN verificado cambia estado a señado/cobrado.
- [ ] Seña no reembolsable configurable; devolución solo con rol `admin`.
**Reglas relacionadas**: RN-CJ-02, RN-CJ-03

### US-032 — Cuenta corriente y recupero de deudas
**Como** admin **Quiero** ver quién debe y lanzar recupero **Para** cobrar lo pendiente.
**Criterios de aceptación**:
- [ ] Saldo por paciente derivado de movimientos; listado de morosos con antigüedad.
- [ ] Acción de recupero (WA + link MP) auditada.
**Reglas relacionadas**: RN-CJ-04

### US-033 — Obras sociales con nomenclador
**Como** secretaria **Quiero** aplicar cobertura (código → arancel → copago) **Para** cobrar correcto al paciente y a la OS.
**Criterios de aceptación**:
- [ ] Catálogo nacional + convenios por tenant; buscador por código/práctica.
- [ ] Copago calculado automático en turno/presupuesto. v1 validación manual/tabla (online real-time es supuesto, discovery §9).
**Reglas relacionadas**: RN-CJ-05

### US-034 — Comprobante manual ARCA-preparado [MVP diseño / FASE 2 emisión]
**Como** admin **Quiero** registrar el comprobante (recibo/factura manual) **Para** conciliar hasta que llegue la FE.
**Criterios de aceptación**:
- [ ] Entidad `Comprobante` + adapter `Facturador(manual)`; el cambio a `arca` no toca caja.
- [ ] Conciliación manual visible (pendiente de FE) como mitigación del riesgo fiscal.
**Reglas relacionadas**: RN-CJ-05

## Épica E: Roles, auditoría y reportes [MVP]

### US-040 — Roles/permisos + auditoría + exportación
**Como** admin **Quiero** gestionar usuarios/roles y ver quién hizo qué **Para** dar confianza (Ley 25.326).
**Criterios de aceptación**:
- [ ] Matriz de `03_actores_y_roles.md` enforced en API y UI; auditoría exportable.
- [ ] Exportación CSV de turnos/caja/pacientes (con resguardo de datos sensibles).
**Reglas relacionadas**: RN-SEG-01, RN-SEG-02, RN-SEG-03

### US-041 — Reportes ocupación / facturación / ausentismo
**Como** dueño **Quiero** ver ocupación por sillón, facturación por medio y ausentismo **Para** decidir precios y horarios.
**Criterios de aceptación**:
- [ ] 3 reportes con rango de fechas y comparativa semanal; datos exportables.
**Reglas relacionadas**: RN-CJ-01

## Épica F: Post-MVP [FASE 2]

- **US-050** Periodontograma avanzado + fichas de especialidad (orto/implanto/prótesis). **[FASE 2]**
- **US-051** Imágenes con visor + segunda opinión por IA. **[FASE 2]**
- **US-052** Campañas y recupero automatizado de inactivos. **[FASE 2]**
- **US-053** API pública + Google Calendar bidireccional. **[FASE 2]**
- **US-054** Multi-sucursal enterprise. **[FASE 2]**
- **US-055** App móvil nativa. **[FASE 2]**
- **US-056** Recepcionista virtual IA 24 h (evolución de US-010). **[FASE 2]**
- **US-057** Facturación electrónica ARCA vía adapter (`Facturador(arca)`) + validación OS online. **[FASE 2, primera candidata post-MVP — a priorizar, ver `10_preguntas_abiertas.md`]**
