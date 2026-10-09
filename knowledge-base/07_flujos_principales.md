# Flujos Principales

Cada flujo va extremo a extremo con errores. Actores: P=paciente, R=recepción, O=odontólogo, S=sistema/jobs.

## Flujo 1: Reserva online 24/7 [MVP]

**Disparador**: P abre `/reservar/:slug` (link/QR). **Actor**: paciente.

**Pasos**:
1. Frontend público pide `GET /public/disponibilidad/:slug` (prestación → duración; filtros profesional/sillón).
2. API calcula huecos reales (turnos + bloqueos + duración variable; RN-AG-01/02/04).
3. P elige horario → `POST /public/reservar/:slug` (nombre+DNI+teléfono) → pre-reserva 15 min.
4. API crea Turno `reservado` + `token_publico`; encola WA de confirmación (Redis).
5. S envía WA con botones Confirmar/Cancelar/Reprogramar + link `/p/turno/:token`.

```
P → Portal → API → DB (turno reservado + token)
API → Redis → WA (confirmación) → P confirma → webhook → API → DB (confirmado)
```

**Casos de error**:
- Hueco tomado en el ínterin → 409 con huecos alternativos (RN-AG-07).
- Teléfono inválido → 422, no crea turno.
- WA caído → turno igual creado; reintento con backoff + alerta (RN-G-01).

## Flujo 2: Confirmación y recordatorios WhatsApp [MVP]

**Disparador**: jobs programados (T-24 h, T-2 h). **Actor**: sistema.

**Pasos**:
1. Worker Redis selecciona turnos `reservado` próximos sin confirmación.
2. Envía plantilla WA (rioplatense) con botones; registra Notificación.
3. P responde (Confirmar/Cancelar) → `POST /webhooks/whatsapp` (firma Meta) → cambia estado (RN-AG-08).
4. Si cancela dentro de antelación → libera hueco → dispara Flujo 4; si es fuera de término, deriva a R y aplica seña no reembolsable (RN-AG-06, RN-CJ-02).

**Casos de error**:
- Sin respuesta → a T-2 h reintenta; el no-show queda `ausente` y alimenta ausentismo + recupero.
- Webhook duplicado → idempotencia por `message_id`.

## Flujo 3: Atención + presupuesto + cobro Mercado Pago [MVP]

**Disparador**: P presente en consultorio. **Actores**: O, R, P.

**Pasos**:
1. R marca `presente`; O abre ficha y carga odontograma (RN-CL-01/02).
2. O arma presupuesto desde odontograma/nomenclador (cobertura OS calculada) → estado `enviado` + link `/p/presupuesto/:token` por WA.
3. P aprueba online (quién/cuándo/IP) → si hay seña, S genera link MP (`POST /cobros/mp-link`).
4. P paga → `POST /webhooks/mercadopago` verificado → MovimientoCaja + Turno/Presupuesto `cobrado/señado` (RN-CJ-03).
5. R cierra caja del día contra movimientos (RN-CJ-01); Comprobante manual registrado (RN-CJ-05).

```
O → API (presupuesto) → WA link → P aprueba → API (link MP) → MP → webhook → caja
```

**Casos de error**:
- Pago sin webhook (P cierra el browser) → el estado NO cambia hasta IPN; R ve "pendiente" y puede conciliar manual.
- Monto distinto (arancel desactualizado) → alerta de descuadre; nunca edita el movimiento, crea ajuste auditado.

## Flujo 4: Lista de espera con auto-relleno [MVP, diferencial]

**Disparador**: cancelación que libera hueco. **Actor**: sistema + R (supervisa).

**Pasos**:
1. Al cancelar, API busca ListaEspera `activa` compatible (prestación, profesional, preferencia) ordenada por prioridad/antigüedad.
2. S ofrece por WA al primero (`ofrecida`, expira 60 min) con link de aceptación.
3. Si acepta → crea Turno vinculado y marca lista `aceptada`; si vence/rechaza → pasa al siguiente (RN-AG-09).
4. R ve el log de ofrecimientos en la agenda.

**Casos de error**:
- Nadie acepta → hueco queda libre visible para reserva pública.
- Dos aceptaciones simultáneas → gana la primera (antisolapamiento RN-AG-01); la otra recibe alternativa.

## Flujo 5: Cierre de caja diario [MVP]

**Disparador**: fin del día. **Actor**: recepción/admin.

**Pasos**:
1. R abre cierre: S suma movimientos del día por medio (efectivo, MP, transferencia, OS).
2. Cuenta efectivo físico → si descuadra, registra ajuste (egreso/ingreso con motivo, auditado).
3. Admin aprueba cierre; exportación CSV; Comprobantes pendientes de FE marcados para fase 2.

**Casos de error**:
- Webhook MP tardío → movimiento entra al día siguiente con marca de conciliación; nunca se reabre un cierre aprobado (nuevo ajuste).
