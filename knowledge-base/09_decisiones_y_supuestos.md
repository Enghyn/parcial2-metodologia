# Decisiones y Supuestos

Documentación de las decisiones de diseño adoptadas para balancear el rigor metodológico y la viabilidad del proyecto académico.

---

## Decisiones de Diseño Documentadas

### DD-01 — Monolito Modular
* **Decisión:** Unificar el backend en una única aplicación FastAPI modularizada por carpetas de dominio (`modules/agenda`, `modules/clinica`, `modules/caja`), comunicada con una SPA en React.
* **Justificación:** Reduce drásticamente la fricción de despliegue y desarrollo local respecto a microservicios, manteniendo la separación de responsabilidades y facilitando transacciones en base de datos.

### DD-02 — Modelo de Consultorio Único (Mono-Tenant)
* **Decisión:** El sistema gestiona un único consultorio odontológico con múltiples sillones (2 a 3 sillones) y múltiples usuarios internos.
* **Justificación:** El aislamiento multi-inquilino comercial (`tenant_id` en cada tabla y consulta) agrega complejidad redundante para la evaluación de la cátedra sin aportar valor a las reglas clínicas y de agenda.

### DD-03 — Antisolapamiento en Capa de Servicio Backend
* **Decisión:** Implementar la validación de solapamiento de agenda en la capa de servicios de FastAPI (`Service Layer`) mediante consultas SQL estándar, respaldada por una exhaustiva suite de pruebas unitarias (`pytest`).
* **Justificación:** Evita atarse a extensiones avanzadas de PostgreSQL (`btree_gist` / `EXCLUDE USING gist`), simplificando las migraciones de Alembic y permitiendo ejecutar pruebas rápidas en cualquier entorno.

### DD-04 — Odontograma Esquemático Interactivo (FDI)
* **Decisión:** Desarrollar el odontograma en React como una grilla interactiva de los 32 dientes numerados del 11 al 48, con selección visual de estados (`sano`, `caries`, `obturacion`, etc.).
* **Justificación:** Proporciona una interfaz clara, intuitiva y rápida de implementar, evitando el sobrecosto de modelar gráficos vectoriales SVG hipercomplejos de cada cara dental desde cero.

### DD-05 — Comunicación Directa vía Enlaces `wa.me/`
* **Decisión:** La comunicación con los pacientes se resuelve mediante botones que abren enlaces Click-to-Chat (`https://wa.me/<telefono>?text=...`) con mensajes preformateados, complementado con un servicio de notificación simulado en consola/BD.
* **Justificación:** Cumple al 100% el requerimiento funcional de contacto y confirmación con el paciente sin incurrir en costos ni depender de la compleja verificación de cuentas comerciales en Meta Cloud API.

### DD-06 — Caja Directa y Cobros Simulados
* **Decisión:** Gestión contable basada en libro de movimientos de caja (ingresos/egresos, señas, medios de pago) sin conexión a webhooks de producción de Mercado Pago.
* **Justificación:** Permite demostrar el flujo contable completo (cobro de atención, seña de turno, balance diario) sin requerir túneles HTTPS externos (Ngrok) ni cuentas de sandbox.

### DD-07 — Tareas en Segundo Plano Nativas
* **Decisión:** Emplear `BackgroundTasks` nativas de FastAPI para operaciones en segundo plano (envío simulado de recordatorios, registros de auditoría), prescindiendo de contenedores Redis y Celery/RQ.
* **Justificación:** Mantiene `docker-compose.yml` liviano (únicamente `api`, `web` y `postgres`), acelerando el arranque del entorno y el consumo de recursos de la máquina.

---

## Supuestos de Negocio

* **SU-01 (Capacidad Instalada):** El consultorio cuenta con 2 o 3 sillones físicos identificados y un equipo de odontólogos con distintas especialidades y duraciones de consulta.
* **SU-02 (Acceso Público Ágil):** Los pacientes no desean crearse una cuenta con usuario/contraseña para solicitar un turno; prefieren una reserva ágil con DNI y teléfono.
* **SU-03 (Horarios de Atención):** El consultorio maneja franjas horarias fijas de atención (ej. lunes a viernes de 8:00 a 20:00 hs), dentro de las cuales se validan los turnos y bloqueos.
