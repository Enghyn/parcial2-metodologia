# Descripción General

## Stack tecnológico

Stack del proyecto orientado a robustez, tipado estricto y mantenibilidad para el parcial académico:

| Capa | Tecnología | Versión mínima | Justificación |
|---|---|---|---|
| Lenguaje backend | Python | 3.12+ | Tipado estricto, sintaxis moderna, alta productividad |
| Framework API | FastAPI | 0.110+ | Validación automática con Pydantic, documentación OpenAPI interactiva |
| ORM | SQLAlchemy | 2.0+ | Mapeo objeto-relacional asíncrono con control explícito de consultas |
| Base de datos | PostgreSQL | 15+ | Integridad referencial, transacciones ACID y performance |
| Migraciones | Alembic | 1.13+ | Versionado del esquema de base de datos |
| Auth | JWT Bearer (`PyJWT` / `python-jose`) | — | Tokens de acceso estándar para roles internos (`admin`, `odontologo`, `recepcion`) |
| UI Frontend | React + TypeScript | 18+ / TS 5+ | Componentes reactivos fuertemente tipados |
| Bundler frontend | Vite | 5+ | Tiempos de compilación ultrarrápidos y HMR |
| Estilos | Tailwind CSS | v4 | Estilos declarativos y diseño responsivo |
| Despliegue local | Docker Compose | v2 | Entorno reproducible con 3 servicios: `api`, `web`, `postgres` |

## Arquitectura general

El sistema adopta un patrón de **Monolito Modular** estructurado en backend y una **SPA en React** en frontend:

```
                  ┌──────────────────────────────────────────────┐
                  │                 Navegador Web                │
                  │   Superficie Pública:  /reservar (Turnos)    │
                  │   Superficie Privada:  /app (Gestión)        │
                  └───────────────────────┬──────────────────────┘
                                          │
                                          │ HTTP / JSON (Axios)
                                          │ (Bearer JWT en /app)
                                          ▼
                  ┌──────────────────────────────────────────────┐
                  │            FastAPI (Monolito Modular)        │
                  │                                              │
                  │  ┌───────────────┬────────────────────────┐  │
                  │  │ Auth & Users  │ Agenda & Antisolape    │  │
                  │  ├───────────────┼────────────────────────┤  │
                  │  │ Pacientes     │ Odontograma FDI        │  │
                  │  ├───────────────┼────────────────────────┤  │
                  │  │ Caja & Cobros │ Notificaciones (Mock)  │  │
                  │  └───────────────┴────────────────────────┘  │
                  │                                              │
                  │  - Validación de Schemas (Pydantic v2)       │
                  │  - Reglas de Negocio en Servicios            │
                  │  - BackgroundTasks nativas para logs/avisos  │
                  └───────────────────────┬──────────────────────┘
                                          │
                                          │ SQLAlchemy 2.0
                                          ▼
                  ┌──────────────────────────────────────────────┐
                  │            PostgreSQL 15 (Docker)            │
                  │     Esquema relacional íntegro y testeado    │
                  └──────────────────────────────────────────────┘
```

## Estructura de Módulos de la API

La API expone sus recursos bajo el prefijo `/api/v1`:

- **Auth & Usuarios** (`/api/v1/auth`, `/api/v1/usuarios`):
  - `POST /auth/login` (credenciales → Access Token JWT).
  - `GET /auth/me` (perfil del usuario autenticado).
  - `GET/POST /usuarios` (gestión de usuarios internos con roles).
- **Consultorio & Infraestructura** (`/api/v1/sillones`, `/api/v1/profesionales`):
  - `GET/POST /sillones` (listado y alta de los 2 o 3 sillones físicos).
  - `GET/POST /profesionales` (odontólogos, matrícula, especialidad).
- **Agenda & Turnos** (`/api/v1/turnos`):
  - `GET /turnos?fecha=&sillon_id=&profesional_id=` (calendario diario/semanal).
  - `POST /turnos` (creación de turno con validación antisolapamiento).
  - `PATCH /turnos/:id` (cambio de estado: reservado, confirmado, presente, cancelado, atendido).
  - `POST /bloqueos` (bloqueo de sillón o profesional por horarios/mantenimiento).
- **Reserva Pública** (`/api/v1/public`):
  - `GET /public/disponibilidad` (consulta de huecos libres sin login).
  - `POST /public/reservar` (reserva directa por paciente con nombre, DNI y teléfono).
  - `GET /public/turnos/:token` (consulta de estado con enlace `wa.me/` para confirmar).
- **Clínica & Odontograma** (`/api/v1/pacientes`, `/api/v1/odontograma`):
  - `GET/POST /pacientes` (búsqueda por DNI/nombre y ficha personal).
  - `GET /pacientes/:id/odontograma` (obtener estado actual de las piezas FDI 11–48).
  - `PUT /pacientes/:id/odontograma/piezas/:pieza` (actualizar estado y tratamiento de una pieza).
- **Caja & Cobros** (`/api/v1/caja`):
  - `GET/POST /caja/movimientos` (ingresos, egresos, medios de pago y conceptos).
  - `GET /caja/resumen-diario` (balance total por día y por medio de pago).
