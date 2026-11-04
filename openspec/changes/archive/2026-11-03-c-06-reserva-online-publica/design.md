# Design — C-06: reserva-online-publica

## Context

C-04 dejó `TurnoService`, los helpers puros `solapamiento`/`detectar_conflicto` y los endpoints internos de agenda; C-05 dejó la SPA con router público (`/reservar/:slug`, `/p/turno/:token`) y el cliente API tipado. `Paciente` (con `dni` UNIQUE y `deleted_at`) y `Turno` (con `token_publico` UNIQUE) ya existen en el esquema; no se requiere migración (R5). La duración no proviene de un catálogo (KB 10): el frontend ofrece una lista estática de prestaciones con duración y el backend recibe `duracion_min`.

Constraints: endpoints públicos sin auth pero con validación estricta (R1/R8/RN-SEG-01); no duplicar la lógica de antisolapamiento (R6); no datos sensibles en URLs/logs (R9); borrado lógico (R13); superficies en es-AR y montos en ARS (R10).

## Goals / Non-Goals

**Goals:**
- Portal público end-to-end: disponibilidad → reserva → confirmación → cancelación, reusando `TurnoService`.
- Cálculo de slots determinista y testeable sin DB para la parte pura.
- Find-or-create de paciente por DNI sin duplicados.
- Enlace Click-to-Chat de WhatsApp (RN-G-01) en frontend.

**Non-Goals:**
- Rate limiting / anti-abuso (fuera de alcance; anotado como pregunta abierta futura).
- Catálogo de prestaciones persistido (KB 10, fase 2): lista estática en frontend.
- Envío real de notificaciones WhatsApp por API (solo Click-to-Chat).
- Máquina de estados estricta del turno (se mantiene el catálogo de C-04).
- Scoping de disponibilidad por consultorio multi-sillón más allá de 2–3 sillones.

## Decisions

### D1 — Módulo backend `modules/public/`

Nuevo módulo `backend/src/app/modules/public/` con `schemas.py`, `service.py`, `router.py`. Se monta en `app/api/v1/router.py` como `public.router` con prefix `/public` (rutas finales `/api/v1/public/*`). No se modifica `modules/agenda`; se reusa `TurnoService`, `solapamiento` y `detectar_conflicto` importándolos. Motivo: mantener el límite de contexto (público vs interno) y evitar inflar el router de agenda. Alternativa descartada: agregar endpoints públicos dentro de `agenda/router.py` (mezcla RBAC público/privado en el mismo router, riesgo de confusión).

### D2 — Servicio `PublicReservaService`

```python
class PublicReservaService:
    def __init__(self, db: Session): ...
    def disponibilidad(self, fecha, duracion_min, profesional_id=None) -> list[SlotOut]: ...
    def reservar(self, datos: ReservaCreate) -> Turno: ...   # 409/422 vía HTTPException
    def obtener_por_token(self, token: UUID) -> Turno: ...  # 404
    def cancelar_por_token(self, token: UUID) -> Turno: ...  # 409/404
```

`disponibilidad` implementa el algoritmo de slots. `reservar` hace find-or-create de paciente, valida el hueco reusando `detectar_conflicto` (409 si ocupado) y delega la creación a `TurnoService.crear` o replica su persistencia (mismo patrón). Para evitar duplicar la persistencia, `reservar` construye un `TurnoCreate` y llama a `TurnoService(self.db).crear(datos)`; así la validación antisolapamiento vive en un único lugar (R6). Se añade un método `TurnoService.crear` ya existente; no se modifica.

### D3 — Algoritmo de slots (pure + DB)

Para una fecha `D`, duración `dur`, profesional opcional `P`:

1. Jornada laboral `[start, end)` con defaults 08:00–20:00; grilla de inicio cada `grid` min (default 30). Un slot de duración `dur` cabe si `inicio + dur <= end`.
2. Profesionales candidatos: si `P` se provee, `[P]` (activo, no borrado); si no, todos los `Profesional` activos/no borrados.
3. Sillones candidatos: todos los `Sillon` activos/no borrados.
4. Para cada profesional `prof` y cada inicio candidato:
   a. Consultar turnos activos del día para ese profesional y bloqueos; para cada sillón, verificar que no haya turno activo ni bloqueo solapado para el profesional o el sillón (reuso `solapamiento`).
   b. Tomar el primer sillón libre; si existe, emitir `Slot(inicio, profesional_id=prof.id, sillon_id=sillon.id)`.
5. Ordenar por `inicio`, luego `profesional_id`.

Helpers puros extraídos para TDD sin DB:

```python
def generar_inicios(start: time, end: time, grid_min: int, duracion_min: int) -> list[time]: ...
def slot_libre(turnos, bloqueos, sillon_id, profesional_id, inicio, fin) -> bool: ...  # reusa solapamiento
```

`generar_inicios` es puro. `slot_libre` es puro (recibe iterables). `disponibilidad` orquesta las consultas a DB y llama a los helpers.

Configuración por env (con defaults):
- `PUBLIC_SLOT_START` (default `"08:00"`)
- `PUBLIC_SLOT_END` (default `"20:00"`)
- `PUBLIC_SLOT_GRID_MIN` (default `30`)

Se agregan a `Settings` con defaults; se parsean a `time` en el servicio con validación (si inválidos, fallback a defaults y log warning).

### D4 — Paciente find-or-create por DNI

En `reservar`, antes de crear el turno:

```python
paciente = db.scalar(select(Paciente).where(Paciente.dni == datos.paciente.dni, Paciente.deleted_at.is_(None)))
if paciente is None:
    # si existe soft-deleted, reactivar
    paciente = db.scalar(select(Paciente).where(Paciente.dni == datos.paciente.dni))
    if paciente is not None:
        paciente.deleted_at = None
    else:
        paciente = Paciente(nombre=..., dni=..., telefono=..., email=...)
        db.add(paciente); db.flush()
# actualizar contacto
if datos.paciente.telefono: paciente.telefono = datos.paciente.telefono
if datos.paciente.email is not None: paciente.email = datos.paciente.email
db.flush()
```

Luego se construye `TurnoCreate(paciente_id=paciente.id, ...)` y se llama a `TurnoService.crear`. Se commitea en `TurnoService.crear` (que hace commit). Riesgo: si `TurnoService.crear` falla por 409, el paciente ya se flusheó en la misma transacción; como `crear` hace su propio commit solo al éxito, un fallo anterior no commitea el paciente (la sesión no commiteó). Pero flusheamos en la misma sesión sin commit; si `crear` lanza HTTPException antes de commit, el paciente no persiste. Bueno. Sin embargo `crear` hace `db.commit()` al final; si el slot se ocupó concurrentemente, el 409 ocurre antes del commit, por lo que no se persiste el paciente nuevo. Aceptable.

### D5 — Cancelación por token

`cancelar_por_token`:
1. Buscar `Turno` por `token_publico == token` y `deleted_at IS NULL`. Si no existe → 404 `Turno no encontrado`.
2. Si `estado` not in (`reservado`, `confirmado`) → 409 `No se puede cancelar un turno en estado {estado}`.
3. `turno.estado = "cancelado"`; commit; refresh; return.

No se borra físicamente (R13). Se reusa el mismo mensaje shape.

### D6 — Vista pública por token

`obtener_por_token` busca por `token_publico` y `deleted_at IS NULL`. Mapea a `PublicTurnoOut` con nombres resueltos (paciente.nombre, profesional.nombre, sillon.nombre) y sin IDs/DNI/teléfono. Si no existe → 404.

### D7 — Schemas públicos (R1)

```python
class PacientePublicoIn(BaseModel):
    model_config = ConfigDict(extra="forbid")
    nombre: str = Field(min_length=1, max_length=100)
    dni: str = Field(min_length=1, max_length=20)
    telefono: str = Field(min_length=1, max_length=30)
    email: str | None = Field(default=None, max_length=150)

class ReservaCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    prestacion: str = Field(min_length=1, max_length=150)
    duracion_min: int = Field(gt=0)
    inicio: datetime
    profesional_id: UUID
    sillon_id: UUID
    paciente: PacientePublicoIn
    @model_validator(mode="before"): normalizar inicio a UTC

class SlotOut(BaseModel):
    model_config = ConfigDict(extra="forbid")
    inicio: datetime
    profesional_id: UUID
    sillon_id: UUID

class DisponibilidadQuery(BaseModel): ... # o params directos en router con Query

class PublicTurnoOut(BaseModel):
    model_config = ConfigDict(extra="forbid", from_attributes=False)
    token: UUID
    prestacion: str
    inicio: datetime
    fin: datetime
    duracion_min: int
    estado: str
    paciente_nombre: str
    profesional_nombre: str
    sillon_nombre: str
```

La disponibilidad se expone como query params (`fecha`, `duracion_min`, `profesional_id`) en el router, validados por `Query`. El schema `ReservaCreate` cubre el body.

### D8 — RBAC / seguridad

Los endpoints públicos no usan `Depends(get_current_user)` ni `require_role`. La validación es por schema (R1) y por constraints de campo. R8 se cumple: no hay permisos que delegar al frontend. R9: el token en la URL es opaco y aceptable; nunca se loguean DNI/teléfono/email (el logger ya redacta esas claves). El handler de errores no expone stack traces.

### D9 — Frontend: módulo `features/reserva-publica/`

Estructura:
```
frontend/src/features/reserva-publica/
├── index.ts
├── types.ts
├── api.ts            # funciones tipadas: getDisponibilidad, reservar, getTurnoPublico, cancelarTurnoPublico
├── ReservarWizard.tsx
├── steps/
│   ├── PasoPrestacion.tsx
│   ├── PasoProfesional.tsx
│   ├── PasoHorario.tsx
│   └── PasoDatos.tsx
├── TurnoPublicoPage.tsx   # o en app/pages.tsx
├── WhatsappButton.tsx
└── store.ts          # Zustand: paso actual, selecciones, paciente
```

Se reutiliza `request<T>` de `shared/api/client.ts` (no envía Bearer cuando no hay token; ya soportado).

Rutas: `/reservar` (wizard) y `/p/turno/:token` (confirmación). El router ya declara `/reservar/:slug` y `/p/turno/:token`; se ajusta a `/reservar` (sin slug) y se mantiene `/p/turno/:token`. Cambio menor en `router.tsx`.

Estado del wizard en Zustand (o useState local). Se propone Zustand para persistir entre pasos; alternativa useState en el componente padre. Se usará useState en `ReservarWizard` con un estado tipado para simplicidad y evitar store global. (Decisión: useState; sin nueva dependencia.)

Catálogo de prestaciones estático en `catalogos.ts` (reuso del patrón de agenda): lista de `{ nombre, duracion_min }` (ej. "Consulta diagnóstica" 30, "Limpieza" 30, "Extracción" 60, "Endodoncia" 60, "Ortodoncia control" 30). Profesionales y sillones se obtienen... en público no hay endpoint de catálogos internos (protegidos). Para el paso 2 "profesional", el backend de disponibilidad requiere `profesional_id` opcional; para listar profesionales en el portal público se necesita un endpoint público de profesionales o se oculta la selección. Decisión: agregar `GET /api/v1/public/profesionales` (solo id+nombre) y `GET /api/v1/public/sillones` no es necesario (sillón se asigna internamente). Para simplificar, el wizard ofrece "Cualquiera disponible" por defecto y una lista opcional de profesionales obtenida vía endpoint público mínimo. Se agrega `GET /api/v1/public/profesionales` (lista de `{id, nombre}` activos). Esto es un endpoint público adicional documentado.

WhatsApp: `WhatsappButton` construye la URL:
```ts
const telefono = (import.meta.env.VITE_WHATSAPP_CONSULTORIO ?? "").replace(/\D/g, "");
const mensaje = encodeURIComponent(`Hola, confirmo mi turno: ${prestacion} el ${fecha} a las ${hora} con ${profesional}.`);
const url = `https://wa.me/${telefono}?text=${mensaje}`;
```
Se abre con `window.open(url, "_blank", "noopener,noreferrer")` o `<a target="_blank" rel="noopener noreferrer">`. Si no hay teléfono configurado, el botón se deshabilita con tooltip. Defaults: documentar `VITE_WHATSAPP_CONSULTORIO` (ej. `5491100000000`) como supuesto de demo.

### D10 — Config y env

Backend `Settings` agrega:
- `public_slot_start: str = "08:00"`
- `public_slot_end: str = "20:00"`
- `public_slot_grid_min: int = 30`

Frontend env (Vite): `VITE_WHATSAPP_CONSULTORIO`. Backend env (opcional, para logs): `WHATSAPP_CONSULTORIO` (teléfono receptor) documentado como supuesto; no se usa en el backend salvo logs. Se agrega al `.env.example`.

### D11 — Sin migración Alembic

No cambia el esquema (R5). `token_publico` ya existe; la cancelación solo actualiza `estado`. Se documenta en tasks como "verificar `alembic current` al día; no generar migración".

### D12 — Errores

Reusa la forma única `{error:{code,message}}`. Mensajes:
- 409 disponibilidad/reserva: `Conflicto de agenda: el sillón está ocupado en ese horario` / `...profesional...` / `...rango bloqueado` (reuso mensajes de C-04).
- 409 cancelación: `No se puede cancelar un turno en estado {estado}`.
- 404: `Turno no encontrado`.
- 422: validación pydantic.

### D13 — TDD

- Backend RED-first: tests para `generar_inicios`, `slot_libre` (sin DB) y `PublicReservaService` integración (disponibilidad, reservar, obtener, cancelar) contra Postgres, siguiendo el patrón de C-04.
- Frontend: verificación por `tsc --noEmit` + `eslint` + `vite build`; smoke opcional con `playwright-cli`.

### D14 — Component tree (frontend)

```
ReservarWizard (estado: paso, prestacion, profesionalId|null, slot:{inicio,profesional_id,sillon_id}, paciente)
├── PasoPrestacion (lista estática)
├── PasoProfesional (lista de /public/profesionales + "Cualquiera")
├── PasoHorario (calendario fecha + grid de slots desde /public/disponibilidad)
└── PasoDatos (form nombre/DNI/teléfono/email) → submit → navigate /p/turno/:token

TurnoPublicoPage
├── datos del turno
├── WhatsappButton
└── botón cancelar
```

## Risks / Trade-offs

- [Condición de carrera entre disponibilidad y reserva] → dos pacientes podrían ver el mismo slot; la reserva valida con `TurnoService.crear` y responde 409 si se ocupó. Mitigación: transacción única + revalidación (R6). Aceptable para MVP.
- [Jornada laboral fija] → profesionales con horarios distintos no se modelan; se asume 08:00–20:00 para todos. Mitigación: documentado como supuesto; configurable globalmente por env.
- [Lista estática de prestaciones] → no persistida; si cambia la duración, hay que actualizar el frontend. Mitigación: KB 10 fase 2.
- [Teléfono del consultorio en frontend] → expuesto en bundle (VITE_*); aceptable para demo. Mitigación: documentar.
- [Endpoint público de profesionales] → expone nombres de profesionales (no sensibles). Aceptable.
- [Sin rate limiting] → abuso posible; fuera de alcance (pregunta abierta futura).
- [Find-or-create con soft-delete] → si un paciente fue borrado lógicamente, se reactiva; documentado.

## Migration Plan

- Sin migración Alembic (sin cambio de esquema; R5 satisfecho por "no hay cambio de schema").
- Deploy: crear módulo `public`, montar router, agregar endpoints públicos de profesionales, actualizar frontend, actualizar `.env.example`.
- Rollback: revertir código; no hay datos ni esquema que revertir. Los turnos creados por el portal quedan en la base (estado `reservado`) y son gestionables por la agenda interna.

## Open Questions

- Rate limiting / anti-spam en endpoints públicos: fuera de alcance para el MVP académico; si se requiere, agregar middleware o dependencia en una change futura.
- Grilla de slots: fija a 30 min globalmente; si se requiere por profesional, agregar `duracion_slot_min` a `Profesional` (migración futura, R5).
- Teléfono receptor de WhatsApp: si se prefiere centralizar en backend, agregar endpoint `GET /api/v1/public/config` que exponga `whatsapp_consultorio`; por ahora se usa env de frontend (supuesto documentado).
- Cancelación: se permite en estados `reservado` y `confirmado`; si se requiere motivo, agregar campo `motivo_cancelacion` (migración futura).