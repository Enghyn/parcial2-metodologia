# Tasks — C-11 ficha-clinica-avanzada

> **TDD estricto.** Backend desde `backend/`. Integración con PostgreSQL migrado y sembrado. Gobernanza CRÍTICO: no implementar hasta que un humano apruebe `proposal.md`, `design.md` y los mockups.

## 1. Safety net y RED de schemas

- [x] 1.1 Correr `python -m pytest -m "not integration" -q` y `python -m pytest -q` con base migrada; registrar la línea base y confirmar que no hay fallos previos.
- [x] 1.2 **RED**: crear `backend/test/test_clinica_avanzada_schemas.py` con tests que fallen: `extra="forbid"` en `EvolucionCreate` y `ConsentimientoCreate`; texto/versión vacíos rechazados; `autor_usuario_id` y `fecha` no declarables; `HallazgoOut` acepta `autor_usuario_id`.
- [x] 1.3 **GREEN**: implementar los schemas nuevos en `clinica/schemas.py`; verificar que los tests de 1.2 pasan y que los tests existentes de C-07 siguen verdes.

## 2. Modelos y migración 0007

- [x] 2.1 **RED**: crear `backend/test/test_clinica_avanzada_models.py` con tests que fallen: tablas `evoluciones_clinicas`, `consentimientos_informados` y `hallazgos_pieza_historial` existen; `hallazgos_pieza.autor_usuario_id` existe; ninguna tabla nueva tiene `tenant_id`; los triggers rechazan `UPDATE`/`DELETE` por SQL directo.
- [x] 2.2 Confirmar `alembic heads` y escribir `0007_ficha_clinica_avanzada.py` con `down_revision` correcto (`0006_pre_reserva_origen`), tres tablas, columna, índices, función de inmutabilidad y triggers.
- [x] 2.3 **GREEN**: implementar los modelos en `clinica/models.py`; correr `alembic upgrade head` y verificar que los tests de 2.1 pasan.
- [x] 2.4 Verificar reversibilidad: `alembic downgrade -1` y `alembic upgrade head` sin errores ni objetos huérfanos.

## 3. Evolución clínica

- [x] 3.1 **RED**: crear `test_clinica_avanzada_service.py` con casos que fallen: alta de evolución con autor del JWT; lectura ordenada por fecha descendente; paciente borrado → 404; texto vacío rechazado.
- [x] 3.2 **GREEN**: implementar `EvolucionService` en `clinica/service.py`; verificar los tests de 3.1.
- [x] 3.3 **RED**: crear `test_clinica_avanzada_router.py` con casos HTTP que fallen: `POST` 201 para odontólogo, 403 para recepción y admin, 401 sin token; `GET` 200 para los tres roles; `PUT`/`DELETE` → 405.
- [x] 3.4 **GREEN**: implementar los endpoints de evolución en `clinica/router.py` con `require_role` y autor desde el usuario inyectado; verificar 3.3.
- [ ] 3.5 **TRIANGULATE**: agregar el caso de corrección por evolución nueva (original intacta + nueva visible) y verificar.

## 4. Consentimiento informado

- [x] 4.1 **RED**: agregar a `test_clinica_avanzada_service.py` casos que fallen: alta de consentimiento con autor del JWT; versión duplicada → 409; versión nueva no pisa la anterior; paciente borrado → 404.
- [x] 4.2 **GREEN**: implementar `ConsentimientoService` con `UNIQUE(paciente_id, version)` y traducción de `IntegrityError` a 409; verificar 4.1.
- [x] 4.3 **RED**: agregar a `test_clinica_avanzada_router.py` casos HTTP: `POST` 201 solo odontólogo, 403 para recepción/admin, `GET` 200 para los tres roles, cuerpo con autor/fecha → 422.
- [x] 4.4 **GREEN**: implementar los endpoints de consentimiento en `clinica/router.py`; verificar 4.3.

## 5. Autoría y upsert con historial

- [x] 5.1 **RED**: agregar a `test_clinica_avanzada_service.py` casos que fallen: el `PUT` de pieza guarda `autor_usuario_id` del JWT; la primera versión del historial tiene `estado_anterior` nulo; una segunda actualización agrega una versión con anterior/nuevo.
- [x] 5.2 **GREEN**: modificar `OdontogramaService.upsert` para recibir el `Usuario`, completar `autor_usuario_id` y escribir `hallazgos_pieza_historial` en la misma transacción; verificar 5.1 y que los tests de C-07 siguen verdes.
- [ ] 5.3 **REFACTOR**: extraer el armado de la versión de historial y evitar duplicar la lectura del hallazgo; correr `ruff check src test`.

## 6. Historial por pieza

- [x] 6.1 **RED**: agregar a `test_clinica_avanzada_router.py` casos que fallen: `GET .../piezas/{pieza}/historial` 200 para los tres roles; pieza 19 → 422; pieza sin hallazgos → 200 con lista vacía; paciente borrado → 404; orden descendente.
- [x] 6.2 **GREEN**: implementar el endpoint y el schema `HistorialPiezaOut`; verificar 6.1.
- [x] 6.3 **PRIVACIDAD**: agregar `test_no_loguea_texto_clinico` con `caplog` sobre evolución, consentimiento y upsert; verificar que los logs no contienen texto, estados ni observaciones (R9).

## 7. Frontend — cliente de API

- [ ] 7.1 **RED**: crear `frontend/src/shared/api/clinicaAvanzada.test.ts` (o el patrón de tests puros existente) con casos que fallen para el mapeo de respuestas y errores 409/403.
- [ ] 7.2 **GREEN**: ampliar `shared/api/clinica.ts` con `listarEvoluciones`, `crearEvolucion`, `listarConsentimientos`, `crearConsentimiento`, `getHistorialPieza`; sin `any` y con tipos exportados.
- [ ] 7.3 Verificar `npx tsc --noEmit` y `npm run lint` en verde.

## 8. Frontend — ficha avanzada

- [ ] 8.1 Implementar la sección de evolución en `features/clinica/OdontogramaPage.tsx` (lista, alta solo odontólogo, estados vacío/carga/error/éxito); verificar con el test de componente o el build.
- [ ] 8.2 Implementar la sección de consentimiento (versiones, alta solo odontólogo, error 409 visible); verificar con el test o el build.
- [ ] 8.3 Implementar la sección de historial por pieza (selector, línea de tiempo, estados vacío/carga/error); verificar con el test o el build.
- [ ] 8.4 Mostrar autor y fecha del último cambio en el panel de la pieza y deshabilitar escritura para roles sin permiso; verificar manualmente con cada rol.
- [ ] 8.5 Verificar `npm run build` y que la UI usa los tokens de `design-system/tokens.css` sin colores literales nuevos.

## 9. Verificación integral

- [x] 9.1 Correr `python -m pytest -q` con PostgreSQL migrado y sembrado **dos veces seguidas**; confirmar que no queda data sucia.
- [x] 9.2 Correr `ruff check src test` en cero y `openspec validate "c-11-ficha-clinica-avanzada" --strict`.
- [x] 9.3 Correr `openspec validate --all` y confirmar 0 fallos.
- [x] 9.4 Pasar `business-rule-coverage-auditor` sobre C-11 (RN-CL-01/02, R1, R2, R5, R6, R8, R9, R10, R13) y actualizar la matriz de cobertura.

## Workflow follow-up

- Aprobar explícitamente los mockups en `mockups/` antes de aplicar (política `system-and-mockups`); actualizar `design.md` con `Approval: approved` y `Preview: rendered`.
- Implementar con TDD y actualizar los checkboxes.
- Revisión humana del design por gobernanza CRÍTICO (inmutabilidad, versionado de consentimiento y autoría).
- Archivar con `openspec archive "c-11-ficha-clinica-avanzada" -y`.
- Marcar C-11 `[x]` en `CHANGES.md` y `AGENTS.md`, y corregir la referencia a US-020 si el humano lo indica.
