# Tasks

Cwd canónico para todo: `backend/`. Regla TDD: cada grupo tiene su tarea RED (el test falla porque falta la implementación) antes de la tarea GREEN. Integración requiere `docker compose up` + `alembic upgrade head` desde `backend/` ANTES de correr la suite (Postgres con datos de `python -m app.db.seed`).

## 1. Setup

- [x] 1.1 Agregar `pyjwt>=2.8` a `backend/pyproject.toml` y verificar instalación: `pip install -e ".[dev]"` corre y `python -c "import jwt"` no falla.
- [x] 1.2 Crear barrels del módulo `backend/src/app/modules/auth/` (`router.py` con `router = APIRouter()` vacío, `schemas.py` con el recordatorio R1 `extra="forbid"`, `service.py`, sin `models.py`), y registrar el módulo: agregar `auth` a `MODULOS` y quitar `core/security.py` + `core/deps.py` de `CORE_STUBS` en `backend/test/test_structure.py`. Verificación: `pytest test/test_structure.py` queda VERDE con los barrels nuevos y sin exigir stubs a implementar.
- [x] 1.3 Documentar env en `.env.example` (raíz): `JWT_SECRET` (32+ chars, sin default demo) y `JWT_EXPIRE_MIN=720` (KB 08). Verificación: los valores aparecen en el archivo y `test_env_examples.py` sigue en verde.

## 2. Núcleo de seguridad JWT (TDD, sin DB)

- [x] 2.1 RED — Crear `backend/test/test_auth_security.py` con casos: `hash_password` produce hash bcrypt que `verify_password` valida y con password distinto rechaza; round-trip `crear_access_token`/`decodificar_token` devuelve `sub` + `rol` correctos; token con `exp` vencido → error; token firmado con otra clave → error; expiración configurable (2 tokens con `jwt_expire_min` distinto difieren en `exp`, usando settings concretas). Verificación RED: `pytest test/test_auth_security.py` falla porque `core/security.py` es stub.
- [x] 2.2 GREEN — Implementar `core/security.py`: `hash_password(password) -> str` y `verify_password(raw, hashed) -> bool` (bcrypt, rounds 12, reuso estilo seed); `crear_access_token(sub: str, rol: str, secret: str, expire_min: int) -> str` (HS256, claims `sub`/`rol`/`iat`/`exp`); `decodificar_token(token, secret) -> TokenPayload` (schema Pydantic `TokenPayload` con `sub`, `rol` validado contra `ROLES_USUARIO`, `exp`, `extra="forbid"`; `jwt.ExpiredSignatureError` y firmas inválidas se propagan como error manejable). Sin imports de FastAPI. Reemplaza el stub `TODO(C-03)` (y borra la mención heredada a refresh/`tenant_id`). Verificación: `pytest test/test_auth_security.py` en verde.

## 3. Servicio de autenticación (TDD, fake repo)

- [x] 3.1 RED — Crear `backend/test/test_auth_service.py` con un fake `find_by_email(email) -> Usuario | None` y casos: credenciales correctas → devuelve `Usuario`; password mal → `None`; email no registrado → `None`; usuario `activo=False` → `None`; email con mayúsculas/espacios se normaliza antes de la búsqueda. Verificación RED: `pytest test/test_auth_service.py` falla (función inexistente).
- [x] 3.2 GREEN — Implementar `modules/auth/service.py`: `autenticar_usuario(db, email, password) -> Usuario | None` que normaliza el email (trim + lower, igual que `validates` del modelo), resuelve por `find_by_email`, rechaza `activo=False` y verifica con `verify_password`. Type hints + snake_case (R5), sin HTTP ni logs de credenciales (R9). Verificación: `pytest test/test_auth_service.py` en verde.

## 4. Dependencias RBAC reutilizables (TDD)

- [x] 4.1 RED — Crear `backend/test/test_auth_deps.py`: `require_role("admin", "recepcion")` con `Usuario` en memoria de rol `recepcion` → pasa y devuelve el usuario; rol `odontologo` → levanta `HTTPException 403`; `get_current_user` resuelto con token expirado / firma inválida → `HTTPException 401` (probado contra la función con token generado en el test). Verificación RED: `pytest test/test_auth_deps.py` falla (deps.py es stub).
- [x] 4.2 GREEN — Implementar `core/deps.py`: `oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")`; `get_current_user(token, db)` con la revalidación por request (no existe o `activo=False` → 401); factory `require_role(*roles)` que valida `rol in roles` y devuelve el `Usuario`. Los 401/403 usan los mensajes fijos del diseño (D7). Verificación: `pytest test/test_auth_deps.py` en verde.

## 5. Endpoints de auth (TDD, HTTP real)

- [x] 5.1 RED — Crear `backend/test/test_auth_router.py` con `httpx.AsyncClient` sobre `create_app()` y `dependency_overrides`: login OK contra la base de test Postgres (seeded) → `200` con `access_token`/`token_type: "bearer"`/`expires_in` y sin `password_hash`; password mal → `401 {error:{code:"unauthorized", message:"Credenciales inválidas"}}`; campo extra en body → `422` (R1); `GET /auth/me` con `get_current_user` overrideado → `200 {id, nombre, email, rol}`; sin token → `401`; endpoint de prueba con `requirements` de rol (`Depends(require_role("admin"))` montado solo en el test) con rol odontólogo → `403 {error:{code:"forbidden"}}`. Verificación RED: `pytest test/test_auth_router.py` falla (routers vacíos).
- [x] 5.2 GREEN — Implementar `modules/auth/schemas.py` (`LoginIn` con `email` Form/Str válido y `password`, `extra="forbid"`, R1; `TokenOut`; `UsuarioOut` con `from_attributes`), `modules/auth/router.py` (`POST /login` → `service.autenticar_usuario`, token con `settings`; `GET /me` con `get_current_user`) y el `include_router` en `app/api/v1/router.py`. Verificación: `pytest test/test_auth_router.py` en verde.

## 6. Config guard (TDD)

- [x] 6.1 RED — Extender `backend/test/test_settings.py`: con `app_env="production"` y `jwt_secret` default ("changeme…") instanciar `Settings` falla; en `local` no falla. Verificación RED: el test nuevo falla (sin guard).
- [x] 6.2 GREEN — Agregar model validator en `core/config.py` que bloquea el arranque en producción con el secreto inseguro. Verificación: `pytest test/test_settings.py` completo en verde.

## 7. Verificación de integración (alcanza el change completo)

- [x] 7.1 Suite completa: desde `backend/` (con Postgres de Docker arriba y `alembic upgrade head` aplicado), `pytest` entero en verde — incluye `test_structure.py` actualizado y sin regresiones de C-01/C-02. Verificación: output de pytest sin errores. (Baselina pre-C-03: 86 passed / 8 skipped → final: 128 passed / 7 skipped.)
- [x] 7.2 Smoke E2E manual con curl contra la API levantada: `POST /api/v1/auth/login` con seed OK → token; `GET /api/v1/auth/me` con token → perfil; el mismo endpoint sin token → `401`; un endpoint protegido simulado montando un mini-router temporal con `dependencies=[Depends(require_role("admin"))]` y token de recepción → `403` (según el spec auth). Verificación: los 4 comportamientos observables se ven tal como se describen.
- [x] 7.3 Trazabilidad de reglas duras: revisar que R1 (`LoginIn`/`TokenOut` con `extra="forbid"`), R2 (cero `tenant_id`), R5 (type hints, snake_case, sin migración porque el esquema no cambia), R8 (401/403 resueltos por dependencias en el backend), R9 (sin password/token en logs ni URLs) y R13 (login rechaza `activo=False`, baja lógica) tienen evidencia en tests. Verificación: checklist en la descripción del PR del change con test_id por regla.

Checklist C-03 con evidencia por test (7.3):

| Regla | Evidencia (test_id) |
|---|---|
| R1 (`extra="forbid"`) | `test_auth_router.py::test_login_campo_extra_da_422` (422 en body con campo inyectado) · `test_auth_security.py::test_token_con_rol_fuera_del_catalogo_rechaza` (payload de token con claim/rol no declarado → ValidationError) · `test_structure.py::test_schemas_stubs_recuerdan_extra_forbid` |
| R2 (cero `tenant_id`) | `test_auth_security.py::test_payload_no_lleva_email_ni_nombre_ni_tenant` (claims = {sub, rol, iat, exp}) · `test_structure.py::test_auth_no_duplica_modelo_usuario` (auth sin models.py; Usuario vive en admin) |
| R5 (type hints + snake_case + migración solo si cambia schema) | Sin migración nueva (Usuarios ya tenía `rol`/`password_hash`/`activo` de C-02; `alembic upgrade head` corre sin revisiones nuevas) · `test_migrations.py::test_baseline_habilita_btree_gist` sigue en verde · APIs/JS: `access_token`, `token_type`, `expires_in` snake_case (D7) |
| R8 (RBAC en backend) | `test_auth_deps.py::test_require_role_rechaza_con_403` · `test_auth_router.py::test_endpoint_protegido_rol_odontologo_da_403` y `test_me_sin_token_da_401` (curl directo: 403/401 server-side, smoke 7.2) |
| R9 (sin datos sensibles en logs ni URLs) | `test_auth_security.py::test_payload_no_lleva_email_ni_nombre_ni_tenant` · `test_auth_router.py::test_login_ok_devuelve_token_bearer` y `test_me_devuelve_perfil_sin_password_hash` (jamás `password_hash`) · `test_login_email_desconocido_da_el_mismo_401` (error genérico anti-enumeración) · token solo viaja por header Bearer |
| R13 (baja lógica, nunca DELETE físico de `Usuarios`) | `test_auth_service.py::test_usuario_dado_de_baja_devuelve_none` · `test_auth_deps.py::test_usuario_dado_de_baja_con_token_vigente_da_401` (revalidación per-request) |

## Workflow follow-up

- Ejecutar `/opsx:validate` y `/opsx:archive c-03-auth-jwt-roles` cuando las 7 tareas estén en verde y el change sea revisado.
- Marcar `[x]` la sección C-03 en `CHANGES.md` tras el archive.
- Avisar a C-04 que `require_role` / `get_current_user` ya están listos (contrato en `design.md` D6/D7).
