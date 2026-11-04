# Matriz de trazabilidad — reglas → tests

> Generada con `business-rule-coverage-auditor` el 2026-11-04.
> Estado: ✅ cubierta · ⚠️ parcial · ❌ sin cobertura · ➖ no aplica.
> Actualizar antes de archivar un change.

| Regla | Evidencia principal | Estado |
|---|---|---|
| RN-AG-01 | `test_agenda_conflicts.py`, `test_agenda_router.py` (409) | ✅ |
| RN-AG-02 | `test_agenda_service.py::test_crear_en_hueco_libre_persiste_fin` | ✅ |
| RN-AG-03 | `test_agenda_schemas.py`, NOT NULL del modelo | ✅ |
| RN-AG-04 | `test_agenda_service.py::test_bloqueo_conflicto_en_turno` | ✅ |
| RN-AG-05 | `test_turno_estado_update_extra_forbid_y_valores` (solo catálogo) | ⚠️ |
| RN-AG-06 | `test_public_schemas.py::test_paciente_requiere_nombre_dni_telefono` | ✅ |
| RN-CL-01 | `test_clinica_service.py` (pieza 19), `test_clinica_schemas.py`, CHECK FDI | ✅ |
| RN-CL-02 | `test_clinica_router.py::test_recepcion_no_puede_editar_pieza_403` | ✅ |
| RN-CJ-01 | `test_caja_router.py` (201/422), `test_caja_schemas.py`, usuario desde JWT | ✅ |
| RN-CJ-02 | `test_caja_inmutable.py`, `test_pg_hardening.py`, `test_caja_router.py` sin PATCH/DELETE | ✅ |
| RN-CJ-03 | Seña manual aprobada; no hay deducción de saldo (decisión de C-08) | ⚠️ |
| RN-SEG-01 | `test_auth_router.py`, `test_agenda_router.py` (401/403) | ✅ |
| RN-SEG-02 | `test_soft_delete.py`, 404 de paciente borrado | ✅ |
| RN-G-01 | `frontend/test/whatsapp.test.ts` (constructor de URL) | ✅ |
| R1 | Tests de schemas auth/agenda/public/clinica | ✅ |
| R2 | `test_models_structure.py::test_ninguna_tabla_tiene_tenant_id` | ✅ |
| R3 | `test_caja_inmutable.py`, triggers de `0003`, `test_caja_router.py` sin PATCH/DELETE | ✅ |
| R4 | `test_caja_router.py` (usuario JWT, body con `usuario_id` 422) | ✅ |
| R5 | `ruff`, type hints, `test_migration_*` | ✅ |
| R6 | `test_agenda_conflicts.py`, 409 HTTP | ✅ |
| R7 | `tsc`, `eslint`, `build`; sin tests de componentes | ⚠️ |
| R8 | `test_auth_deps.py`, RBAC de agenda/clinica | ✅ |
| R9 | `test_login_fallido_no_loguea_credenciales`, `test_crear_turno_no_loguea_notas`, `test_reservar_no_loguea_datos_paciente`, `test_no_loguea_estado_ni_observacion`, `test_no_loguea_concepto_clinico` | ✅ |
| R10 | UI es-AR/ARS; sin test automatizado de textos | ⚠️ |
| R11 | Regla de proceso | ➖ |
| R12 | Regla de proceso | ➖ |
| R13 | `test_soft_delete.py`, triggers, 404 clínico | ✅ |

## Brechas conocidas

- **R7/R10**: no hay tests de componentes React ni E2E; solo `tsc`/`eslint`/`build` y tests de helpers puros.
- **RN-AG-05**: el catálogo está cubierto; las transiciones no se validan (decisión pendiente en KB 10).
- **RN-CJ-03**: la seña se registra manualmente y no hay deducción automática de saldo (decisión aprobada de C-08).
- **R9**: cubierto con `caplog` en auth/agenda/público/clínica/caja; no hay un test global de logging, pero las cinco superficies están cubiertas.

## Cómo usarla

1. Antes de archivar un change, buscar las reglas que toca.
2. Verificar que cada ✅ tenga un test concreto ejecutándose.
3. Si una regla queda ⚠️ o ❌, proponer el test o registrar la decisión de dominio.
