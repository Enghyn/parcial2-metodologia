# Guía de handoff — C-21 reportes

> Para el compañero que cierra el MVP expandido. Esta guía es un **cómo arrancar y qué no olvidar**.
> La fuente de verdad sigue siendo [`CHANGES.md`](../CHANGES.md), [`AGENTS.md`](../AGENTS.md) y `knowledge-base/`.
> Estado al escribir esto: C-01..C-20 archivados, C-21 en apply.

## 1. Antes de tocar código

```powershell
git pull --rebase origin main

cd backend
alembic upgrade head          # idempotente; cwd canónico = backend/
cd ..
```

C-21 no crea migración (solo lecturas sobre tablas existentes), pero hay que asegurarse de que la base está en la cabeza (`0016_auditoria`) antes de correr tests de integración.

```powershell
cd backend
$env:DATABASE_URL="postgresql+psycopg://odonto:odonto@localhost:5432/odonto"
python -m pytest -q
cd ..
```

- Si el baseline no está **verde**, frená y avisá: no arranques sobre rojo.
- Corré la suite **dos veces seguidas**. Si la segunda falla, hay data de test sin limpiar (los tests de reportes crean turnos/movimientos/pacientes con fechas al azar; si una segunda corrida choca, revisá aislamiento).

## 2. Alcance de C-21 (solo lectura, sin migración)

Tres endpoints de gestión + su variante CSV es-AR:

| Endpoint | Roles | Descripción |
|---|---|---|
| `GET /api/v1/reportes/ocupacion` | admin, recepcion, odontólogo (solo propio) | Ocupación por sillón y profesional: conteos por estado, tasa y horas bloqueadas. |
| `GET /api/v1/reportes/facturacion` | admin, recepcion | Ingresos por medio de pago y desglose por obra social (monto OS / copago / paciente). |
| `GET /api/v1/reportes/ausentismo` | admin, recepcion | Cancelados, no presentados, recuperados (heurística) y tasa de ausentismo. |
| `GET /api/v1/reportes/{reporte}/export.csv` | igual que el reporte | CSV es-AR: BOM UTF-8, separador `;`, coma decimal, `dd/mm/aaaa`, `Content-Disposition: attachment`. |

Filtros (todos): `desde`, `hasta` (YYYY-MM-DD, día calendario ART). Default: `desde = hoy - 30 días`, `hasta = hoy`. `desde > hasta` → **422**. Sin token → **401**. `odontólogo` sobre reporte global → **403** (salvo ocupación propia).

### Parámetros adicionales
- `ocupacion`: además acepta `profesional_id` y `sillon_id` (opcionales). Un `odontólogo` solo puede consultar su propio `profesional_id` (otro → 403).

## 3. Reglas duras aplicables (R1–R13)

- **R1**: todos los schemas Pydantic de reportes declaran `extra="forbid"` (ver `test_reportes_schemas.py`).
- **R2**: C-21 no usa `tenant_id` (mono-consultorio multi-sillón).
- **R3**: C-21 es solo lectura; no escribe ni borra en caja.
- **R4**: no aplica (reportes no cobran; solo leen `MovimientoCaja`).
- **R5**: type hints + `snake_case`; C-21 no cambia schema → no hay migración (R5 no obliga a migración sin cambio de schema).
- **R6**: no aplica (reportes no crea ni reprograma turnos; solo lee estados).
- **R7**: frontend tipado estricto (`tsc`, `eslint`, `build` verde); componentes `PascalCase`; sin `any`.
- **R8**: RBAC se cumple en el backend (`require_role` + `usuario_con_filtro_profesional`); la UI solo oculta/deshabilita cosméticamente.
- **R9**: los CSV nunca contienen DNI, diagnósticos, hallazgos ni tokens (solo ids, conceptos, montos y fechas).
- **R10**: superficies en español rioplatense; montos en ARS; CSV es-AR.
- **R11 / R12**: reglas de proceso (no commitear/pushear sin pedido; commits convencionales).
- **R13**: C-21 no borra físicamente entidades de negocio.

## 4. Reglas de negocio (RN) aplicables

- **RN-SEG-01**: los endpoints de reportes requieren `Authorization: Bearer` válido (401 sin token).
- **RN-CJ-01**: el reporte de facturación refleja el libro de caja (medio de pago, monto, usuario) sin crear movimientos.
- **RN-AG-01 / RN-AG-05**: el reporte de ocupación refleja estados de turno (`reservado`/`confirmado`/`presente`/`atendido`/`cancelado`) sin imponer antisolapamiento.
- Las demás RN (caja, clínica, agenda, comunicación) son de solo lectura en C-21 o no aplican.

## 5. Endpoints y ejemplos

```bash
# Ocupación, último mes, global (recepcion/admin)
curl "$API/api/v1/reportes/ocupacion" -H "Authorization: Bearer $TOKEN"

# Ocupación de un profesional en un rango (odontólogo puede usar su propio id)
curl "$API/api/v1/reportes/ocupacion?desde=2026-10-01&hasta=2026-10-31&profesional_id=<uuid>" -H "Authorization: Bearer $TOKEN"

# Export CSV de facturación
curl "$API/api/v1/reportes/facturacion/export.csv?desde=2026-10-01&hasta=2026-10-31" \
  -H "Authorization: Bearer $TOKEN" -o facturacion.csv
```

CSV de ejemplo (es-AR):

```
recurso;id;nombre;reservado;confirmado;presente;atendido;cancelado;tasa_ocupacion;horas_bloqueadas
sillon;<uuid>;Sillón 1;1;0;0;2;0;0,6667;0,00
```

## 6. Frontend

- `shared/api/reportes.ts`: clientes tipados (`reporteOcupacion`, `reporteFacturacion`, `reporteAusentismo`, `exportar*Csv`, `descargarCsv`).
- Páginas: `/app/reportes/ocupacion`, `/app/reportes/facturacion`, `/app/reportes/ausentismo` (registradas en `app/router.tsx`).
- RBAC cosmético: `odontólogo` ve solo ocupación; facturación/ausentismo ocultas (el backend es la autoridad).

## 7. Pruebas

- `test/test_reportes_schemas.py` (R1, rangos, estados).
- `test/test_reportes_ocupacion_service.py`, `test_reportes_facturacion_service.py`, `test_reportes_ausentismo_service.py` (integración contra PostgreSQL).
- `test/test_reportes_ocupacion_router.py`, `test_reportes_facturacion_router.py`, `test_reportes_ausentismo_router.py` (HTTP: 401/403/200/422).
- `test/test_reportes_csv.py` (formato es-AR, BOM, separador, coma decimal, escape).
- `test/test_reportes_export_router.py` (export: Content-Type, Content-Disposition, BOM, R9, RBAC).
- `test/test_reportes_integracion.py` (E2E: 3 reportes + CSV + RBAC).

Ejecutar con:
```powershell
$env:DATABASE_URL="postgresql+psycopg://odonto:odonto@localhost:5432/odonto"
python -m pytest test/test_reportes_*.py -q
```

## 8. Qué revisar antes de archivar

- [ ] `test/test_reportes_*.py` en verde y suite completa verde dos veces seguidas.
- [ ] `ruff check src test` y `frontend` `lint`/`tsc`/`build` en verde.
- [ ] `business-rule-coverage-auditor` pasado y `docs/auditorias/matriz-reglas-tests.md` actualizada con C-21.
- [ ] `openspec validate "c-21-reportes" --strict` y `openspec validate --all` sin errores.
- [ ] Archivar con `/opsx:archive c-21-reportes` y marcar `[x]` en `CHANGES.md`.
- [ ] No commitear ni pushear sin pedido explícito (R11).
