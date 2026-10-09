# Reglas de Negocio

Cada regla tiene código único para trazabilidad (formato `RN-{DOMINIO}-{NN}`; se referencian desde `06_funcionalidades.md`).

## Dominio: Agenda (RN-AG)

- **RN-AG-01**: Un sillón no puede tener dos turnos superpuestos; tampoco un profesional (doble exclusion, excluyendo `cancelado`/`reprogramado`). — Sin esto el MVP no tiene sentido (problema central, discovery §7).
- **RN-AG-02**: La duración del turno es variable por prestación/configuración del profesional, no fija global (p. ej. limpieza 30 min, endodoncia 90 min).
- **RN-AG-03**: Todo turno lleva `sillon_id` obligatorio desde día 1 (aunque la UI arranque simple).
- **RN-AG-04**: Los bloqueos (feriados, licencias, mantenimiento) ocupan sillón y/o profesional como si fueran turnos y bloquean huecos.
- **RN-AG-05**: El sobreturno es explícito (flag + motivo + quién lo autorizó) y también respeta RN-AG-01 salvo autorización `admin`/recepción con justificación auditada.
- **RN-AG-06**: Cancelación/reprogramación con antelación mínima configurable por tenant (default 12 h); fuera de término exige confirmación manual de recepción.
- **RN-AG-07**: La reserva pública exige nombre + DNI + teléfono válidos (E.164); el hueco se pre-reserva con expiración (default 15 min) hasta crear el turno.
- **RN-AG-08**: Confirmar/cancelar/reprogramar por token público o WA equivale a hacerlo por mostrador (mismo cambio de estado + auditoría).
- **RN-AG-09**: La lista de espera auto-rellena por orden de prioridad/antigüedad compatible con el hueco; la oferta por WA expira en N min (default 60) y pasa al siguiente.

## Dominio: Clínica (RN-CL)

- **RN-CL-01**: Odontograma con vocabulario cerrado de estados (base 18) y piezas FDI; cada hallazgo lleva fecha y autor.
- **RN-CL-02**: Solo el rol `odontologo` edita odontograma y plan clínico; recepción solo ve lo operativo.
- **RN-CL-03**: El presupuesto tiene total = suma de ítems y estados válidos (`borrador→enviado→aprobado/rechazado→cobrado`); la aprobación online (token) registra quién/cuándo/IP y vale como firma simple en v1.
- **RN-CL-04**: Sin consentimiento informado registrado no se cargan datos de salud (Ley 25.326).

## Dominio: Caja y cobros (RN-CJ)

- **RN-CJ-01**: Todo movimiento de caja deja traza (quién, cuándo, desde dónde: mostrador/portal/webhook) y es exportable. Prohibido el borrado físico; solo anulación con contra-asiento vinculado.
- **RN-CJ-02**: La seña puede configurarse como no reembolsable; ante cancelación fuera de término (RN-AG-06) la seña se retiene por defecto.
- **RN-CJ-03**: El link/seña de Mercado Pago se concilia por webhook (IPN); el turno/presupuesto cambia a `cobrado/señado` solo con webhook verificado, nunca por callback del frontend.
- **RN-CJ-04**: La cuenta corriente por paciente es la única fuente de deuda; el recupero genera movimientos vinculados, no edita saldos a mano.
- **RN-CJ-05**: Comprobante v1 es manual (recibo/factura manual registrada); la FE ARCA llega en fase 2 vía adapter sin cambiar el flujo de caja.

## Dominio: Seguridad y privacidad (RN-SEG)

- **RN-SEG-01**: Aislamiento por `tenant_id` en cada query de negocio; ningún usuario ve datos de otro consultorio.
- **RN-SEG-02**: Acceso a datos de salud por rol + consentimiento (Ley 25.326; diferencial declarado, ningún competidor la declara — discovery §7).
- **RN-SEG-03**: Auditoría de escrituras sensibles (turnos, caja, presupuestos, odontograma): quién/cuándo/qué/desde dónde, exportable.
- **RN-SEG-04**: Tokens públicos (`turno`, `presupuesto`, `pago`) son UUID únicos, con expiración y revocables; no exponen IDs internos.
- **RN-SEG-05**: Rate-limit + captcha en rutas públicas; firmas verificadas en webhooks (Meta y MP).
- **RN-SEG-06**: Borrado lógico en todas las tablas de negocio (`deleted_at` + `deleted_by`, restaurable por `admin`); prohibido el borrado físico salvo purga explícita y auditada. El flag `activo:bool` es on/off operativo, no borrado.

## Dominio: Excepciones globales

- **RN-G-01**: Toda integración externa (WA, MP, ARCA futuro) falla de forma degradada: el flujo core (reservar/atender/cobrar manual) nunca queda bloqueado por una caída externa; el job reintenta con backoff y alerta.
- **RN-G-02**: Precios siempre en ARS; español rioplatense en plantillas y portal.
- **RN-G-03**: Ningún dato de salud viaja en logs ni en mensajes WA más allá de lo operativo (día/hora/profesional); el detalle clínico vive en el portal con auth.
