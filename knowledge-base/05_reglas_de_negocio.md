# Reglas de Negocio

Todas las reglas están codificadas bajo la nomenclatura `RN-{DOMINIO}-{NN}` para facilitar su trazabilidad en el código y en las suites de pruebas unitarias.

---

## Dominio: Agenda y Turnos (RN-AG)

- **RN-AG-01 (Antisolapamiento de Agenda):**
  * Un sillón no puede tener dos turnos activos superpuestos en el tiempo.
  * Un profesional odontólogo no puede tener dos turnos activos superpuestos en el tiempo (aunque estén asignados a distinto sillón).
  * **Implementación:** Se valida en la capa de servicios del backend en FastAPI antes de persistir cualquier reserva o modificación:
    $$\text{Conflicto si: } (\text{inicio} < \text{turno\_fin}) \land (\text{fin} > \text{turno\_inicio}) \land (\text{estado} \neq \text{'cancelado'})$$
  * Ante conflicto, el sistema rechaza la operación con código HTTP 409 (Conflict) indicando claramente si el conflicto es por disponibilidad de sillón o del profesional.

- **RN-AG-02 (Duración Variable):**
  * La duración del turno no es fija globalmente; depende de la prestación solicitada (ej. limpieza: 30 min, extracción o endodoncia: 60 min).
  * El horario de finalización (`fin`) se calcula automáticamente como $\text{inicio} + \text{duracion\_min}$.

- **RN-AG-03 (Asignación Física Obligatoria):**
  * Todo turno debe tener asignado de forma obligatoria un `sillon_id` y un `profesional_id`.

- **RN-AG-04 (Bloqueos de Agenda):**
  * Los bloqueos por mantenimiento de sillón, feriados o ausencias de profesionales impiden la reserva de turnos en dicho intervalo, tratándose como ocupación a efectos de la disponibilidad pública e interna.

- **RN-AG-05 (Estados del Turno):**
  * Los estados permitidos son: `reservado` $\rightarrow$ `confirmado` $\rightarrow$ `presente` $\rightarrow$ `atendido` (o `cancelado`).
  * Cancelar un turno libera de inmediato el sillón y el profesional para nuevas reservas.

- **RN-AG-06 (Validación de Reserva Pública):**
  * La reserva online autónoma no requiere registro de usuario pero exige obligatoriamente: Nombre completo, DNI y Teléfono válido para contacto.

---

## Dominio: Clínica y Odontograma (RN-CL)

- **RN-CL-01 (Nomenclatura FDI y Estados):**
  * El odontograma utiliza la norma internacional FDI para los 32 dientes permanentes numerados del 11 al 48:
    * Cuadrante 1 (Superior derecho): 11 al 18
    * Cuadrante 2 (Superior izquierdo): 21 al 28
    * Cuadrante 3 (Inferior izquierdo): 31 al 38
    * Cuadrante 4 (Inferior derecho): 41 al 48
  * Estados clínicos permitidos por pieza: `sano`, `caries`, `obturacion`, `corona`, `extraccion`, `tratamiento_conducto`.

- **RN-CL-02 (Permisos Clínicos):**
  * La edición de hallazgos del odontograma y ficha clínica está restringida al rol `odontologo` y supervisada por `admin`. Personal de recepción solo tiene lectura informativa.

---

## Dominio: Caja y Finanzas (RN-CJ)

- **RN-CJ-01 (Trazabilidad de Movimientos):**
  * Todo ingreso o egreso de dinero debe registrar obligatoriamente: fecha, monto ($>0$), medio de pago (`efectivo`, `transferencia`, `debito`, `credito`, `otro`), concepto y el usuario responsable que operó la transacción.

- **RN-CJ-02 (Inmutabilidad Contable):**
  * Queda prohibido el borrado físico (`DELETE`) de movimientos de caja. Errores de carga se subsanan registrando un movimiento de egreso o contra-asiento compensatorio con nota aclaratoria.

- **RN-CJ-03 (Señas de Turnos):**
  * El consultorio puede registrar señas anticipadas vinculadas al turno. Al atenderse el paciente y liquidar el total, la seña se deduce del saldo restante.

---

## Dominio: Seguridad y Auditoría (RN-SEG)

- **RN-SEG-01 (Protección de Rutas Privadas):**
  * Toda petición a la API interna (`/api/v1/turnos`, `/pacientes`, `/caja`, etc.) requiere cabecera `Authorization: Bearer <token_jwt>` válida.
  * Rutas públicas (`/api/v1/public/*`) no requieren token pero validan formato estricto de entrada vía schemas Pydantic con `extra='forbid'`.

- **RN-SEG-02 (Borrado Lógico):**
  * Las entidades principales de negocio (`Paciente`, `Turno`, `Profesional`, `Sillon`) no se eliminan físicamente de la base de datos; utilizan borrado lógico mediante la marca temporal `deleted_at`.

---

## Dominio: Comunicación e Integraciones (RN-G)

- **RN-G-01 (Notificaciones y Enlaces WhatsApp):**
  * Las notificaciones de confirmación y recordatorios de turnos se generan mediante enlaces directos Click-to-Chat de WhatsApp (`https://wa.me/<telefono>?text=<mensaje_url_encoded>`), permitiendo al operador o al paciente abrir el chat con un clic sin costos ni configuraciones de APIs comerciales externas.
  * El sistema simula en log de consola y en base de datos el envío de notificaciones automáticas para fines de demostración académica.
