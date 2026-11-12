# Tasks

## 1. Contratos y configuración (backend)

- [x] 1.1 Agregar a `app/modules/public/schemas.py` los schemas públicos `ItemPresupuestoPublicoOut`, `PresupuestoPublicoOut`, `PagoPublicoOut`, `AprobacionPublicaIn` y `RechazoPublicoIn`, todos con `ConfigDict(extra="forbid")` (R1) y sin `id`, `paciente_id`, `presupuesto_id`, `movimiento_id` ni `token_publico`. Verificar con tests de schema que un campo extra produce 422 y que la salida no expone IDs internos.
- [x] 1.2 Agregar `portal_usuario_email: str` (default `admin@consultorio.com`) a `Settings` en `app/core/config.py` y documentarlo en `backend/.env.example`. Verificar con un test de settings que el valor por defecto y el override por entorno funcionan.

## 2. Servicio público del portal (backend)

- [x] 2.1 Implementar `PortalPublicoService` (en `app/modules/public/service.py` o `portal_service.py`) con `obtener_presupuesto_publico(token)`, `aprobar(token, firma)` y `rechazar(token, motivo)`. Verificar con tests de servicio: token válido devuelve ítems/total/estado; token inexistente lanza "no encontrado"; `aprobar` sobre `enviado` pasa a `aprobado` y setea `aprobado_en`; `aprobar` sobre `aprobado` es idempotente; transición sobre `cobrado` es conflicto; `rechazar` sobre `enviado` pasa a `rechazado`.
- [x] 2.2 Implementar `confirmar_pago_publico(token)` con reclamo atómico `SELECT ... FOR UPDATE` sobre la fila de `presupuestos`, resolución/creación del `Pago` pendiente, cobro con `CobradorSimulado`, registro de `IntentoPago` y creación de **un** `MovimientoCaja` de ingreso con medio de pago, concepto y `usuario_id` resuelto por `portal_usuario_email` (R3/R4). Verificar con tests de servicio: confirmación crea un movimiento y pasa a `aprobado`; doble confirmación no crea un segundo movimiento; dos confirmaciones concurrentes crean exactamente un movimiento; presupuesto no `aprobado` → conflicto; token inexistente → no encontrado; `portal_usuario_email` inexistente → conflicto.
- [x] 2.3 Corregir `PagoService.confirmar` para recibir y exigir `usuario_id` (deuda R4 de C-17, hoy crea `MovimientoCaja` con `usuario_id=None`) y agregar el test que verifica que el movimiento resultante tiene `usuario_id` y `medio_pago` válidos.

## 3. Endpoints públicos (backend)

- [x] 3.1 Agregar a `app/modules/public/router.py` las rutas `GET /presupuestos/{token}`, `POST /presupuestos/{token}/aprobar`, `POST /presupuestos/{token}/rechazar`, `GET /pagos/{token}` y `POST /pagos/{token}/confirmar`, con `response_model`, `dependencies=[Depends(limitar_publico(...))]` (lectura/escritura) y mapeo de errores a 404/409/422. Verificar con tests de router que cada endpoint responde 200/201 en el camino feliz y 404/409/422 en los bordes.
- [x] 3.2 Agregar tests de seguridad de los endpoints públicos: token inexistente → 404 genérico sin revelar existencia; respuesta sin `id`/`paciente_id`/`presupuesto_id`/`movimiento_id`; sin DNI/teléfono/datos clínicos en el cuerpo (R9).
- [x] 3.3 Agregar tests que envían un campo no declarado en los cuerpos de `aprobar`/`rechazar` y verifican 422 (R1).

## 4. Cliente de API del portal (frontend)

- [x] 4.1 Agregar a `frontend/src/shared/api/public.ts` los tipos y funciones tipadas `getPresupuestoPublico`, `aprobarPresupuestoPublico`, `rechazarPresupuestoPublico`, `getPagoPublico` y `confirmarPagoPublico` (sin `any`, R7), reusando el patrón de `request<T>` con import diferido. Verificar con tests de node:test de los helpers puros/constructores de URL y con `tsc` sin errores.

## 5. Páginas del portal (frontend)

- [x] 5.1 Crear `features/portal-publico/ResumenPresupuesto.tsx` y `FirmaSimple.tsx` mostrando ítems, total en ARS (`formatArs`) y el campo de firma, con textos en es-AR (R10). Verificar con tests de render que el total se formatea en ARS y que la firma vacía no permite enviar.
- [x] 5.2 Crear `features/portal-publico/PresupuestoPublicoPage.tsx` que lea el `token` de `useParams`, consulte presupuesto y pago en paralelo (`Promise.all`), permita aprobar/rechazar y muestre una vista de "no encontrado" genérica ante 404. Verificar con tests de componente/handler: aprobación exitosa refleja `aprobado`, rechazo refleja `rechazado`, token inválido muestra el mensaje genérico.
- [x] 5.3 Crear `features/portal-publico/PagarPage.tsx` y `ResultadoPago.tsx` con el monto en ARS y el botón de confirmación deshabilitado mientras la request está en curso. Verificar con tests que un doble clic no dispara dos confirmaciones y que el resultado (aprobado/rechazado) se muestra.
- [x] 5.4 Crear `features/portal-publico/MarcaConsultorio.tsx`, montarla en `PublicLayout` (`app/layout.tsx`) y reemplazar los stubs `PresupuestoPublicoPage`/`PagarPage` de `app/pages.tsx` por los componentes reales, importados directamente (sin barrel) desde `app/router.tsx`. Verificar con `tsc` + lint + build del frontend y con un test de render de la marca única (sin slug ni selector de tenant).

## 6. Integración (backend + frontend)

- [x] 6.1 Ejecutar la suite rápida del backend (`cd backend && python -m pytest -m "not integration" -q`) y verificar que queda en verde.
- [x] 6.2 Ejecutar la suite completa del backend con base migrada y sembrada (`alembic upgrade head`, `python -m db.seed` si hace falta, `python -m pytest -q`) y verificar que queda en verde, incluyendo los tests de concurrencia de la confirmación pública.
- [x] 6.3 Ejecutar `ruff check src test` y el lint/`tsc`/build del frontend y verificar que quedan en verde.
- [x] 6.4 Ejecutar `openspec validate c-18-portal-publico --strict` y verificar que pasa.

## 7. Workflow follow-up

- [x] 7.1 Pasar `business-rule-coverage-auditor` sobre el change y actualizar la matriz de cobertura (R1–R13 y RN-*).
- [ ] 7.2 Archivar el change (`/opsx:archive c-18-portal-publico`) y marcar `C-18` como `[x]` en `CHANGES.md`.
