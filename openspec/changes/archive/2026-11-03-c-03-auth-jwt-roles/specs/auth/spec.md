# Spec Delta

## Purpose

Define el contrato de autenticación del personal interno (login con JWT Bearer, verificación de token y perfil) y la autorización RBAC en el backend (`admin`, `recepcion`, `odontologo`) que toda la API privada consume desde C-04 en adelante. Cubre RN-SEG-01 (Rutas Privadas) y R8 (RBAC siempre en el backend).

## ADDED Requirements

### Requirement: Login de personal interno
La API SHALL exponer `POST /api/v1/auth/login` que reciba `email` y `password` en el cuerpo (JSON) y, ante credenciales válidas de un usuario interno existente y activo, SHALL responder `200` con un access token JWT Bearer, su tipo y su expiración en segundos. La autenticación SHALL verificar la contraseña contra su hash bcrypt y el email SHALL normalizarse (trim + minúsculas) antes de la búsqueda.

#### Scenario: Credenciales válidas
- **WHEN** se envía `POST /api/v1/auth/login` con el email y password de un usuario del seed en minúsculas
- **THEN** la API responde `200` con `access_token`, `token_type: "bearer"` y `expires_in` numérico, y el cuerpo nunca incluye `password_hash`

#### Scenario: Password incorrecto o email desconocido
- **WHEN** se envía un login con un email registrado pero password incorrecto, o con un email no registrado
- **THEN** la API responde `401` con la forma única de error y el mensaje no revela si el email o el password fue lo fallado

#### Scenario: Email con variación de forma
- **WHEN** se envía el login con un email válido pero con mayúsculas o espacios en extremos (ej. `Admin@Consultorio.com`)
- **THEN** la API lo normaliza antes de buscar el usuario y el login es exitoso igual que con la forma canónica

#### Scenario: Usuario dado de baja
- **WHEN** se envía un login con credenciales correctas de un usuario con `activo = false`
- **THEN** la API responde `401` y no emite token

#### Scenario: Cuerpo con campos extra
- **WHEN** el cuerpo del login incluye un campo no declarado (ej. `token`)
- **THEN** la API lo rechaza con `422` (schema con `extra="forbid"`, R1)

### Requirement: Access token firmado con claims de rol
El sistema SHALL emitir el access token como JWT firmado con HMAC-SHA256 usando la clave secreta `JWT_SECRET` (variable de entorno), con claims `sub` (id del usuario), `rol` (`admin` | `recepcion` | `odontologo`) y expiración `exp`. La vida del token SHALL ser configurable vía `JWT_EXPIRE_MIN` (minutos).

#### Scenario: Token con claims correctos
- **WHEN** un usuario emite login exitoso y el token se decodifica con la clave secreta de entorno
- **THEN** el payload contiene `sub` igual al id del usuario, `rol` igual al rol persistido y `exp` posterior a la emisión

#### Scenario: Expiración configurable
- **WHEN** la configuración declara `JWT_EXPIRE_MIN = 720` (default KB 08) y un usuario inicia sesión
- **THEN** el `exp` del token queda exactamente a 720 minutos de la emisión

#### Scenario: Claim de rol no falsificable
- **WHEN** se firma un token a mano con un rol distinto y una clave secreta cualquiera
- **THEN** la API lo rechaza con `401` porque la firma no verifica contra `JWT_SECRET`

### Requirement: Perfil del usuario autenticado
La API SHALL exponer `GET /api/v1/auth/me` que requiera `Authorization: Bearer <token>` y devuelva `200` con `id`, `nombre`, `email` y `rol` del usuario autenticado, sin `password_hash`. Ante token ausente, inválido o expirado, SHALL devolver `401` con la forma única de error.

#### Scenario: Perfil con token vigente
- **WHEN** el usuario autenticado envía su token Bearer a `GET /api/v1/auth/me`
- **THEN** la API responde `200` con su perfil y rol, sin exponer `password_hash`

#### Scenario: Sin header de autenticación
- **WHEN** se envía `GET /api/v1/auth/me` sin cabecera `Authorization`
- **THEN** la API responde `401` con la forma única de error

#### Scenario: Token expirado
- **WHEN** se envía a `GET /api/v1/auth/me` un token firmado cuyo `exp` ya venció
- **THEN** la API responde `401`

#### Scenario: Token inválido
- **WHEN** se envía a `GET /api/v1/auth/me` un Bearer token que no es un JWT verificable con `JWT_SECRET`
- **THEN** la API responde `401`

### Requirement: Revalidación de baja del usuario en token vigente
El sistema SHALL revalidar, en cada request cuyo token se procesa, que el usuario resuelto por `sub` exista y esté `activo`; si está dado de baja, SHALL rechazar con `401` aunque el token siga vigente.

#### Scenario: Token de usuario recién dado de baja
- **WHEN** un usuario queda `activo = false` y todavía envía su token vigente a un endpoint protegido
- **THEN** la API responde `401` (el token no vale por sí solo; la identidad se revalida contra la base)

### Requirement: Dependencia de rol para autorización RBAC
El sistema SHALL proveer una dependencia reutilizable de FastAPI (`Depends`) que reciba los roles admitidos y SHALL declararse en cada endpoint protegido de la API interna: los roles válidos son `admin`, `recepcion` y `odontologo`. Un token auténtico cuyo `rol` no está entre los admitidos SHALL recibir `403` con la forma única de error (`code: "forbidden"`), sin tocar la lógica del endpoint.

#### Scenario: Rol admitido
- **WHEN** un endpoint declara la dependencia con roles `("admin", "recepcion")` y el emisor tiene token vigente con `rol: recepcion`
- **THEN** la request avanza a la lógica del endpoint con el usuario resuelto disponible vía inyección

#### Scenario: Rol no admitido
- **WHEN** un endpoint declara la dependencia con roles `("admin","recepcion")` y el emisor tiene token vigente con `rol: odontologo`
- **THEN** la API responde `403` con `error.code: "forbidden"` y el código del módulo no se ejecuta

#### Scenario: Composición en endpoint futuro
- **WHEN** C-04 agrega un endpoint de turnos con la dependencia de rol en su firma de FastAPI
- **THEN** la dependencia funciona sin código extra en el nuevo módulo (es reutilizable por diseño, R8)

### Requirement: RBAC siempre en el backend
La autorización SHALL cumplirse SIEMPRE en el backend: cualquier endpoint de la API interna SHALL validar token y rol en el servidor antes de procesar la request y nunca SHALL confiar en el frontend, que solo oculta o deshabilita la UI de manera cosmética (R8).

#### Scenario: Ignorado el frontend
- **WHEN** un cliente directo (curl, script) llama a un endpoint privado sin token o con rol insuficiente
- **THEN** la API responde `401` o `403` respectivamente, porque la dependencia de autenticación/autorización está resuelta en el servidor

### Requirement: Forma única de error de auth
Todos los fallos de autenticación y autorización SHALL responder con la forma única de error `{error: {code, message}}` del proyecto y el mapa de estados fijos: `401` para credenciales o token inválidos y `403` para rol insuficiente.

#### Scenario: Cuerpo consistente
- **WHEN** cualquier escenario de esta capability termina en `401` o `403`
- **THEN** el cuerpo tiene exactamente la forma `{error: {code, message}}` definida en `core/errors.py`, sin nombres de librería ni stack traces
