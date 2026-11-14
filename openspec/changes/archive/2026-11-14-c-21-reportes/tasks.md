# Tasks — C-21 reportes

Orden TDD: cada grupo escribe primero la prueba que falla, luego la implementación y deja sus pruebas y documentación propias. Gobernanza MEDIO: no se empieza a implementar hasta que un humano apruebe las decisiones abiertas de `design.md` y los mockups de UI.

## 1. Schemas Pydantic (R1)

- [x] 1.1 Crear `OcupacionFiltros`, `OcupacionSillonOut`, `OcupacionProfesionalOut`, `OcupacionOut` con `extra="forbid"` y `Literal` de estados de turno. Verificación: `test_reportes_schemas.py` cubre campo extra, fechas y estado inválido.
- [x] 1.2 Crear `FacturacionMedioOut`, `FacturacionOSOut`, `FacturacionOut` con `extra="forbid"` y `monto >= 0`. Verificación: `test_reportes_schemas.py` en verde.
- [x] 1.3 Crear `AusentismoOut`, `AusentismoTurnoOut` con `extra="forbid"`. Verificación: `test_reportes_schemas.py` en verde.
- [x] 1.4 Crear `ReporteRangoIn` (validador `desde <= hasta`) con `extra="forbid"`. Verificación: `test_reportes_schemas.py` cubre desde posterior a hasta (422).

## 2. Servicio de reportes (solo lectura)

- [x] 2.1 Implementar `reporte_ocupacion(desde, hasta, profesional_id, sillon_id)` sobre `Turno`: conteos por estado, tasa de ocupación y horas bloqueadas. Verificación: `test_reportes_ocupacion_service.py` cubre rango con turnos, rango vacío y filtro por profesional.
- [x] 2.2 Implementar `reporte_facturacion(desde, hasta)` sobre `MovimientoCaja` tipo ingreso, agrupado por `medio_pago` y desglose por OS (afiliación vigente C-13a; sin afiliación → "sin OS"). Verificación: `test_reportes_facturacion_service.py` cubre por medio, por OS y paciente sin afiliación.
- [x] 2.3 Implementar `reporte_ausentismo(desde, hasta)` sobre `Turno`: cancelados, no presentados, recuperados (heurística por paciente) y tasa. Verificación: `test_reportes_ausentismo_service.py` cubre ausentismo, tasa cero y rango sin turnos.
- [x] 2.4 Implementar default de rango (últimos 30 días ART) y validación `desde <= hasta` (422). Verificación: pruebas de default y de rango invertido.

## 3. Routers y RBAC (R8)

- [x] 3.1 Montar `GET /api/v1/reportes/ocupacion` y variante `.../export.csv` con `require_role(admin, recepcion)`. Verificación: `test_reportes_ocupacion_router.py` cubre 401, 403 de `odontologo`, 200/422.
- [x] 3.2 Montar `GET /api/v1/reportes/facturacion` y variante `.../export.csv` con `require_role(admin, recepcion)`. Verificación: `test_reportes_facturacion_router.py` cubre 401/403/200/422.
- [x] 3.3 Montar `GET /api/v1/reportes/ausentismo` y variante `.../export.csv` con `require_role(admin, recepcion)`. Verificación: `test_reportes_ausentismo_router.py` cubre 401/403/200/422.
- [x] 3.4 Lectura propia del odontólogo (ocupación filtrada por su `profesional_id`) si se confirma en design; caso contrario 403. Verificación: router y service.
- [x] 3.5 Registrar los routers en `api/v1/router.py` y actualizar `test_structure.py`. Verificación: `python -m pytest test/test_structure.py -q`.

## 4. Export CSV es-AR

- [x] 4.1 Reutilizar el formateador CSV de C-12 (BOM UTF-8, separador `;`, coma decimal, `dd/mm/aaaa`, escape de campos). Verificación: `test_reportes_csv.py` cubre acentos, comillas, punto y coma y montos.
- [x] 4.2 Implementar `GET /reportes/{reporte}/export.csv` para los tres reportes con `Content-Disposition: attachment`. Verificación: `test_reportes_export_router.py` valida encabezados, filas y tipo de contenido.
- [x] 4.3 Verificar R9 y RBAC: el CSV no contiene DNI, diagnósticos, hallazgos ni tokens; `odontologo` recibe 403 y sin token 401. Verificación: aserciones explícitas de ausencia en `test_reportes_export_router.py`.

## 5. Mockups y aprobación (gate de política `system-and-mockups`)

- [x] 5.1 Crear `mockups/README.md` y los HTML `ocupacion.html`, `facturacion.html`, `ausentismo.html`, importando `design-system/tokens.css` y `brand.js`. Verificación: los archivos existen y abren sin assets remotos.
- [x] 5.2 Renderizar cada mockup a 390×844 y 1440×900, guardar capturas en `mockups/previews/` e inspeccionarlas. Verificación: capturas presentes y sin defectos evidentes.
- [x] 5.3 Registrar `Approval: approved (fecha, by user)` en `mockups/README.md` y en la sección UI Mockups de `design.md`. Verificación: aprobación explícita del usuario antes de tocar el frontend.

## 6. Frontend — cliente de API

- [x] 6.1 Crear `shared/api/reportes.ts` con tipos y funciones de los tres reportes + export (blob). Verificación: `npm run tsc` sin errores y sin `any`.
- [x] 6.2 Exportar tipos usados por las páginas de reportes. Verificación: `tsc` sin errores.

## 7. Frontend — páginas de reportes

- [x] 7.1 Crear `/app/reportes/ocupacion` con filtros de rango, selector de profesional/sillón, tarjetas y tabla de ocupación. Verificación: `tsc`, `eslint` y navegación manual.
- [x] 7.2 Crear `/app/reportes/facturacion` con filtros, tarjetas por medio/OS y tabla de desglose. Verificación: `tsc`, `eslint` y `npm run build`.
- [x] 7.3 Crear `/app/reportes/ausentismo` con filtros, tarjetas de ausentismo/recuperación y tabla. Verificación: `tsc`, `eslint` y `npm run build`.
- [x] 7.4 Implementar botones de export CSV con manejo de error, estados vacío/carga/error y 403 por rol, respetando RBAC cosmético. Verificación: `npm run build` y recorrido manual con `admin`, `recepcion` y `odontologo`.

## 8. Integración, documentación y verificación

- [x] 8.1 Escribir la prueba de integración de punta a punta: registrar turnos y movimientos, consultar los tres reportes, exportar CSV y verificar RBAC (401/403). Verificación: `python -m pytest test/test_reportes_integracion.py -q` en verde.
- [x] 8.2 Documentar endpoints, filtros y formato CSV en `docs/guia-c21-reportes.md`, incluyendo la fórmula de ocupación y la heurística de ausentismo. Verificación: comandos y endpoints documentados responden como se describe.
- [x] 8.3 Ejecutar la skill `business-rule-coverage-auditor` y actualizar `docs/auditorias/matriz-reglas-tests.md` con reglas de reportes, R1–R13 y RN aplicables. Verificación: matriz sin huecos sin justificar y ambigüedades registradas.
- [x] 8.4 Correr `ruff check src test`, `python -m pytest -q` dos veces seguidas, y en frontend `lint`, `tsc` y `build`. Verificación: todo en verde y suite completa estable.
- [x] 8.5 Correr `openspec validate "c-21-reportes" --strict` y `openspec validate --all`. Verificación: ambos comandos sin errores ni advertencias.

## Workflow follow-up

- Confirmar con el usuario las decisiones abiertas de `design.md` antes de implementar (gobernanza MEDIO).
- Aprobar los mockups y registrarlo antes de aplicar cambios visuales.
- Archivar el change con `/opsx:archive c-21-reportes` y marcar `[x]` en `CHANGES.md`.
- No commitear ni pushear sin pedido explícito (R11).
