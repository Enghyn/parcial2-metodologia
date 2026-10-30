# Actores y Roles

## Actores del sistema

| Actor | Descripción | Entorno de Interacción |
|---|---|---|
| **Paciente (Público)** | Usuario que solicita atención médica dental. No requiere credenciales ni login en el sistema. | Portal web público (`/reservar` y `/p/turno/:token`), mobile-friendly. |
| **Recepcionista / Secretaría** | Personal administrativo encargado de la atención diaria, agenda y cobros. | Aplicación privada (`/app/agenda`, `/app/pacientes`, `/app/caja`). |
| **Odontólogo** | Profesional de la salud que atiende en los sillones y registra la evolución clínica. | Aplicación privada (`/app/mi-agenda`, `/app/odontograma`). |
| **Administrador / Dueño** | Responsable de la gestión del consultorio, configuración y métricas. | Aplicación privada (acceso total a configuración, usuarios y reportes). |

## Matriz de Permisos (RBAC)

La autorización se valida en FastAPI mediante dependencias reutilizables (`require_role(...)`):

| Módulo / Recurso | `admin` | `recepcion` | `odontologo` | `publico` (sin login) |
|---|---|---|---|---|
| **Agenda (Turnos)** | CRUD completo | CRUD (crear, confirmar, cancelar, reprogramar) | Ver agenda propia + marcar turno atendido | Crear reserva pública / Cancelar con token |
| **Sillones y Profesionales** | CRUD (alta/baja sillones y profesionales) | Lectura de disponibilidad | Lectura de disponibilidad | Lectura de disponibilidad para reserva |
| **Bloqueos de Agenda** | Crear / Eliminar bloqueos | Crear / Eliminar bloqueos | Crear bloqueo propio | Solo lectura indirecta (no ve huecos bloqueados) |
| **Pacientes** | CRUD completo | CRUD (alta, edición de datos de contacto) | Lectura de sus pacientes | Crear ficha inicial al reservar |
| **Odontograma Clínico** | Lectura completa | Lectura de prestaciones | CRUD (actualizar piezas dentales y tratamientos) | — |
| **Caja y Movimientos** | CRUD + Cierre diario y balance | Registro de ingresos/egresos y cobro de turnos | — | — |
| **Usuarios y Roles** | CRUD de usuarios (`admin`, `recepcion`, `odontologo`) | — | — | — |

## Superficies de la Aplicación

### 1. Superficie Pública (sin autenticación)
* `/reservar`: Asistente interactivo en pasos para reservar turno (selección de prestación, sillón/profesional, fecha/hora y datos del paciente).
* `/p/turno/:token`: Vista del comprobante de reserva con token UUID seguro, con botón directo para contactar al consultorio por WhatsApp (`wa.me/?text=...`) y opción de cancelación autónoma.

### 2. Superficie Privada (requiere JWT Bearer)
* `/app/login`: Formulario de inicio de sesión con email y contraseña.
* `/app/agenda`: Vista multi-sillón diaria/semanal con discriminación visual de estados y alertas de solapamiento.
* `/app/pacientes`: Directorio de pacientes, historial de visitas y acceso a la ficha clínica.
* `/app/odontograma/:pacienteId`: Interfaz interactiva de la dentadura (grilla FDI) para marcar diagnósticos y procedimientos.
* `/app/caja`: Registro de cobros, señas, gastos y resumen de caja por turno o día.
* `/app/admin`: Gestión de usuarios, sillones y configuraciones generales del consultorio.
