# Preguntas Abiertas y Resoluciones

## Decisiones Fundacionales Cerradas

Las inconsistencias e incertidumbres iniciales de la fase de descubrimiento quedaron formalmente resueltas para encuadrar el proyecto en los objetivos académicos:

| Tema | Estado | Resolución Adoptada |
|---|---|---|
| **Acceso del Paciente** | Cerrado | Reserva online pública **sin login** (identificación por Nombre, DNI y Teléfono; consulta por `token_publico`). |
| **Capacidad de Sillones** | Cerrado | Consultorio con **2 a 3 sillones físicos**, con validación de antisolapamiento lógica en backend. |
| **Integración con WhatsApp** | Cerrado | **Click-to-Chat (`wa.me/`)** desde la interfaz con mensajes parametrizados + simulación en consola (sin Meta Cloud API). |
| **Pasarela de Cobros** | Cerrado | Gestión de caja directa (registro de cobros y señas manuales/simuladas, sin webhooks externos de Mercado Pago). |
| **Infraestructura Asíncrona** | Cerrado | Uso de **`BackgroundTasks` nativas de FastAPI**, descartando Redis y Celery/RQ. |
| **Facturación Fiscal** | Cerrado | Excluida del alcance del MVP (no se conecta a servicios de ARCA/AFIP). |

---

## Puntos Menores a Definir en la Implementación

| Prioridad | Pregunta | Módulo Afectado | Recomendación |
|---|---|---|---|
| **Baja** | ¿Cuál es la granularidad de la grilla de disponibilidad horaria? | Agenda pública y turnero | Slots de 30 minutos por defecto (8:00 a 20:00 hs). |
| **Baja** | ¿El arqueo de caja requiere exportación a archivo plano? | Módulo de Caja | Generación de resumen visual en pantalla con opción de descarga en CSV simple. |
| **Baja** | ¿Se contemplan piezas dentales temporales (dientes de leche) en el odontograma? | Odontograma | Solo 32 piezas permanentes (FDI 11–48) para el MVP. |
| **Media** | ¿La duración del turno se deriva de un catálogo `Prestacion` o se carga manual/por profesional? | Agenda (C-04) | Mantener `duracion_min` manual en C-04; evaluar catálogo de prestaciones en fase 2. |
| **Media** | ¿En qué estado del turno se devenga o retiene la seña? | Caja (C-08) | Registrar la seña al reservar y deducirla al pasar el turno a `atendido`. |
| **Baja** | ¿Se aceptan triggers de base para R3/R13 en producción? | Persistencia | Sí: son defensa en profundidad; el ORM mantiene los mensajes amigables. |
