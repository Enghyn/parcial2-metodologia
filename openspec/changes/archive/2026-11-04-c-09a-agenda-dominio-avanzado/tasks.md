# Tasks — C-09a agenda-dominio-avanzado

> **TDD estricto.** Backend desde `backend/`; integración con PostgreSQL migrado y sembrado.

## 1. Safety net

- [x] 1.1 Correr `pytest -m "not integration" -q` y `pytest -q` con base; registrar la línea base (esperado: 173/8/95 y 269/7).
- [x] 1.2 Releer `agenda/service.py`, `schemas.py`, `router.py` y `test_agenda_*`; no romper antisolapamiento ni RBAC.

## 2. Migración 0004

- [x] 2.1 **RED**: crear `test_migration_0004.py` que exija `revision="0004_agenda_avanzada"`, `down_revision="0003_core_data_model_hardening"`, las tres columnas, el `CHECK` con `ausente` y el `CHECK` de sobreturno con motivo.
- [x] 2.2 **GREEN**: crear `0004_agenda_avanzada.py` con `ALTER TABLE turnos` y constraints; verificar.
- [x] 2.3 **TRIANGULATE**: verificar downgrade reversible y que no toque datos existentes.
- [x] 2.4 **REFACTOR**: comentar el propósito de cada constraint; correr `alembic upgrade head --sql`.

## 3. Schemas

- [x] 3.1 **RED**: ampliar `test_agenda_schemas.py` con `ReprogramarTurno` (inicio/duración), `SobreturnoCreate` (motivo obligatorio) y `TurnoEstadoUpdate` con `ausente`.
- [x] 3.2 **GREEN**: implementar los schemas; verificar.
- [x] 3.3 **TRIANGULATE**: duración opcional, motivo vacío y estado inválido.

## 4. Servicio

- [x] 4.1 **RED**: agregar a `test_agenda_service.py` reprogramación exitosa, conflicto 409, turno atendido/cancelado 409, sobreturno con solapamiento permitido, sobreturno sin motivo 422 y ausente.
- [x] 4.2 **GREEN**: implementar `reprogramar`, `crear_sobreturno` y el catálogo `ausente`; reusar `detectar_conflicto` excluyendo el turno actual.
- [x] 4.3 **RED/GREEN**: ventana de cancelación en `public/service.py` con `cancelacion_min_horas`.
- [x] 4.4 **TRIANGULATE**: reprogramar al mismo horario, cambio de duración y override de recepción.
- [x] 4.5 **REFACTOR**: extraer validación de estado reprogramable y motivo de sobreturno; correr `ruff`.

## 5. Router y frontend

- [x] 5.1 **RED**: `test_agenda_router.py` con `PATCH /reprogramar` 200/409/404, `POST /sobreturno` 201/422/403 y `ausente` en `PATCH estado`.
- [x] 5.2 **GREEN**: implementar rutas y montar; verificar.
- [x] 5.3 Frontend: acción reprogramar, acción sobreturno (admin/recepción), `ausente` en menú y color; `tsc`, `eslint`, `build`.
- [x] 5.4 **TRIANGULATE**: reprogramación con error de UI y sobreturno sin motivo.

## 6. Verificación

- [x] 6.1 Aplicar `alembic upgrade head` en PostgreSQL y verificar constraints.
- [x] 6.2 Correr `pytest -q` dos veces; `pytest -m "not integration"`; `ruff`.
- [x] 6.3 Frontend `npm test`, `npm run lint`, `npx tsc --noEmit`, `npm run build`.
- [x] 6.4 `openspec validate "c-09a-agenda-dominio-avanzado" --strict` y `openspec validate --all`.
- [x] 6.5 Pasar `business-rule-coverage-auditor` y actualizar la matriz.

## Workflow follow-up

- Revisión humana del design (sobreturno, ventana de cancelación).
- Aplicar con TDD y actualizar checkboxes.
- Archivar con `openspec archive "c-09a-agenda-dominio-avanzado" -y`.
- Continuar con C-09b (vista semanal).
