# Proposal — C-03: auth-jwt-roles

## Why

La superficie privada (`/app/**` y toda la API interna `/api/v1/*`) todavía es accesible sin credenciales: `backend/src/app/core/security.py` y `core/deps.py` son stubs con `TODO(C-03)` y ningún router exige token. La KB (03_actores_y_roles, RN-SEG-01) exige que toda la API interna requiera `Authorization: Bearer <token_jwt>` y que la autorización RBAC se resuelva en el backend. C-04 (agenda) es el primer consumidor de los turnos: necesita `get_current_user` y `require_role(...)` antes de poder escribir su primer endpoint. Ahora es el momento porque C-02 ya dejó el modelo `Usuario` (con `rol` y `password_hash`) y el seed con usuarios de prueba arrancable.

## What Changes

- Nuevo módulo `backend/src/app/modules/auth/` con los endpoints:
  - `POST /api/v1/auth/login` — valida `email` + `password` (hash **bcrypt**), devuelve access token JWT Bearer.
  - `GET /api/v1/auth/me` — devuelve perfil y rol del usuario logueado (requiere token).
- `core/security.py` (reemplaza el stub): `hash_password` / `verify_password` (bcrypt), `crear_access_token` / `decodificar_token` (PyJWT, HMAC-SHA256 con `JWT_SECRET`). Expiración configurable vía `JWT_EXPIRE_MIN` ya existente en `Settings`.
- `core/deps.py` (reemplaza el stub): dependencias reutilizables de FastAPI para C-04+ — `get_current_user` (401 ante token ausente/inválido/expirado o usuario `activo=False`) y `require_role(*roles)` (403 ante rol insuficiente).
- `modules/auth/router.py` montado en el agregador `app/api/v1/router.py` (su primer `include_router`, que hoy nace vacío a propósito).
- Nueva dependencia `pyjwt` en `backend/pyproject.toml` (bcrypt ya está).
- Contrato de API documentado (schemas Pydantic con `extra="forbid"`, R1) como especificación para que C-05 construya el login UI sin adivinar.
- **Documentación del login básico frontend**: se registra el contrato HTTP (shapes de request/response y códigos 401/403/422) en `design.md`; la implementación React queda para C-05 (out of scope acá).

## Capabilities

### New Capabilities

- `auth`: Autenticación de personal interno por JWT Bearer (login, token con claims de rol, perfil `/me`), la verificación de token en el backend y las dependencias de autorización RBAC (`admin`, `recepcion`, `odontologo`) que consume toda la API interna desde C-04 en adelante. Propiedad del comportamiento durable: cómo se entra, cómo se valida la identidad y cómo se aplican los roles.

### Modified Capabilities

- (ninguna — `core-data-model` conserva la persistencia de `Usuario` sin cambios: C-03 no altera ni agrega columnas, por lo que no hace falta migración Alembic; la autorización vive en una capability nueva).

## Impact

- **Código nuevo**: `backend/src/app/modules/auth/{router,schemas,service}.py` (los barrels stub de `auth` no existen todavía porque `MODULOS` en `test_structure.py` no lo incluye; se crean con esta change).
- **Código reemplazado**: `backend/src/app/core/security.py`, `backend/src/app/core/deps.py` (stubs dueño C-03) y una línea de `main.py`/`api/v1/router.py` para el `include_router`.
- **Tests**: nuevos `backend/test/test_auth_*.py`; `backend/test/test_structure.py` deja de listar `core/security.py` y `core/deps.py` como stubs.
- **Dependencias**: `pyjwt>=2.8` agregado a `backend/pyproject.toml`.
- **Config**: se documentan/usan `JWT_SECRET` y `JWT_EXPIRE_MIN` en `.env.example` (ya declaradas en KB 08 y en `Settings`).
- **Consumidores futuros**: C-04 (turnos/bloqueos), C-07 (pacientes/odontograma), C-08 (caja) usan `Depends(require_role(...))` sin nueva infraestructura.
