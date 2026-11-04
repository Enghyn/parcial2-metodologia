# Design — C-04: agenda-servicio-antisolapamiento

## Context

C-02 ya dejó `turnos`, `bloqueos`, `sillones`, `profesionales` y `pacientes` con sus índices (`ix_turnos_sillon_inicio_fin`, `ix_turnos_profesional_inicio_fin`), la restricción `ck_turnos_fin_coherente` y los triggers de borrado lógico. C-03 dejó `get_current_user` / `require_role` y la forma única de error `{error:{code,message}}`. Los barrels `modules/agenda/{schemas,service,router}.py` son stubs `TODO(C-04)`; `models.py` ya es código real. No hay catálogo `Prestacion` (KB 10): la duración se carga manualmente vía `duracion_min`.

## Goals / Non-Goals

**Goals:**
- Capa de servicios `TurnoService` reutilizable por C-05/C-06 con anti-solapamiento cruzado (RN-AG-01), exclusión de cancelados y de borrados lógicos, cálculo de `fin` (RN-AG-02) y bloqueos como ocupación (RN-AG-04).
- Endpoints HTTP internos con RBAC backend (R8) y contrato de errores es-AR.
- Suite TDD: helpers puros testeables sin DB + integración contra Postgres.

**Non-Goals:**
- Catálogo de prestaciones / duración automática por prestación (KB 10, fase 2).
- Máquina de estados estricta del turno (cualquier valor del catálogo es aceptado en C-04; C-05 refina).
- Scoping "agenda propia" del odontólogo (deferido a C-05; C-04 permite listar a los 3 roles).
- Bloqueo con `deleted_at` o soft-delete (R13 no protege `Bloqueo`; se borra físicamente).
- Exclusión a nivel DB (constraint `EXCLUDE`): la validación vive en la capa de servicios (DD-03).

## Decisions

### D1 — Layout del módulo (espejo de auth/clinica)

```
backend/src/app/modules/agenda/
├── models.py      # existente, sin cambios (Turno, Sillon, Profesional, Bloqueo, ESTADOS_TURNO)
├── schemas.py     # TurnoCreate, TurnoEstadoUpdate, TurnoOut, BloqueoCreate, BloqueoOut
├── service.py     # helpers puros + TurnoService (Session)
└── router.py      # /turnos, /bloqueos
```

`app/api/v1/router.py` monta `agenda.router` junto a `auth.router`.

### D2 — Helpers puros de solapamiento (testeables sin DB)

```python
def solapamiento(inicio_a, fin_a, inicio_b, fin_b) -> bool:
    # fórmula exacta RN-AG-01
    return inicio_a < fin_b and fin_a > inicio_b
```

```python
def detectar_conflicto(
    turnos: Iterable[Turno],
    bloqueos: Iterable[Bloqueo],
    sillon_id, profesional_id, inicio, fin,
) -> str | None:
    # devuelve None si libre, o el motivo ("sillon" | "profesional" | "bloqueo")
```

`TurnoService` usa estos helpers sobre los registros activos consultados por recurso y rango. Esto permite TDD RED sin base de datos.

### D3 — Algoritmo de consulta de conflictos

Para un turno nuevo `(sillon_id, profesional_id, inicio, fin)`:

1. Consultar turnos activos (`deleted_at IS NULL`, `estado != 'cancelado'`) donde `(sillon_id = nuevo.sillon_id OR profesional_id = nuevo.profesional_id)` y `inicio < fin_nuevo AND fin > inicio_nuevo`.
2. Si existe alguno con `sillon_id == nuevo.sillon_id` → conflicto "sillón".
3. Si existe alguno con `profesional_id == nuevo.profesional_id` → conflicto "profesional".
4. Consultar bloqueos activos (`deleted_at` no aplica; todos los existentes) donde `(sillon_id = nuevo.sillon_id OR profesional_id = nuevo.profesional_id)` y `desde < fin_nuevo AND hasta > inicio_nuevo` → conflicto "bloqueo".
5. Si no hay conflictos, calcular `fin = inicio + duracion_min`, persistir y commitear.

El orden de mensajes prioriza sillón > profesional > bloqueo. El check y el insert ocurren en la misma sesión/transacción; no se garantiza aislamiento serializable (riesgo documentado).

### D4 — Interfaz de `TurnoService`

```python
class TurnoService:
    def __init__(self, db: Session): ...
    def listar(self, fecha=None, profesional_id=None, sillon_id=None) -> list[Turno]: ...
    def crear(self, datos: TurnoCreate) -> Turno: ...            # 409/422 vía HTTPException
    def cambiar_estado(self, turno_id: UUID, estado: str) -> Turno: ...  # 404 si no existe/borrado
    def crear_bloqueo(self, datos: BloqueoCreate) -> Bloqueo: ...
    def eliminar_bloqueo(self, bloqueo_id: UUID) -> None: ...    # 404 si no existe
```

El router instancia `TurnoService(db)` y traduce excepciones a HTTP. Los helpers puros viven en el mismo módulo para reuso por C-06.

### D5 — `Bloqueo`: sin migración nueva

El modelo y la tabla `bloqueos` de C-02 ya existen y cubren el alcance (id, sillon_id, profesional_id, desde, hasta, motivo, timestamps; check `sillon OR profesional`, `hasta > desde`, motivo no vacío). `Bloqueo` no implementa `SoftDeleteMixin` y no tiene trigger de borrado físico: R13 solo protege `Paciente`/`Turno`/`Profesional`/`Sillon`, por lo que `DELETE /api/v1/bloqueos/{id}` borra la fila físicamente (permitido). No se agrega migración Alembic en C-04; R5 se satisface vía "sin cambio de esquema".

### D6 — Schemas (R1: `extra="forbid"`)

```python
class TurnoCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    paciente_id: UUID
    profesional_id: UUID
    sillon_id: UUID
    prestacion: str = Field(min_length=1, max_length=150)
    inicio: datetime
    duracion_min: int = Field(gt=0)
    sena_monto: Decimal = Field(default=Decimal("0.00"), ge=0)
    notas: str | None = None

class TurnoEstadoUpdate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    estado: Literal["reservado","confirmado","presente","atendido","cancelado"]

class TurnoOut(BaseModel):
    model_config = ConfigDict(extra="forbid", from_attributes=True)
    id: UUID; paciente_id: UUID; profesional_id: UUID; sillon_id: UUID
    prestacion: str; inicio: datetime; fin: datetime; duracion_min: int
    estado: str; token_publico: UUID; sena_monto: Decimal; notas: str | None
    created_at: datetime; updated_at: datetime

class BloqueoCreate(BaseModel):
    model_config = ConfigDict(extra="forbid")
    sillon_id: UUID | None = None
    profesional_id: UUID | None = None
    desde: datetime
    hasta: datetime
    motivo: str = Field(min_length=1)
    # validators: al menos un recurso; hasta > desde

class BloqueoOut(BaseModel):
    model_config = ConfigDict(extra="forbid", from_attributes=True)
    id: UUID; sillon_id: UUID | None; profesional_id: UUID | None
    desde: datetime; hasta: datetime; motivo: str
    created_at: datetime; updated_at: datetime
```

Fechas naive se normalizan a UTC en un `model_validator(mode="before")` para evitar rechazos por zona horaria.

### D7 — RBAC por endpoint

| Endpoint | admin | recepcion | odontologo |
|---|---|---|---|
| `GET /turnos` | ✓ | ✓ | ✓ |
| `POST /turnos` | ✓ | ✓ | ✗ (403) |
| `PATCH /turnos/{id}/estado` | ✓ | ✓ | ✓ |
| `POST /bloqueos` | ✓ | ✓ | ✗ (403) |
| `DELETE /bloqueos/{id}` | ✓ | ✓ | ✗ (403) |

Patrón: `Depends(require_role(...))` en la firma (R8), igual que auth. `GET /turnos` y `PATCH .../estado` inyectan el usuario vía `Annotated[Usuario, Depends(require_role(...))]`; los de solo admin/recepcion usan `dependencies=[Depends(require_role("admin","recepcion"))]`.

### D8 — Contrato de errores (es-AR)

| Caso | HTTP | `error.code` | `error.message` |
|---|---|---|---|
| Solapamiento de sillón | 409 | `conflict` | `Conflicto de agenda: el sillón está ocupado en ese horario` |
| Solapamiento de profesional | 409 | `conflict` | `Conflicto de agenda: el profesional está ocupado en ese horario` |
| Rango bloqueado | 409 | `conflict` | `Conflicto de agenda: el rango está bloqueado` |
| Turno/bloqueo inexistente o borrado | 404 | `not_found` | `Turno no encontrado` / `Bloqueo no encontrado` |
| Cuerpo inválido / campo extra | 422 | `unprocessable_entity` | (validación pydantic) |
| Sin token / token inválido | 401 | `unauthorized` | (mensajes de auth D7) |
| Rol insuficiente | 403 | `forbidden` | `Rol insuficiente` |

### D9 — Registro en `test_structure.py`

- Agregar `agenda` a `MODULOS_CON_RUTAS` (su router deja de estar vacío).
- Agregar `agenda` a `MODULOS_SIN_STUBS` (schemas/service/router dejan de ser stubs TODO).
- `agenda` ya está en `MODULOS_CON_MODELOS`, por lo que `models.py` no se exige como stub.

### D10 — TDD y estructura de tests

- `backend/test/test_agenda_conflicts.py` (o sección en service tests): RED primero para `solapamiento` y `detectar_conflicto` (sin DB).
- `backend/test/test_agenda_service.py`: integración contra Postgres (patrón auth) para `TurnoService` (crear/listar/cambiar estado/bloqueos).
- `backend/test/test_agenda_router.py`: HTTP real con `httpx.AsyncClient` + `dependency_overrides`, cubriendo los 5 escenarios obligatorios de CHANGES (201, 409 sillón, 409 profesional, éxito mismo horario distinto recurso, éxito sobre cancelado) + RBAC 401/403 + 404 + 422.

Cada grupo de tareas en `tasks.md` sigue RED → GREEN.

## Risks / Trade-offs

- **[Condición de carrera entre check e insert]** → dos requests concurrentes podrían pasar el check y solaparse. Mitigación: transacción única por request + validación en capa de servicios (DD-03); para el MVP académico se acepta. Un constraint `EXCLUDE USING gist` sería la defensa en profundidad futura (baseline ya habilita `btree_gist`).
- **[Zonas horarias]** → clientes pueden enviar datetimes naive. Mitigación: normalización a UTC en el schema (D6).
- **[Tests de integración requieren Postgres]** → igual regla que C-01/C-02/C-03: `docker compose up` + `alembic upgrade head` + `python -m app.db.seed` antes de `pytest`; los tests de helpers puros corren sin DB.
- **[Bloqueo sin soft-delete]** → un `DELETE` físico es irreversible. Mitigación: R13 no protege `Bloqueo` y el MVP permite recrear bloqueos; si se requiere auditoría, agregar `deleted_at` + migración en una change futura.
- **[Mensajes 409 distintos por motivo]** → los tests que asserten mensaje exacto deben usar los de D8; si el implementador simplifica a un solo mensaje, actualizar D8 y los tests juntos.

## Migration Plan

- Sin migración Alembic (sin cambio de esquema; R5 satisfecho por "no hay cambio de schema").
- Deploy: implementar los barrels, montar el router en `api/v1/router.py`, actualizar `test_structure.py`, correr `pytest`.
- Rollback: revertir el código; no hay datos ni esquema que revertir.

## Open Questions

- Ninguna bloquea la implementación. Nota para C-05: el scoping "agenda propia" del odontólogo y la máquina de estados estricta se refinan ahí. Nota para C-06: `TurnoService.detectar_conflicto` y los helpers puros se reusan para calcular huecos públicos.