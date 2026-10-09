# Descripción General

## Stack tecnológico

Stack REAL del proyecto (decisiones cerradas del gate; prioridad: velocidad de entrega).

| Capa | Tecnología | Versión mínima |
|---|---|---|
| Lenguaje backend | Python | 3.12 |
| Framework API | FastAPI | 0.110+ |
| Auth | JWT (OAuth2 Bearer, `python-jose` o `PyJWT`) | — |
| ORM | SQLAlchemy | 2.0+ |
| Base de datos | PostgreSQL | 15+ |
| Colas / jobs | Redis (RQ o Celery) + Redis | 7+ |
| Empaquetado / deploy | Docker + Docker Compose | Compose v2 |
| Lenguaje frontend | TypeScript | 5+ |
| UI | React (SPA) | 18+ |
| Build frontend | Vite | 5+ |
| Tenancy | Columna `tenant_id` en cada tabla (discriminador) + RLS opcional fase 2 | — |
| Integración WA | WhatsApp Business API (Cloud API, REST + webhooks) | v19+ |
| Integración cobros | Mercado Pago Checkout Pro / Payment Link + Webhooks IPN (SDK `mercadopago`) | API v1 |
| Facturación v1 | Registro manual (`Comprobante` + adapter `Facturador` modo `Manual`) | — |
| Facturación fase 2 | ARCA WSFE (adapter `Facturador` modo `ARCA`) | — |

## Arquitectura general

Monolito modular FastAPI + React SPA + Postgres + Redis, multi-tenant por `tenant_id`, desplegado con Docker Compose. Velocidad de entrega antes que microservicios; la modularización interna (agenda / clínica / caja / notificaciones) evita el big-ball-of-mud y deja deuda documentada (ver `08_arquitectura_propuesta.md`).

```
                    ┌──────────────────────────────────────────────┐
                    │              Consultorio (tenant)            │
                    │  link/QR  /reservar/:slug  (portal público) │
                    └──────┬───────────────────────────────┬───────┘
                           │                               │
              ┌────────────▼────────────┐     ┌────────────▼────────────┐
              │  React SPA + Vite (TS)  │     │  WhatsApp Business API  │
              │  agenda · clínica · caja│     │  recordatorios/confirm. │
              └────────────┬────────────┘     └────────────▲────────────┘
                           │ HTTPS/JWT (JSON)              │ webhook
              ┌────────────▼───────────────────────────────┴────────────┐
              │              FastAPI monolito modular                   │
              │  agenda │ clinica │ caja │ notificaciones │ admin/tenants│
              │  JWT + RBAC por consultorio · auditoría · exportación   │
              └──────┬──────────────────────────────┬───────────────────┘
                     │ SQLAlchemy                   │ RQ/Celery
          ┌──────────▼──────────┐        ┌──────────▼──────────┐
          │  PostgreSQL (+tenant│        │  Redis (colas WA,   │
          │  _id en cada tabla) │        │  confirmaciones,    │
          └─────────────────────┘        │  auto-relleno)      │
                                         └─────────────────────┘
              ┌──────────────────┐     ┌──────────────────┐
              │  Mercado Pago    │     │  ARCA fase 2     │
              │  link/seña+webhook│    │  (adapter v1=Manual)│
              └──────────────────┘     └──────────────────┘
```

Justificación: el piloto es chico (1–5 consultorios, <50 usuarios internos + pacientes) y la prioridad es salir rápido; un monolito modular da deploys simples (un Compose), transacciones ACID para antisolapamiento y caja, y colas Redis para lo único realmente asíncrono (recordatorios, confirmaciones, auto-relleno). Postgres con `tenant_id` por tabla aísla consultorios sin el costo operativo de un schema/DB por tenant.

## Integraciones externas

| Servicio | Propósito | Tipo |
|---|---|---|
| WhatsApp Business API (Cloud API) | Recordatorios, confirmación/cancelación/reprogramación con botones, aviso de lista de espera | REST (envío + plantillas) + webhook (entrantes/estados) |
| Mercado Pago | Link de pago y seña online; conciliación de cobros | REST (Checkout Pro / Payment API) + webhook IPN + SDK |
| Web / portal propio | Reserva online 24/7 por link/QR (`/reservar/:slug`), SEO por consultorio | Frontend propio (SPA pública, sin auth) → REST interno |
| ARCA (fase 2) | Factura electrónica A/B/C | Adapter `Facturador`: v1 `Manual`, fase 2 `ARCA` (WSFE/SOAP-REST) |
| Google Calendar (fase 2) | Sincronización bidireccional de agenda | REST (OAuth2 + webhooks de canal) |
| API pública (fase 2) | Integraciones de terceros | REST + API keys por tenant |

## API REST

Agrupada por recurso; todo bajo `/api/v1` salvo rutas públicas. Autenticación JWT Bearer; tenant derivado del usuario (o del `slug` en rutas públicas).

- **Auth/usuarios**: `POST /auth/login`, `POST /auth/refresh`, `GET /usuarios`, `POST /usuarios`, `PATCH /usuarios/:id`, `GET /roles`.
- **Tenants**: `POST /tenants`, `GET /tenants/:id`, `PATCH /tenants/:id` (slug, planes, cupo WA).
- **Profesionales/sillones**: `GET/POST /profesionales`, `GET/POST /sillones`, `GET /disponibilidad?profesional=&sillon=&desde=&hasta=`.
- **Turnos**: `GET /turnos?dia=&sillon=&profesional=`, `POST /turnos`, `PATCH /turnos/:id` (confirmar/cancelar/reprogramar), `POST /turnos/:id/sobreturno`, `POST /bloqueos`.
- **Reserva pública**: `GET /public/disponibilidad/:slug`, `POST /public/reservar/:slug` (sin auth, rate-limited + captcha).
- **Lista de espera**: `GET/POST /lista-espera`, `POST /lista-espera/:id/ofrecer` (dispara WA, expira en N min).
- **Clínica**: `GET/PUT /pacientes/:id/odontograma`, `GET/POST /fichas`, `GET/POST /presupuestos`, `POST /presupuestos/:id/aprobar`.
- **Caja**: `GET/POST /movimientos-caja`, `POST /cobros/mp-link`, `POST /webhooks/mercadopago`, `GET /cuentas-corrientes`, `POST /recuperos`.
- **OS/nomenclador**: `GET /obras-sociales`, `GET /nomenclador?q=`, `POST /coberturas/verificar` (v1: manual/tabla; fase 2: online).
- **Comprobantes**: `GET/POST /comprobantes` (v1 manual; fase 2 emite vía adapter ARCA).
- **Notificaciones**: `POST /notificaciones/recordatorio`, `POST /webhooks/whatsapp`.
- **Reportes/admin**: `GET /reportes/ocupacion`, `GET /reportes/facturacion`, `GET /reportes/ausentismo`, `GET /auditoria`, `GET /export?entidad=`.
