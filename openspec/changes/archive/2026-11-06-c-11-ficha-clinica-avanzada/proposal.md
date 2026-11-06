# Proposal — C-11 ficha-clinica-avanzada

## Why

C-07 dejó la ficha clínica reducida al estado actual del odontograma: cada pieza se pisa con un upsert y no queda registro de quién la cambió ni cuándo. Tampoco existen evolución clínica ni consentimiento informado. Sin esa trazabilidad la ficha no sirve como historia clínica ni como insumo auditable para C-13a, C-16 y C-20.

## What Changes

- **Evolución clínica**: `GET`/`POST /api/v1/pacientes/{id}/evoluciones` con `texto`, `fecha` y autor tomado del JWT. Append-only: sin edición ni borrado.
- **Consentimiento informado**: `GET`/`POST /api/v1/pacientes/{id}/consentimientos` con `version`, `fecha` y autor del JWT. Un consentimiento por versión y paciente; el alta de una versión nueva no pisa la anterior.
- **Autor y fecha por hallazgo**: `hallazgos_pieza` incorpora `autor_usuario_id`; el `PUT` de pieza lo completa desde el JWT (nunca desde el cuerpo).
- **Historial por pieza**: `GET /api/v1/pacientes/{id}/odontograma/piezas/{pieza}/historial` devuelve versiones con estado/observación anteriores y nuevos, autor y fecha. Se escribe una versión por cada upsert en la misma transacción.
- **Inmutabilidad**: evoluciones, consentimientos e historial son append-only; se bloquean `UPDATE` y `DELETE` por trigger, igual que el libro de caja (R3/R13).
- **RBAC**: lectura de las tres secciones para `admin`, `recepcion` y `odontologo`; escritura solo `odontologo` (RN-CL-02, R8).
- **Frontend**: la ficha `/app/odontograma/:pacienteId` suma evolución, consentimiento e historial por pieza, reutilizando el sistema de diseño revisión 1.
- **Migración `0007_ficha_clinica_avanzada`**: tres tablas nuevas, una columna y triggers. Se numera `0007` porque la última migración real es `0005` y C-10 tomaría `0006` si se implementa antes.
- **Estados clínicos**: se mantienen los 6 de la KB (`sano`, `caries`, `obturacion`, `corona`, `extraccion`, `tratamiento_conducto`); no se adoptan los 18 del roadmap viejo.

## Capabilities

### New Capabilities

- Ninguna. El consentimiento informado no se separa en una capability propia: es un registro clínico 1:N del paciente que comparte RBAC, privacidad, inmutabilidad y superficie de UI con `clinical-records`. Crear `informed-consent` duplicaría el modelo de acceso y partiría la ficha del paciente en dos contratos.

### Modified Capabilities

- `clinical-records`: se agregan requisitos de evolución clínica, consentimiento versionado, autoría/fecha del hallazgo, historial por pieza, RBAC ampliado, privacidad y la interfaz de la ficha avanzada.
- `core-data-model`: se agregan requisitos de persistencia para `evoluciones_clinicas`, `consentimientos_informados`, `hallazgos_pieza_historial`, la columna `hallazgos_pieza.autor_usuario_id` y la migración reversible.

## Impact

- **Backend**: `modules/clinica/{models,schemas,service,router}.py`; `db/migrations/versions/0007_ficha_clinica_avanzada.py`; `api/v1/router.py` (si cambia el montaje); tests de schemas, servicio, router y estructura.
- **Base de datos**: tres tablas nuevas, una columna nullable y triggers anti-`UPDATE`/`DELETE`. Sin `tenant_id` (R2).
- **Frontend**: `shared/api/clinica.ts` y `features/clinica/*` (secciones nuevas dentro de la ficha existente). Sin ruta pública nueva.
- **Contratos existentes**: `GET /odontograma` y `PUT /piezas` se mantienen; el `PUT` suma autor/historial y la respuesta puede incluir `autor_usuario_id` de forma aditiva.
- **Documentación**: `CHANGES.md` mantiene C-11 `[ ]` hasta archivar; la numeración real de migración se confirma al implementar.
- **Fuera de alcance**: firma digital, adjuntos/imágenes, revocación de consentimiento, plantillas de texto de consentimiento, edición de evoluciones y cualquier integración externa.
- **Gobernanza CRÍTICO**: este propose es solo análisis. La implementación requiere aprobación humana explícita.
