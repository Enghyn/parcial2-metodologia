# Guía de handoff — C-07 y C-08

> Para el compañero que cierra el MVP. Esta guía es un **cómo arrancar y qué no olvidar**.
> La fuente de verdad sigue siendo [`CHANGES.md`](../CHANGES.md), [`AGENTS.md`](../AGENTS.md) y `knowledge-base/`.
> Estado al escribir esto: `main` = `87f85ac`, C-01..C-06 archivados, 0 changes activos, 211 tests passed / 7 skipped.

---

## 1. Antes de tocar código

```powershell
git pull --rebase origin main

cd backend
alembic upgrade head          # idempotente; cwd canónico = backend/
cd ..

# baseline: la suite tiene que estar verde ANTES de empezar
cd backend
$env:DATABASE_URL="postgresql+psycopg://odonto:odonto@localhost:5432/odonto"
.venv/Scripts/python.exe -m pytest -q
cd ..
```

- Si el baseline no da **211 passed / 7 skipped**, frená y avisá: no arranques sobre rojo.
- Corré la suite **dos veces seguidas**. Si la segunda falla, hay data de test sin limpiar (ya pasó con `test_agenda_router.py`, quedó resuelto con un fixture: copiá ese patrón si creás turnos/bloqueos).

## 2. Antes de escribir código

1. Leé `AGENTS.md` (reglas duras R1–R13) y los documentos de "Leer antes" de cada change.
2. Creá el change con OpenSpec — **no** escribas specs a mano:

```
/opsx:propose C-07-clinica-odontograma
/opsx:propose C-08-caja-movimientos-balance
```

3. Implementá con TDD: primero el test que falla, después el mínimo código.

---

## 3. C-07 — `clinica-odontograma`

**Depende de:** C-05 (ya cerrado). No toca nada de C-06.
**No necesita migración** salvo que se decida agregar `deleted_at` a odontogramas (ver §5, decisión 1).

### Backend

| Archivo | Hoy | Qué hacer |
|---|---|---|
| `backend/src/app/modules/clinica/router.py` | `APIRouter()` vacío | rutas `/pacientes...` (sin prefijo `/clinica`) |
| `backend/src/app/modules/clinica/schemas.py` | vacío | schemas con `extra="forbid"` (R1) |
| `backend/src/app/modules/clinica/service.py` | vacío | casos de uso + queries con `deleted_at.is_(None)` |
| `backend/src/app/api/v1/router.py` | no monta clinica | `include_router` |

**Endpoints:**

- `GET  /api/v1/pacientes`
- `POST /api/v1/pacientes`
- `GET  /api/v1/pacientes/{id}/odontograma`
- `PUT  /api/v1/pacientes/{id}/odontograma/piezas/{pieza}` ← **upsert** del hallazgo

**Modelos ya existen** (`backend/src/app/modules/clinica/models.py`): `Paciente`, `Odontograma`, `HallazgoPieza` (CHECK FDI y CHECK de estados ya puestos). No los reescribas.

**Detalles que importan:**

- `Odontograma` es único por paciente → el GET lo crea si no existe, o devolvé 404 y que el front lo cree (elegí y documentalo).
- `HallazgoPieza` es único por `(odontograma_id, pieza)` → el PUT es update-or-insert.
- Estado válido: `sano | caries | obturacion | corona | extraccion | tratamiento_conducto` (**no** `conducto`; el CHECK manda).
- RBAC en backend con `require_role` (R8): lectura los 3 roles, escritura de pieza `odontologo`.
- No loguear diagnóstico ni datos de salud (R9).

### Frontend

| Archivo | Hoy | Qué hacer |
|---|---|---|
| `frontend/src/features/clinica/index.ts` | placeholder | exportar páginas reales |
| `frontend/src/shared/api/clinica.ts` | no existe | cliente tipado, sin `any` (R7) |
| `frontend/src/app/router.tsx` | solo `agenda` | agregar `pacientes` y `odontograma/:pacienteId` bajo `/app` |

- `/app/pacientes`: directorio + buscador.
- `/app/odontograma/:pacienteId`: grilla 4 cuadrantes, piezas 11–48, selector de estado, guardado.
- `AppLayout` no tiene navegación; si agregás links, es opcional y prolijo.

### Tests

`backend/test/test_clinica_*.py`: paciente con DNI duplicado, listado sin borrados lógicos, GET odontograma, PUT pieza nueva y pieza existente, pieza fuera de FDI → 422.

---

## 4. C-08 — `caja-movimientos-balance`

**Depende de:** C-05. **Independiente de C-07** → se puede hacer en paralelo.

### Backend

Mismos 3 stubs en `backend/src/app/modules/caja/` + montar en `api/v1/router.py`.

**Endpoints** (router con `prefix="/caja"`):

- `POST /api/v1/caja/movimientos`
- `GET  /api/v1/caja/movimientos` (filtros por fecha)
- `GET  /api/v1/caja/resumen-diario` (totales por medio de pago + balance neto)

**El modelo `MovimientoCaja` es append-only y ya está protegido** (`ImmutableLedgerMixin` en `app/db/base.py`): cualquier UPDATE o DELETE lanza `ImmutableLedgerError`. Hay tests en `backend/test/test_caja_inmutable.py`. No intentes "anular" cambiando una fila.

**Reglas que muerden:**

- **R3/RN-CJ-02**: corrección = movimiento inverso (otra fila), nunca UPDATE/DELETE.
- **R4/RN-CJ-01**: cobro sin `medio_pago` + usuario responsable → inválido.
- **R8**: `usuario_id` sale del JWT (`get_current_user`), **jamás** del body.
- `monto > 0`, `tipo ∈ {ingreso, egreso}`, `medio_pago ∈ {efectivo, transferencia, debito, credito, otro}` (CHECKs ya puestos).
- Si vinculás a turno: verificar que el turno exista y `deleted_at IS NULL`.

### Frontend

- `frontend/src/shared/api/caja.ts` (nuevo, tipado).
- `/app/caja`: modal de cobro rápido desde turno atendido, formulario de egreso, tabla del libro diario y tarjetas de balance (Efectivo / Transferencias / Tarjetas / Total del día). Montos en ARS (R10).

---

## 5. Decisiones que necesitan respuesta antes de codear

| # | Tema | Situación | Qué hacer |
|---|---|---|---|
| 1 | `deleted_at` en odontogramas | `Odontograma` y `HallazgoPieza` no tienen `deleted_at`; el alcance de C-07 pide filtrarlo | consultar: agregar `SoftDeleteMixin` + migración `0004`, o ajustar el alcance a solo `Paciente` |
| 2 | `conducto` vs `tratamiento_conducto` | `CHANGES.md` dice `conducto`, el modelo y la KB dicen `tratamiento_conducto` | usar `tratamiento_conducto` y corregir el texto de `CHANGES.md` |
| 3 | Anulación en caja | no hay columna `anulado` ni `contra_asiento_de` | contra-asiento = fila inversa; si hace falta el vínculo, migración |
| 4 | Seña (`Turno.sena_monto`) | hoy no genera movimiento de caja | definir: ingreso al reservar o recién al cobrar |
| 5 | WhatsApp (RN-G-01, 2.ª viñeta) | `adapters/whatsapp.py` sigue stub y ningún change lo asigna | definir si entra acá o queda fuera del MVP |
| 6 | Migraciones | viven en `backend/src/app/db/migrations/versions/` (última `0003`) | nueva sería `0004_*.py`; correr desde `backend/` |

---

## 6. Archivos compartidos (no pisar al otro)

| Archivo | Lo tocan |
|---|---|
| `backend/src/app/api/v1/router.py` | C-07 y C-08 |
| `backend/test/test_structure.py` (`MODULOS_SIN_STUBS`, `MODULOS_CON_RUTAS`) | C-07 y C-08 |
| `frontend/src/app/router.tsx` | C-07 y C-08 |
| `CHANGES.md` / `AGENTS.md` | ambos al cerrar |

Si van en paralelo: que uno haga los dos `include_router` y las dos rutas, o mergear esas ediciones en un solo commit.

---

## 7. Definición de terminado (por change)

- [ ] Tests nuevos en verde y suite completa en verde **dos veces seguidas**.
- [ ] `npm run lint` y `npm run build` sin errores (si tocó frontend).
- [ ] `openspec validate <change> --type change --strict` sin issues.
- [ ] Skill `business-rule-coverage-auditor` pasada (matriz de cobertura RN-*).
- [ ] `/opsx:archive <change>` → `specsUpdated: true`.
- [ ] `CHANGES.md`: estado `[x] (Completado y archivado)` + `[x]` en el árbol de dependencias.
- [ ] `AGENTS.md`: línea del roadmap a `[x] (Completado y archivado)`.
- [ ] `openspec validate --all` y `openspec validate --archived` en verde.
- [ ] Nada de `git push --force`; commits en conventional y sin co-autoría IA (R12).

---

## 8. Chuleta de comandos

```powershell
# backend (cwd = backend/)
$env:DATABASE_URL="postgresql+psycopg://odonto:odonto@localhost:5432/odonto"
.venv/Scripts/python.exe -m pytest -q
.venv/Scripts/python.exe -m pytest test/test_clinica_service.py -q   # un archivo
alembic upgrade head

# frontend (cwd = frontend/)
npm run lint
npm run build

# openspec (cwd = raíz)
openspec list --json
openspec status --change "C-07-clinica-odontograma" --json
openspec validate "C-07-clinica-odontograma" --type change --strict --json
openspec archive "C-07-clinica-odontograma" --yes --json
openspec validate --all --json
openspec validate --archived --json
```
