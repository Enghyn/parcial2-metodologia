# Arquitectura Propuesta

Monolito modular FastAPI + React SPA + Postgres + Redis + Docker Compose. Multi-tenant por `tenant_id`. Prioridad velocidad de entrega; deuda documentada al pie.

## Patrones aplicados

| Patrón | Dónde se usa | Por qué |
|---|---|---|
| Monolito modular | Backend `agenda/clinica/caja/notificaciones/admin` como paquetes con fronteras | Deploys simples en piloto; transacciones ACID para antisolapamiento y caja |
| Adapter (Ports) | `Facturador(manual→arca)`, `Notificador(wa)`, `Cobrador(mp)` | ARCA fase 2 sin tocar caja; WA/MP mockeables en tests |
| RBAC por tenant | Dependencia FastAPI `require(rol, recurso)` + `tenant_id` en cada query | Aislamiento barato sin schema-por-tenant |
| Exclusion constraint | Antisolapamiento sillón/profesional en Postgres (`gist`) + chequeo en servicio | Garantía a nivel DB contra carreras (doble reserva) |
| Jobs/colas | Redis RQ/Celery: recordatorios, confirmaciones, ofertas de lista de espera, webhooks | Lo único asíncrono real; reintentos con backoff |
| Webhooks idempotentes | WA y MP con tabla de `event_id` procesados | Evita doble cobro / doble confirmación |
| Token público | Turno/presupuesto/pago con UUID + expiración | Paciente opera sin login en v1 |

## Estructura de directorios

```
proyecto/
├── docker-compose.yml          # api + web + postgres + redis (+ worker)
├── backend/
│   ├── Dockerfile
│   ├── pyproject.toml          # fastapi, sqlalchemy, alembic, redis/rq, mercadopago-sdk, pydantic-settings
│   └── app/
│       ├── main.py             # create_app, routers, middlewares (tenant, auth, audit)
│       ├── core/               # config, security (JWT), deps (get_tenant, require_role), errors
│       ├── modules/
│       │   ├── agenda/         # router, service (antisolapamiento), schemas, models (Turno, Bloqueo, Sillon)
│       │   ├── lista_espera/   # service auto-relleno + jobs
│       │   ├── clinica/        # pacientes, odontograma, presupuestos
│       │   ├── caja/           # movimientos, MP links, cuenta corriente, comprobantes + adapter Facturador
│       │   ├── os/             # obras sociales + nomenclador
│       │   ├── notificaciones/ # adapter WA + plantillas + jobs recordatorios
│       │   └── admin/          # tenants, usuarios, reportes, auditoría, exportación
│       ├── adapters/           # facturador.py (Manual/Arca), whatsapp.py, mercadopago.py
│       ├── db/                 # base, session (tenant filter), migrations (alembic)
│       └── workers/            # rq tasks: recordatorios, ofertas, conciliación
└── frontend/
    ├── Dockerfile
    ├── vite.config.ts
    └── src/
        ├── app/                # router, auth (JWT), tenant context, layout
        ├── features/
        │   ├── agenda/         # día/semana por sillón, crear turno, bloqueos, sobreturnos
        │   ├── reserva-publica/ # /reservar/:slug (4 pasos, sin auth)
        │   ├── lista-espera/
        │   ├── clinica/        # ficha, odontograma SVG, presupuestos
        │   ├── caja/           # movimientos, cierre, cuenta corriente, MP links
        │   ├── os/             # buscador nomenclador, cobertura
        │   └── reportes/       # ocupación, facturación, ausentismo
        └── shared/             # ui, api client, hooks, utils
```

## Seguridad

- Autenticación: JWT Bearer (access corto + refresh); login solo usuarios internos; paciente con tokens públicos UUID, no JWT.
- Autorización: RBAC por `(tenant_id, rol)` — matriz de `03_actores_y_roles.md`; enforcement en dependencia FastAPI + chequeo en frontend solo cosmético.
- Validación de input: schemas Pydantic estrictos (teléfono E.164, DNI, montos>0, rangos temporales); captcha + rate-limit en `/public/*`.
- Secrets management: solo por variables de entorno / Docker secrets; nunca en repo. Rotación de signing keys JWT documentada.
- Datos de salud: consentimiento obligatorio (RN-CL-04), acceso por rol, sin PHI en logs/WA (RN-G-03); backups Postgres cifrados; RLS como mejora fase 2.

## Variables de entorno

| Variable | Descripción | Ejemplo | Sensible |
|---|---|---|---|
| `DATABASE_URL` | DSN Postgres | `postgresql+psycopg://u:p@db:5432/odonto` | Y |
| `REDIS_URL` | Colas/jobs | `redis://redis:6379/0` | N |
| `JWT_SECRET` | Firma de tokens | `changeme-32+` | Y |
| `JWT_EXPIRE_MIN` | Vida del access token | `60` | N |
| `WA_TOKEN` | WhatsApp Cloud API | `EAAB...` | Y |
| `WA_PHONE_ID` | ID número emisor | `123456789` | N |
| `WA_WEBHOOK_VERIFY` | Token verificación Meta | `...` | Y |
| `MP_ACCESS_TOKEN` | Mercado Pago | `APP-...` | Y |
| `MP_WEBHOOK_SECRET` | Firma IPN | `...` | Y |
| `TENANT_DEFAULT_CANCEL_HS` | Antelación cancelación | `12` | N |
| `LISTA_ESPERA_OFERTA_MIN` | Expiración oferta | `60` | N |
| `FACTURADOR_MODO` | `manual` en v1, `arca` fase 2 | `manual` | N |
| `ARCA_*` | CUIT, cert, key, WSFE endpoint (fase 2) | — | Y |
| `CORS_ORIGINS` | Orígenes SPA + portal | `https://app.x,https://slug.x` | N |

Deuda documentada (velocidad primero): sin RLS en v1 (filtro por `tenant_id` en sesión), sin multi-sede, reportes con SQL directo (sin warehouse), tests e2e mínimos del flujo reserva→cobro; todo listado para roadmap.
