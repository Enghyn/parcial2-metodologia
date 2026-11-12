# Tasks

## 1. Modelos y migración

- [ ] 1.1 Crear modelos `ObraSocial`, `Convenio`, `NomencladorPractica`, `ConvenioPractica`, `PacienteObraSocial` en `backend/src/app/modules/os/models.py` y `nomenclador/models.py`, con PK UUID `gen_random_uuid()`, sin `tenant_id`, y verificar import en `app.db.registry`.
- [ ] 1.2 Crear migración Alembic `0009` (confirmar número con `alembic heads`) con las 5 tablas y FKs, y verificar `alembic upgrade head` sin errores.
- [ ] 1.3 Agregar tests de modelo (estructura, columnas, constraints) en `test/test_os_models.py` y `test/test_nomenclador_models.py`, y verificar que pasan.

## 2. Servicios y cálculo de cobertura

- [ ] 2.1 Implementar servicio de OS/convenios/afiliación en `os/service.py` y servicio de nomenclador en `nomenclador/service.py`, y verificar tests unitarios de cobertura.
- [ ] 2.2 Implementar función pura `calcular_cobertura(paciente, practica, fecha)` con tests de copago fijo, porcentaje y sin cobertura.

## 3. API y RBAC

- [ ] 3.1 Crear routers `/api/v1/os/*` y `/api/v1/nomenclador/*` con CRUD (admin) y consulta (admin/recepcion/odontologo), y verificar tests de RBAC (401/403).
- [ ] 3.2 Registrar routers en `app/api/v1/router.py` y verificar `openspec validate c-13a-os-nomenclador-cobertura --strict`.

## 4. Integración

- [ ] 4.1 Ejecutar suite no-integración y verificar verde; documentar en CHANGES.md al archivar.

## Workflow follow-up

- Archivar el change con `/opsx:archive` y marcar `[x]` en `CHANGES.md`.