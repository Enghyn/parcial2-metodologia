# Visión y Objetivos

## Propósito del sistema

**Optimizar la gestión integral de un consultorio odontológico con múltiples sillones (2–3 sillones de atención), unificando la agenda con validación de antisolapamiento, reserva pública online, ficha odontológica con odontograma esquemático y control de caja.**

El proyecto está diseñado con foco académico en **Metodología de Desarrollo de Sistemas**, priorizando la calidad del software, la separación de capas, el cumplimiento de reglas de negocio centrales y una arquitectura limpia y testeable (FastAPI + React), evitando sobrecostos de infraestructura comercial o dependencias complejas de terceros.

## Objetivos por actor

| Actor | Objetivo principal | Objetivos secundarios |
|---|---|---|
| Paciente | Reservar y consultar turnos de forma autónoma (portal online sin login) | Confirmar o cancelar turnos mediante enlaces directos a WhatsApp (`wa.me/`) |
| Recepción / Secretaría | Gestionar la agenda del día/semana sin solapamientos entre profesionales y sillones | Registrar pacientes, dar turnos, registrar cobros y cierres de caja |
| Odontólogo | Visualizar su agenda diaria y actualizar la ficha del paciente con odontograma | Registrar hallazgos y tratamientos por pieza dental (nomenclatura FDI) |
| Administrador | Configurar profesionales, sillones y aranceles; supervisar reportes de ocupación y caja | Gestionar usuarios internos y auditar operaciones clave |

## Alcance del MVP Académico

- **Agenda multi-profesional y multi-sillón (2 a 3 sillones)** con duración variable por prestación y **validación antisolapamiento lógica en backend** (control cruzado: ni el sillón ni el profesional pueden tener turnos superpuestos).
- **Portal de reserva online pública (24/7)** con link o QR, sin login obligatorio para el paciente (identificación por Nombre, DNI y Teléfono).
- **Comunicación y confirmación de turnos**: Enlaces directos a WhatsApp (`wa.me/`) generados en la interfaz y servicio de notificaciones simulado (registro en BD/consola).
- **Ficha clínica y Odontograma esquemático**: Visualización y edición de las piezas dentales (FDI 11–48) para registrar estados clínicos básicos (sano, caries, obturación, corona, extracción).
- **Caja y Cobros**: Registro de movimientos de caja diaria (ingresos/egresos, medios de pago: efectivo, transferencia, tarjeta), registro de señas y trazabilidad de operaciones.
- **Seguridad y Roles**: Autenticación JWT Bearer simple para usuarios internos con control de acceso basado en roles (`admin`, `odontologo`, `recepcion`).

## Fuera de alcance (simplificaciones deliberadas)

- Arquitectura SaaS multi-tenant compleja (el sistema opera para un consultorio único con múltiples sillones y usuarios).
- Integración directa con Meta Cloud API para WhatsApp (se utiliza simulación y links `wa.me/`).
- Webhooks de pasarelas de pago externas como Mercado Pago IPN (los cobros y señas se gestionan de forma directa/simulada).
- Servidor de colas Redis / Celery (se aprovechan las `BackgroundTasks` nativas de FastAPI para procesos en segundo plano).
- Facturación electrónica legal con ARCA/AFIP (requiere certificados fiscales X.509 fuera del ámbito académico).
- Visores de imágenes radiográficas con IA o periodontogramas avanzados.

## Métricas de éxito del proyecto

| # | Métrica | Meta esperada | Verificación |
|---|---|---|---|
| M-01 | Cero solapamientos en agenda | 100% de solapamientos bloqueados (sillón y profesional) | Tests unitarios y de integración en backend |
| M-02 | Cobertura de tests en reglas core | ≥ 80% en agenda, caja y permisos | Reporte de pytest |
| M-03 | Flujo de reserva pública fluido | Creación de turno en < 4 pasos sin login | Prueba E2E en frontend |
| M-04 | Trazabilidad de caja | Cero inconsistencias en balance diario de caja | Balance de movimientos de caja |
| M-05 | Experiencia de usuario en odontograma | Carga y actualización ágil de piezas FDI | Validación en interfaz de React |
