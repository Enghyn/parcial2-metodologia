# Flujos Principales del Sistema

A continuación se describen los 4 flujos de trabajo extremo a extremo (E2E) que articulan las funcionalidades del sistema:

---

## Flujo 1: Reserva Online Pública y Comunicación (Paciente)

1. **Acceso al portal:** El paciente accede a `/reservar` desde cualquier navegador (móvil o PC).
2. **Selección de consulta:**
   - Elige la prestación deseada (ej. "Limpieza dental", duración estimada: 30 min).
   - Elige un profesional odontólogo específico o "Cualquiera disponible".
3. **Cálculo de huecos disponibles:**
   - El backend consulta turnos y bloqueos existentes para los 2 a 3 sillones físicos.
   - Devuelve las franjas horarias donde haya al menos un sillón y un profesional libres.
4. **Confirmación y carga de datos:**
   - El paciente ingresa Nombre, Apellido, DNI y Teléfono.
   - El sistema crea el turno en estado `reservado` y genera un `token_publico`.
5. **Comprobante y WhatsApp:**
   - Se muestra la pantalla de éxito con el resumen de la cita.
   - Se ofrece el botón "Enviar confirmación a WhatsApp", que abre `wa.me/` con el texto prearmado para el consultorio.

---

## Flujo 2: Operación Diaria y Atención Odontológica

1. **Inicio de jornada:** La recepcionista inicia sesión en `/app/login` con sus credenciales y accede a `/app/agenda`.
2. **Visualización de la agenda:**
   - Observa las 3 columnas correspondientes a Sillón 1, Sillón 2 y Sillón 3.
   - Verifica los turnos programados del día y sus estados.
3. **Llegada del paciente:**
   - El paciente se presenta en mostrador; recepción cambia el estado del turno a `presente`.
4. **Atención clínica y Odontograma:**
   - El odontólogo accede a la ficha del paciente desde `/app/odontograma/:pacienteId`.
   - Visualiza el esquema de 32 piezas dentales FDI.
   - Hace clic sobre la pieza intervenida (ej. pieza 16) y selecciona "obturación" con una nota de evolución.
   - Guarda los cambios. El turno pasa a estado `atendido`.

---

## Flujo 3: Cobro y Cierre Diario de Caja

1. **Recepción del pago:**
   - Finalizada la atención, el paciente pasa por recepción.
   - La secretaria abre el modal de cobro desde la agenda o desde `/app/caja`.
2. **Registro del movimiento:**
   - Ingresa el monto (ej. $15.000), selecciona el medio de pago (`efectivo`, `transferencia` o `tarjeta`) y concepto ("Cobro atención odontológica").
   - El sistema asocia el movimiento al turno y registra al usuario receptor.
3. **Cierre de caja:**
   - Al finalizar el turno de atención, el administrador o recepcionista ingresa a `/app/caja/resumen`.
   - El sistema totaliza los ingresos por medio de pago y emite el balance diario de caja.

---

## Flujo 4: Cancelación de Turno y Liberación de Agenda

1. **Disparo de la cancelación:**
   - El paciente cancela desde el enlace público `/p/turno/:token` o avisa por teléfono/WhatsApp y recepción cancela desde la agenda.
2. **Actualización de estado:**
   - El turno pasa a estado `cancelado` (con fecha y motivo opcional).
3. **Liberación inmediata:**
   - El backend excluye los turnos cancelados en la validación antisolapamiento (`RN-AG-01`).
   - El sillón y el profesional quedan disponibles de inmediato para nuevas reservas públicas o asignación manual.
