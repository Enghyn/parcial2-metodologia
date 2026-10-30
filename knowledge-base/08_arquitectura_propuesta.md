# Arquitectura Propuesta

Monolito modular FastAPI + React SPA + PostgreSQL + Docker Compose. Arquitectura orientada a la simplicidad, robustez y facilidad de prueba para el entorno académico.

---

## Patrones Arquitectónicos Aplicados

| Patrón | Dónde se aplica | Propósito |
|---|---|---|
| **Monolito Modular** | Backend en `backend/src/app/modules/` | Mantiene el código organizado por dominio de negocio (agenda, clínica, caja, admin) en un único despliegue simple. |
| **Capa de Servicios (Service Layer)** | En cada módulo de backend | Aísla la lógica de negocio (validación antisolapamiento, cálculo de horarios, balance de caja) de los controladores HTTP. |
| **Dependency Injection** | FastAPI `Depends` (`get_db`, `get_current_user`, `require_role`) | Inyección de sesiones de base de datos y autorización declarativa en endpoints. |
| **Data Transfer Objects (DTO)** | Schemas Pydantic v2 con `extra='forbid'` | Validación estricta de tipos de entrada y serialización segura de respuestas. |
| **Click-to-Chat Adapter** | Rutas públicas y notificaciones | Generación declarativa de URLs `wa.me/` sin acoplarse a APIs propietarias. |

---

## Estructura de Directorios

```
active-or-practica/
├── docker-compose.yml          # Servicios: api + web + postgres
├── backend/
│   ├── Dockerfile
│   ├── pyproject.toml          # Dependencias: fastapi, sqlalchemy, alembic, pydantic-settings, pyjwt
│   ├── alembic.ini
│   ├── src/
│   │   └── app/
│   │       ├── main.py         # App factory, CORS, middlewares y router raíz
│   │       ├── core/           # config.py, security.py (JWT), deps.py, errors.py
│   │       ├── db/             # base.py, session.py, migrations/ (Alembic)
│   │       └── modules/
│   │           ├── auth/       # Login, hash de contraseñas y obtención de perfil
│   │           ├── agenda/     # Turnos, sillones, profesionales, validación antisolapamiento
│   │           ├── clinica/    # Pacientes, fichas, odontograma FDI y hallazgos
│   │           ├── caja/       # Movimientos de caja, cobros, resumen diario
│   │           └── admin/      # Gestión de usuarios del sistema
│   └── test/                   # Tests unitarios y de integración (pytest)
└── frontend/
    ├── Dockerfile
    ├── vite.config.ts
    ├── package.json
    └── src/
        ├── app/                # Router, AuthProvider, Layouts privado y público
        ├── features/
        │   ├── agenda/         # Calendario multi-sillón (columnas por sillón), modales de turno
        │   ├── reserva-publica/ # Asistente paso a paso para el paciente (/reservar)
        │   ├── clinica/        # Odontograma interactivo (grilla FDI 11–48) y ficha médica
        │   └── caja/           # Formulario de cobros y arqueo diario
        └── shared/             # Cliente API (Axios), componentes UI (Tailwind), hooks
```

---

## Seguridad y Control de Acceso

1. **Autenticación:**
   - JWT estándar (Access Token) firmado mediante HMAC-SHA256 con clave secreta (`JWT_SECRET`).
   - Expiración configurable (default: 720 minutos / 12 horas para facilitar la jornada de trabajo).
2. **Autorización (RBAC):**
   - Resuelta en FastAPI mediante dependencias:
     ```python
     @router.post("/turnos", dependencies=[Depends(require_role("admin", "recepcion"))])
     async def crear_turno(...): ...
     ```
3. **Validación de Datos:**
   - Schemas Pydantic con validación de expresiones regulares (DNI, teléfono), rangos de fechas (`fin > inicio`) y montos positivos.
4. **Protección de Datos:**
   - Contraseñas almacenadas exclusivamente como hashes mediante `bcrypt`.

---

## Variables de Entorno (.env)

| Variable | Descripción | Valor por Defecto / Ejemplo |
|---|---|---|
| `DATABASE_URL` | Conexión a PostgreSQL | `postgresql+psycopg://odonto:odonto@postgres:5432/odonto` |
| `JWT_SECRET` | Clave para firma de tokens | `super-secret-key-32-chars-long-min` |
| `JWT_EXPIRE_MIN` | Minutos de vida del token | `720` |
| `CORS_ORIGINS` | Orígenes permitidos para el frontend | `http://localhost:5173,http://localhost:3000` |
| `APP_ENV` | Entorno de ejecución | `development` |
