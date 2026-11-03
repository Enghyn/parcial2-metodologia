# Design — C-03: auth-jwt-roles

## Context

Del código C-01/C-02 existen ya: `Settings` con `jwt_secret` / `jwt_expire_min` / `cors_origins` (`core/config.py`), el modelo `Usuario` con `rol`, `password_hash` y `activo` (`modules/admin/models.py`), bcrypt como dependencia en `pyproject.toml`, la forma única de error `{error:{code,message}}` (`core/errors.py`) y `get_db` yield-DI (`db/session.py`). Los stubs `core/security.py` y `core/deps.py` están rotulados `TODO(C-03)` (dueño de esta change) y ningún router fuerza autenticación todavía.

Restricciones duras aplicables: R1 (`extra="forbid"`), R2 (sin `tenant_id`), R5 (type hints + snake_case; solo migración si cambia el esquema), R8 (RBAC en el backend), R9 (nada de credenciales en logs ni URLs). El stub `security.py` menciona "refresh rotado con claims `tenant_id`": es texto heredado que esta change **elimina a propósito** — R2 prohíbe `tenant_id` (mono-consultorio, DD-02) y el alcance C-03 es un solo access token.

## Goals / Non-Goals

**Goals:**
- Login por JWT Bearer + perfil `/me`, con el rol en el token y 401/403 correctos.
- Dependencias `get_current_user` / `require_role(...)` **reutilizables** que C-04, C-07 y C-08 consumen por `Depends` sin tocar el core de seguridad.
- Suite TDD (pytest) que cubre login exitoso/fallido, token expirado/inválido, usuario dado de baja y RBAC 401/403.
- Contrato de API documentado (shapes de request/response + códigos) para que C-05 haga el login UI sin adivinar.

**Non-Goals:**
- Refresh token, rotación, blacklist por `jti` o revocación server-side: la expiración configurable es la política del MVP académico (si hiciera falta, es una change futura que no rompe el contrato).
- Gestión CRUD de usuarios (`Usuarios y Roles` de la matriz KB, solo `admin`): módulo `admin`, change futura.
- Login UI React / AuthContext / almacenamiento del token en frontend: C-05. Acá solo se fija el contrato HTTP.
- Rate limiting y lockout por intentos: fuera del MVP (riesgo aceptado en la sección de riesgos).
- OAuth2 con cookies o sesión server-side: solo header `Authorization: Bearer`.

## Decisions

### D1 — Biblioteca JWT: PyJWT (nueva dependencia)
`pyjwt>=2.8` se agrega a `backend/pyproject.toml`. Alternativas: `python-jose` (más pesada, con historial de CVEs de mantenimiento irregular) y firmar a mano con `hmac` (frágil y mal revisable). PyJWT es la que la KB 08 ya lista para el backend y la mínima para firmar/verificar HS256.

### D2 — Un solo access token, sin refresh (y sin `tenant_id`)
CHANGES.md C-03 pide "token JWT Bearer estándar con expiración configurable" y nada más. La jornada de recepción (KB 08: `JWT_EXPIRE_MIN=720`) se cubre con expiración larga configurada por entorno. Se elimina el texto del stub que sugería refresh + `tenant_id` (R2). Alternativa considerada (access 15 min + refresh rotado): descartada — agrega endpoints, storage server-side y superficie de bugs para un sistema que no exige revocación.

### D3 — Contraseñas: bcrypt (ya en el proyecto), rounds 12
Se reutiliza `bcrypt.hashpw` / `bcrypt.checkpw` — misma librería y `rounds=12` que el seed C-02 ya usa en `_hash_password`, con lo que los usuarios del seed loguean contra `/auth/login` sin re-seed ni migración de hashes. No se agrega `passlib`: duplicaría la dependencia; la verificación con `checkpw` ya es constant-time por sí sola.

### D4 — Estructura de módulos (fastapi-templates, layout del repo)

```
backend/src/app/
├── core/
│   ├── security.py   # hash_password, verify_password, crear_access_token, decodificar_token
│   └── deps.py       # oauth2_scheme, get_current_user, require_role
├── modules/auth/
│   ├── router.py     # POST /auth/login (público), GET /auth/me (get_current_user)
│   ├── schemas.py    # LoginIn (extra="forbid", R1), TokenOut, UsuarioOut
│   └── service.py    # autenticar_usuario(db, email, password) -> Usuario | None (sin HTTP)
└── api/v1/router.py  # + include_router(auth.router)
```

- El módulo `auth` no tiene `models.py`: el `Usuario` es propiedad de `modules/admin` (C-02) y se importa, no se duplica la entidad.
- `core/security.py` queda sin dependencias de FastAPI (funciones puras, testeable sin app); `core/deps.py` es lo único que conoce FastAPI + DB.
- `modules/auth/service.py` aísla la lógica de negocio del controlador HTTP (Service Layer, KB 08) y solo depende de la sesión.

### D5 — Token payload (claims mínimos)

```json
{
  "sub": "<uuid del usuario (str)>",
  "rol": "admin|recepcion|odontologo",
  "iat": 1699000000,
  "exp": 1699000000 + jwt_expire_min * 60
}
```

- `alg: HS256`, clave `settings.jwt_secret` (env `JWT_SECRET`, ya declarada en `Settings`).
- Claims mínimos: **no** se embebe email ni nombre — los datos descriptivos se leen de la DB en `/me`; evita stale claims y conserva el token pequeño.
- Los claims decodificados validan contra un schema Pydantic `TokenPayload` (`sub: str`, `rol: Literal[...]`, `exp: int`), con `extra="forbid"` también acá: un claim inesperado o rol fuera del catálogo rechaza el token en vez de pasarse por defecto.
- Expiración: `settings.jwt_expire_min`; no se hardcodea 720. `.env.example` documenta `JWT_EXPIRE_MIN=720` (jornada plena, KB 08).
- Guard de arranque en `Settings`: con `APP_ENV=production`, un `JWT_SECRET` con el default inseguro ("changeme…") hace fallar el arranque — coherente con "falla al arrancar si falta una variable requerida" del backend-foundation, extendido a "no segura".

### D6 — Dependencias DI (contrato que consume C-04)

```python
# app/core/deps.py — lo único que C-04+ importa
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/api/v1/auth/login")

async def get_current_user(
    token: Annotated[str, Depends(oauth2_scheme)],
    db: Annotated[Session, Depends(get_db)],
) -> Usuario: ...

def require_role(*roles: str) -> Callable[..., Usuario]:
    """Factory de dependencia: Depends(require_role("admin", "recepcion"))."""
```

- **`get_current_user`**: ante token ausente o header inválido → `HTTPException(401, "No autenticado")`; `decodificar_token` → 401 ("Token expirado" / "Token inválido"); carga `select(Usuario).where(Usuario.id == sub, Usuario.activo == true)` → 401 si no existe o está dado de baja (revalidación por request; la baja lógica de `Usuario` es `activo`, columna de C-02 — RN-SEG-02 lista a las 4 entidades de negocio y `Usuario` no cambia su esquema). Devuelve el ORM `Usuario` para que los endpoints no re-consulten.
- **`require_role(*roles)`**: factory que cierra sobre la lista de roles declarada por cada endpoint; en runtime recibe `Usuario` resuelto por `get_current_user` y valida `user.rol in roles` → `HTTPException(403, "Rol insuficiente")` si no. También devuelve el `Usuario`, por si el endpoint lo usa (ej. "agenda propia" de odontólogo).
- Uso declarativo en C-04 (igual a KB 03 + KB 08; RBAC 100% backend, R8):

```python
@router.post("/turnos", dependencies=[Depends(require_role("admin", "recepcion"))])
async def crear_turno(...): ...   # odontologo NO accede

@router.patch("/turnos/{id}/estado")
async def cambiar_estado(
    user: Annotated[Usuario, Depends(require_role("admin", "recepcion", "odontologo"))], ...
): ...
```

- El catálogo de roles es único: la constante `ROLES_USUARIO` vive en `modules/admin/models.py` (C-02) y `security.py` no la redeclara — valida contra esa constante.

### D7 — Contrato HTTP para C-05 (documentación de la API)

Errores ya tienen shape `{error:{code,message}}` (core/errors). Mensajes fijos es-AR:

| Caso | HTTP | `error.code` | `error.message` |
|---|---|---|---|
| Sin header Bearer | 401 | `unauthorized` | `No autenticado` |
| Token expirado | 401 | `unauthorized` | `Token expirado` |
| Token inválido (firma/payload) | 401 | `unauthorized` | `Token inválido` |
| Credenciales (email o password) | 401 | `unauthorized` | `Credenciales inválidas` — no revela cuál falló |
| Rol insuficiente | 403 | `forbidden` | `Rol insuficiente` |
| Campo desconocido en body | 422 | `unprocessable_entity` | (validación pydantic) |

Éxito:
- `POST /api/v1/auth/login` → `200 {access_token: str, token_type: "bearer", expires_in: int}`; `expires_in` = `jwt_expire_min * 60` (para el contador de sesión del front).
- `GET /api/v1/auth/me` → `200 {id, nombre, email, rol}` — nunca expone `password_hash` (R9) sino el mínimo para la UI.

Nota de proyecto: los campos JSON van en `snake_case`, igual al resto del backend (R5 convenciones del repo; la regla de camelCase del skill genérico no aplica).

### Matriz de permisos (RBAC, referencia de la KB 03 que C-04+ aplica)

| Recurso | `admin` | `recepcion` | `odontologo` | Consumidor |
|---|---|---|---|---|
| Agenda (turnos CRUD) | ✓ | ✓ | agenda propia + marcar atendido | C-04 |
| Sillones/Profesionales | CRUD | lectura | lectura | C-04 |
| Pacientes | CRUD | CRUD | lectura | C-07 |
| Odontograma | lectura | lectura | CRUD | C-07 |
| Caja | CRUD + cierre | ingresos/egresos | — (bloqueado) | C-08 |
| Usuarios y roles | CRUD | — | — | change futura |

C-03 entrega el mecanismo (`require_role`); cada endpoint elegir su lista.

### D8 — Estrategia de tests (TDD, RED primero)

- **Sin DB** (`test_auth_security.py`): hash/verify bcrypt, round-trip token (claims correctos), expiración configurable `JWT_EXPIRE_MIN`, token expirado/firmado con otra clave/claims inválidos → error.
- **Servicio con fake repo** (`test_auth_service.py`): `service.autenticar_usuario` depende de un Protocol mínimo (`find_by_email(email) -> Usuario | None`); con un fake en memoria se cubren: usuario activo, `activo=False` (401), password mal, email no registrado, normalización de email. El 401 lo monta el router; el service devuelve `| None` y por eso es trivial de testear.
- **Router/E2E** (`test_auth_router.py`): `httpx.AsyncClient` con `app.dependency_overrides`:
  - `login OK/401/422`: `get_db` override con sesión real a la base de test Postgres (docker compose) ya migrada y seeded (pasos previos del checklist en tasks.md).
  - `me` 200/401 y `require_role` 403: override de `get_current_user` (o de la dependencia completa) con un `Usuario` en memoria — sin tocar DB.
- **test_structure.py**: quitar `core/security.py` + `core/deps.py` de `CORE_STUBS` (dejan de ser stubs) y agregar `auth` a `MODULOS` (los barrels `modules/auth/*` existen y pasan el contrato estructural; `schemas.py` contiene `extra="forbid"`).

## Risks / Trade-offs

- **[Login sin rate limiting]** → no hay defensa anti fuerza bruta más allá del coste de bcrypt (costo 12). Mitigación de contexto: MVP académico, red local, contraseñas de demo. Es un change futuro sin tocar este contrato.
- **[Expiración larga (720 min) sin revocación]** → un token filtrado vale hasta 12 h. Mitigaciones de esta change: R9 (el token solo viaja por header `Authorization`, nunca en querystring ni en logs) + revalidación de `activo` por request (la baja lógica corta sesiones al instante). Trade-off asumido para el MVP.
- **[Credenciales de demo en seed] (`admin123`, etc.)** → son de demostración (C-02) y el seed es tanto `SEED_DEFAULT_PASSWORD`-overridable como bloqueado con `APP_ENV=production` salvo `--force`. Riesgo acotado a la demo.
- **[Tests de integración requieren Postgres arriba]** → igual regla que C-01/C-02: `docker compose up` + `alembic upgrade head` antes de `pytest` (se lista en tasks.md como verificación previa, no como code).
- **[Mensaje genérico "Credenciales inválidas" oculta el diagnóstico]** → intencional (anti user-enumeration); para soporte queda el log interno **sin credenciales** (solo el email normalizado como identificador operativo, igual que RN-SEG-01 ya permite en logging).

## Migration Plan

- Sin migración Alembic: no se agrega ni altera ninguna columna (`Usuario` ya tiene `rol`, `password_hash`, `activo` de C-02) → R5 satisfecho vía "no hay cambio de schema".
- Deploy: agregar `pyjwt` a `pyproject.toml`, declarar `JWT_SECRET` / `JWT_EXPIRE_MIN` en el `.env` del entorno (docker compose ya pasa env a `Settings`), `docker compose up -d --build api`.
- Rollback: `docker compose down` + imagen anterior; no hay datos ni esquema que revertir.
- Seed existente: compatible tal cual (bcrypt ya es formato de `checkpw`).

## Open Questions

- Ninguna bloquea la implementación. Nota futura (C-05): dónde guarda el token el navegador (`sessionStorage` vs cookie con CSRF) es decisión del frontend y solo consume el contrato de D7.
