# CHANGES — Secuencia de Implementación

> Índice canónico de los changes del proyecto **Sistema Odontológico Multi-Sillón (AR)** adaptado para el parcial académico de **Metodología de Desarrollo de Sistemas**.
> Cada change es atómico y auto-contenido, diseñado para implementarse con rigor metodológico y pruebas automatizadas (TDD).

---

## Cómo usar este documento

1. Identificar el change a implementar (verificar que sus dependencias previas estén marcadas con `[x]`).
2. Leer los documentos de `knowledge-base/` indicados en "Leer antes".
3. Ejecutar `/opsx:propose <nombre-del-change>`.
4. Implementar las tareas respetando las Reglas Duras de [`AGENTS.md`](AGENTS.md).
5. Al finalizar las pruebas, archivar el change con `/opsx:archive <nombre-del-change>` y marcar el checkbox `[x]` en este archivo.

---

## Árbol de Dependencias del MVP Académico

```
C-01 foundation-setup [x]
  └── C-02 core-models-seed [x]
        └── C-03 auth-jwt-roles
              └── C-04 agenda-servicio-antisolapamiento
                    ├── C-05 agenda-frontend-interna
                    │     ├── C-07 clinica-odontograma
                    │     └── C-08 caja-movimientos-balance (Cierra MVP)
                    └── C-06 reserva-online-publica (Link/QR + WhatsApp)
```

---

## Lista de Changes

### C-01: `foundation-setup`
- **Estado:** `[x]` (Completado y archivado)
- **Alcance:** Esqueleto del backend FastAPI y frontend Vite + React, Docker Compose base y CI inicial.
- **Artefactos:** `backend/`, `frontend/`, `docker-compose.yml`.

---

### C-02: `core-models-seed`
- **Estado:** `[x]` (Completado y archivado)
- **Alcance:**
  - Declaración de modelos SQLAlchemy en `backend/src/app/` (`Usuario`, `Profesional`, `Sillon`, `Paciente`, `Turno`, `Bloqueo`, `Odontograma`, `HallazgoPieza`, `MovimientoCaja`).
  - Migración inicial de Alembic para crear el esquema en PostgreSQL.
  - Script o comando de carga de datos iniciales (`seed.py`): 3 sillones, 1 admin, 1 recepcionista, 2 odontólogos y 2 pacientes de prueba.
  - Tests de integridad del esquema y carga de semilla.
- **Dependencias:** C-01.
- **Leer antes:** `knowledge-base/04_modelo_de_datos.md`.
- **Comando:** `/opsx:propose C-02-core-models-seed`

---

### C-03: `auth-jwt-roles`
- **Estado:** `[ ]` (Próximo a implementar)
- **Alcance:**
  - Endpoint `POST /api/v1/auth/login` con validación de credenciales (hash con `bcrypt`).
  - Generación de token JWT Bearer estándar con expiración configurable.
  - Endpoint `GET /api/v1/auth/me` para obtener el perfil y rol del usuario logueado.
  - Dependencias de seguridad en FastAPI (`get_current_user`, `require_role("admin", "recepcion", "odontologo")`).
  - Integración básica del AuthContext en el frontend para almacenar token en sesión y proteger rutas.
  - Tests unitarios de login exitoso, login con contraseña errónea y restricción de roles (401/403).
- **Dependencias:** C-02.
- **Leer antes:** `knowledge-base/03_actores_y_roles.md`, `knowledge-base/08_arquitectura_propuesta.md`.
- **Comando:** `/opsx:propose C-03-auth-jwt-roles`

---

### C-04: `agenda-servicio-antisolapamiento`
- **Estado:** `[ ]`
- **Alcance:**
  - Capa de servicios (`TurnoService`) con la lógica central de negocio:
    - Validación de antisolapamiento cruzado (RN-AG-01): rechazar si el sillón está ocupado O si el profesional está ocupado en ese rango horario.
    - Exclusión de turnos cancelados en el cálculo de disponibilidad.
    - Cálculo automático de `fin = inicio + duracion_min` según la prestación (RN-AG-02).
  - Endpoints CRUD de turnos: `GET /api/v1/turnos` (filtros por fecha, profesional, sillón), `POST /api/v1/turnos`, `PATCH /api/v1/turnos/:id/estado`.
  - Endpoint de bloqueos: `POST /api/v1/bloqueos` y `DELETE /api/v1/bloqueos/:id`.
  - Suite exhaustiva de pruebas unitarias (`pytest`) que comprueben:
    - Creación de turno en hueco libre (201).
    - Rechazo de turno con solapamiento en el mismo sillón (409 Conflict).
    - Rechazo de turno con solapamiento del mismo profesional en distinto sillón (409 Conflict).
    - Creación exitosa en el mismo horario si los sillones Y los profesionales son distintos.
    - Creación exitosa sobre un turno previamente cancelado.
- **Dependencias:** C-03.
- **Leer antes:** `knowledge-base/05_reglas_de_negocio.md` (RN-AG-01 a RN-AG-06).
- **Comando:** `/opsx:propose C-04-agenda-servicio-antisolapamiento`

---

### C-05: `agenda-frontend-interna`
- **Estado:** `[ ]`
- **Alcance:**
  - Interfaz de agenda en React (`/app/agenda`):
    - Visualización en columnas por sillón físico (Sillón 1, Sillón 2, Sillón 3) para la fecha seleccionada.
    - Selector de fecha (navegación día actual, anterior, siguiente).
    - Código de colores visual por estado del turno (`reservado`, `confirmado`, `presente`, `atendido`, `cancelado`).
  - Modal para agendar nuevo turno con selección de paciente, profesional, prestación, sillón y horario.
  - Menú contextual o modal rápido para actualizar el estado del turno (ej. marcar como `presente` o `cancelado`).
- **Dependencias:** C-04.
- **Leer antes:** `knowledge-base/06_funcionalidades.md` (US-001, US-002), `knowledge-base/07_flujos_principales.md` (Flujo 2).
- **Comando:** `/opsx:propose C-05-agenda-frontend-interna`

---

### C-06: `reserva-online-publica`
- **Estado:** `[ ]`
- **Alcance:**
  - Endpoint público `GET /api/v1/public/disponibilidad` (devuelve huecos libres cruzando sillones y odontólogos).
  - Endpoint público `POST /api/v1/public/reservar` (crea el turno en estado `reservado` y emite `token_publico`).
  - Endpoint público `GET /api/v1/public/turnos/:token` y `POST /api/v1/public/turnos/:token/cancelar`.
  - Pantallas en React:
    - `/reservar`: Asistente paso a paso (1. Prestación → 2. Profesional → 3. Día/Hora libre → 4. Datos del paciente).
    - `/p/turno/:token`: Vista de confirmación con datos del turno y botón "Enviar aviso por WhatsApp" que abre enlace `https://wa.me/<telefono>?text=...` con el mensaje prearmado (RN-G-01).
- **Dependencias:** C-04.
- **Leer antes:** `knowledge-base/06_funcionalidades.md` (US-004, US-005), `knowledge-base/07_flujos_principales.md` (Flujo 1).
- **Comando:** `/opsx:propose C-06-reserva-online-publica`

---

### C-07: `clinica-odontograma`
- **Estado:** `[ ]`
- **Alcance:**
  - Endpoints de backend:
    - `GET /api/v1/pacientes` y `POST /api/v1/pacientes`.
    - `GET /api/v1/pacientes/:id/odontograma`.
    - `PUT /api/v1/pacientes/:id/odontograma/piezas/:pieza` (actualizar estado clínico y nota de una pieza dental).
  - Vistas en React:
    - Directorio y buscador de pacientes (`/app/pacientes`).
    - Componente de Odontograma interactivo (`/app/odontograma/:pacienteId`): grilla organizada en 4 cuadrantes con los 32 dientes FDI (11 a 48), selección visual de estado (`sano`, `caries`, `obturacion`, `corona`, `extraccion`, `conducto`) y guardado en tiempo real.
- **Dependencias:** C-05.
- **Leer antes:** `knowledge-base/04_modelo_de_datos.md` (Odontograma), `knowledge-base/05_reglas_de_negocio.md` (RN-CL-01).
- **Comando:** `/opsx:propose C-07-clinica-odontograma`

---

### C-08: `caja-movimientos-balance`
- **Estado:** `[ ]` (Cierre del MVP Académico)
- **Alcance:**
  - Endpoints de backend:
    - `POST /api/v1/caja/movimientos` (registro de ingreso/egreso con medio de pago, monto, concepto, `usuario_id` y vínculo opcional a `turno_id`).
    - `GET /api/v1/caja/movimientos` (listado con filtros de fecha).
    - `GET /api/v1/caja/resumen-diario` (totales agrupados por medio de pago y balance neto).
  - Pantalla en React (`/app/caja`):
    - Formulario modal de cobro rápido desde el turno atendido.
    - Formulario de egreso de caja.
    - Tabla del libro diario de movimientos y panel superior con tarjetas de balance (Efectivo, Transferencias, Tarjetas, Total del día).
- **Dependencias:** C-05.
- **Leer antes:** `knowledge-base/05_reglas_de_negocio.md` (RN-CJ-01, RN-CJ-02), `knowledge-base/07_flujos_principales.md` (Flujo 3).
- **Comando:** `/opsx:propose C-08-caja-movimientos-balance`
