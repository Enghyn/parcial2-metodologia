# Funcionalidades del Sistema

Organizadas por épicas e historias de usuario (`US-NNN`), con criterios de aceptación verificables mediante tests.

---

## Épica 1: Agenda Multi-Sillón y Antisolapamiento

### US-001 — Calendario multi-sillón día/semana
* **Como** recepcionista u odontólogo
* **Quiero** visualizar la agenda distribuida en columnas por sillón y filtrar por profesional
* **Para** coordinar los turnos del día sin confusiones de espacios físicos.
* **Criterios de Aceptación:**
  - [ ] Vista diaria con columnas para Sillón 1, Sillón 2 y Sillón 3.
  - [ ] Cada bloque de turno muestra: horario, paciente, profesional, prestación y estado.
  - [ ] Los bloques de mantenimiento o feriados aparecen claramente diferenciados.

### US-002 — Alta de turno con validación de antisolapamiento
* **Como** recepcionista
* **Quiero** crear un nuevo turno asignando prestación, profesional, sillón y horario
* **Para** agendar la atención garantizando que no existan conflictos de horarios.
* **Criterios de Aceptación:**
  - [ ] La duración se sugiere automáticamente según la prestación seleccionada.
  - [ ] Si el sillón elegido ya está ocupado en ese rango, el sistema impide la reserva e informa el conflicto (RN-AG-01).
  - [ ] Si el profesional elegido ya tiene otro turno asignado en ese rango, el sistema impide la reserva e informa el conflicto (RN-AG-01).
  - [ ] La reserva exitosa persiste el turno y genera su `token_publico`.

### US-003 — Bloqueos de disponibilidad
* **Como** administrador
* **Quiero** bloquear franjas horarias de un sillón o de un profesional
* **Para** registrar feriados, licencias médicas o mantenimiento de equipamiento.
* **Criterios de Aceptación:**
  - [ ] El bloqueo impide asignar turnos en esa franja horaria.
  - [ ] Se puede eliminar el bloqueo para restablecer la disponibilidad.

---

## Épica 2: Reserva Pública Online y Comunicación

### US-004 — Reserva online sin login (Portal Paciente)
* **Como** paciente
* **Quiero** ingresar al portal público (`/reservar`) y agendar mi turno en pasos simples
* **Para** solicitar atención odontológica las 24 horas sin necesidad de llamar por teléfono.
* **Criterios de Aceptación:**
  - [ ] Paso 1: Selección de prestación médica.
  - [ ] Paso 2: Selección de profesional u opción "Cualquiera disponible".
  - [ ] Paso 3: Selección de fecha y hora entre los huecos disponibles calculados en tiempo real.
  - [ ] Paso 4: Carga de datos del paciente (Nombre, DNI, Teléfono).
  - [ ] Al finalizar, se crea el turno en estado `reservado` y se muestra la pantalla de confirmación.

### US-005 — Consulta de turno y enlace a WhatsApp
* **Como** paciente o recepcionista
* **Quiero** acceder a la vista del turno (`/p/turno/:token`) con enlace directo a WhatsApp
* **Para** confirmar la asistencia o comunicarse con el consultorio en un clic.
* **Criterios de Aceptación:**
  - [ ] La vista pública muestra los datos del turno sin exponer IDs internos.
  - [ ] Incluye botón "Contactar por WhatsApp" que genera el enlace `https://wa.me/<telefono>?text=...` con mensaje preformateado.
  - [ ] Permite al paciente cancelar su turno de manera autónoma, liberando el hueco en la agenda.

---

## Épica 3: Ficha Clínica y Odontograma Interactivo

### US-006 — Gestión de pacientes
* **Como** recepcionista u odontólogo
* **Quiero** buscar pacientes por DNI o apellido y consultar sus datos de contacto
* **Para** mantener actualizada la nómina de pacientes atendidos.
* **Criterios de Aceptación:**
  - [ ] Búsqueda rápida por DNI con autocompletado.
  - [ ] Alta de nuevo paciente con validación de DNI único.
  - [ ] Historial de turnos anteriores del paciente.

### US-007 — Odontograma esquemático interactivo (FDI)
* **Como** odontólogo
* **Quiero** marcar el diagnóstico o tratamiento sobre la grilla interactiva de piezas dentales
* **Para** registrar visualmente el estado de la dentadura del paciente en su historia clínica.
* **Criterios de Aceptación:**
  - [ ] Representación visual de las 32 piezas dentales (FDI 11 a 48) agrupadas en 4 cuadrantes.
  - [ ] Al hacer clic en un diente, se puede asignar su estado (`sano`, `caries`, `obturacion`, `corona`, `extraccion`, `tratamiento_conducto`) y una nota breve.
  - [ ] Cada estado cuenta con un color representativo distintivo.
  - [ ] Los cambios se guardan en la base de datos asociados al paciente.

---

## Épica 4: Caja y Movimientos Diarios

### US-008 — Registro de cobros y señas
* **Como** recepcionista
* **Quiero** registrar el cobro de una atención o una seña anticipada indicando el medio de pago
* **Para** asentar los ingresos de dinero vinculados al turno o paciente.
* **Criterios de Aceptación:**
  - [ ] Formulario de cobro con monto, medio (`efectivo`, `transferencia`, `tarjeta`) y concepto.
  - [ ] Posibilidad de vincular el cobro a un turno específico.
  - [ ] El movimiento queda registrado con fecha/hora y usuario responsable.

### US-009 — Resumen diario de caja
* **Como** administrador o recepcionista
* **Quiero** consultar el balance del día con el desglose de ingresos por medio de pago
* **Para** realizar el arqueo de caja al finalizar la jornada laboral.
* **Criterios de Aceptación:**
  - [ ] Reporte que lista todos los movimientos del día seleccionado.
  - [ ] Totales calculados: Total Efectivo, Total Transferencias, Total Tarjetas y Balance Neto.

---

## Épica 5: Seguridad y Configuración

### US-010 — Autenticación y control de acceso (JWT)
* **Como** usuario del consultorio
* **Quiero** iniciar sesión con mis credenciales seguras
* **Para** acceder a las funciones permitidas según mi rol (`admin`, `recepcion`, `odontologo`).
* **Criterios de Aceptación:**
  - [ ] Login contra `/api/v1/auth/login` devuelve un JWT Bearer válido.
  - [ ] Redirección automática según rol y restricción de vistas protegidas.
  - [ ] Cierre de sesión seguro con limpieza de token en el cliente.

### US-011 — Gestión de sillones y profesionales
* **Como** administrador
* **Quiero** dar de alta o modificar los sillones y los profesionales odontólogos
* **Para** configurar la capacidad operativa del consultorio.
* **Criterios de Aceptación:**
  - [ ] ABM de sillones (definición de nombre y estado activo).
  - [ ] ABM de profesionales (matrícula, especialidad y duración habitual de turno).
