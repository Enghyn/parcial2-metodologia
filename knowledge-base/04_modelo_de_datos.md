# Modelo de Datos

Multi-tenant por discriminador: **toda tabla de negocio lleva `tenant_id`** (aislamiento lógico; RLS opcional en fase 2). Sillón es entidad obligatoria desde día 1 aunque la UI arranque simple.

## Dominios

- **Tenancy/identidad**: Tenant, Usuario (roles por consultorio), Profesional.
- **Agenda**: Sillón, Turno, Bloqueo, ListaEspera.
- **Clínica**: Paciente, Odontograma (piezas/estados), Ficha/Evolución, Presupuesto.
- **Caja/cobros**: MovimientoCaja, CobroMP, CuentaCorriente, Comprobante (ARCA-preparado).
- **OS**: ObraSocial, Nomenclador (práctica + arancel por OS).
- **Transversal**: Notificación/WA, Auditoría, Consentimiento.

## ERD (textual)

```
Tenant 1──* Usuario | 1──* Profesional | 1──* Sillon | 1──* Paciente
Paciente 1──* Turno *──1 Profesional | Turno *──1 Sillon (obligatorio)
Sillon 1──* Bloqueo | Profesional 1──* Bloqueo
Paciente 1──* ListaEspera (→ Turno cuando auto-rellena)
Paciente 1──1 Odontograma 1──* HallazgoPieza | Paciente 1──* Ficha/Evolucion
Presupuesto *──1 Paciente | Presupuesto 1──* ItemPresupuesto (→ Nomenclador)
MovimientoCaja *──1 Turno? | *──1 Presupuesto? | *──1 CobroMP?
Comprobante *──1 MovimientoCaja? (v1 manual; fase 2 emite ARCA vía adapter)
ObraSocial 1──* Nomenclador (codigo, practica, arancel, copago)
Paciente *──* ObraSocial (afiliacion: credencial, plan)
Notificacion *──1 Turno | *──1 ListaEspera (canal WA, plantilla, estado)
Auditoria *──1 Usuario (quien/cuando/que/desde_donde)
```

## Entidades

### Tenant
- Atributos: `id:uuid PK`, `nombre:text`, `slug:text UNIQUE` (para `/reservar/:slug`), `plan:text` (por_sillon v1), `cupo_wa_mensual:int`, `config_cancelacion:jsonb` (antelación, seña reembolsable), `activo:bool`.
- Relaciones: 1──* con Usuario, Profesional, Sillón, Paciente y todo lo operativo.
- Constraints: `slug` único global, formato URL-safe. Índices: `slug`, `activo`.

### Usuario
- Atributos: `id:uuid PK`, `tenant_id:uuid FK→Tenant NOT NULL`, `nombre:text`, `email:citext UNIQUE por tenant`, `password_hash:text`, `rol:enum(admin,odontologo,recepcion)`, `profesional_id:uuid FK?` (si es odontólogo), `activo:bool`.
- Relaciones: *──1 Tenant; 1──1 Profesional (opcional); 1──* Auditoría.
- Constraints: email único por `(tenant_id, email)`; un usuario pertenece a un solo tenant en v1. Índices: `(tenant_id, rol)`, `(tenant_id, email)`.

### Profesional
- Atributos: `id:uuid PK`, `tenant_id FK NOT NULL`, `nombre:text`, `matricula:text`, `especialidad:text`, `duracion_default_min:int`, `agenda:jsonb` (horarios/sobreturnos), `activo:bool`.
- Relaciones: 1──* Turno; 1──* Bloqueo.
- Constraints: matrícula no vacía si atiende OS. Índices: `(tenant_id, activo)`.

### Sillon
- Atributos: `id:uuid PK`, `tenant_id FK NOT NULL`, `nombre:text` ("Sillón 1"), `box:text?`, `activo:bool`.
- Relaciones: 1──* Turno; 1──* Bloqueo.
- Constraints: **obligatorio en cada Turno** (segmento 2–3 sillones); nombre único por tenant. Índices: `(tenant_id, activo)`.

### Paciente
- Atributos: `id:uuid PK`, `tenant_id FK NOT NULL`, `nombre:text`, `dni:text`, `telefono:text` (E.164, para WA), `email:text?`, `obra_social_id:uuid FK?`, `nro_afiliado:text?`, `consentimiento:jsonb` (texto, fecha, firma/token), `origen:text` (linkQR/manual), `activo:bool`.
- Relaciones: 1──* Turno/Ficha/Presupuesto/CuentaCorriente.
- Constraints: `(tenant_id, dni)` único; teléfono válido para notificar; sin consentimiento no se cargan datos de salud. Índices: `(tenant_id, dni)`, `(tenant_id, telefono)`.

### Turno
- Atributos: `id:uuid PK`, `tenant_id FK NOT NULL`, `paciente_id FK NOT NULL`, `profesional_id FK NOT NULL`, `sillon_id FK NOT NULL`, `prestacion:text`, `inicio:timestamptz NOT NULL`, `fin:timestamptz NOT NULL` (= inicio + duración variable), `duracion_min:int`, `estado:enum(reservado,confirmado,presente,en_atencion,realizado,ausente,cancelado,reprogramado)`, `origen:enum(portal,mostrador,telefono,wa)`, `token_publico:uuid UNIQUE` (confirmar/cancelar sin login), `sena_monto:numeric?`, `sena_estado:enum?`, `notas:text?`.
- Relaciones: *──1 Paciente/Profesional/Sillón; 1──* Notificación/MovimientoCaja.
- Constraints: **antisolapamiento** — exclusion por `(sillon_id, rango)` y por `(profesional_id, rango)` excluyendo cancelados/reprogramados (Postgres `EXCLUDE USING gist` + chequeo en servicio); `fin > inicio`; sobreturno marcado explícitamente. Índices: `(tenant_id, inicio)`, `(sillon_id, inicio)`, `(profesional_id, inicio)`, `token_publico`.

### Bloqueo
- Atributos: `id:uuid PK`, `tenant_id FK NOT NULL`, `sillon_id FK?`, `profesional_id FK?`, `desde:timestamptz`, `hasta:timestamptz`, `motivo:text`.
- Constraints: al menos sillón o profesional; respeta el mismo antisolapamiento (bloquea huecos). Índices: `(tenant_id, desde)`.

### ListaEspera
- Atributos: `id:uuid PK`, `tenant_id FK NOT NULL`, `paciente_id FK NOT NULL`, `prestacion:text`, `profesional_id FK?`, `preferencia:jsonb` (días/horarios), `estado:enum(activa,ofrecida,aceptada,vencida,cancelada)`, `oferta_turno_id FK?`, `oferta_expira_at:timestamptz?`.
- Relaciones: → Turno cuando auto-rellena (se crea el Turno y la oferta expira en N min por WA).
- Índices: `(tenant_id, estado)`, `(paciente_id, estado)`.

### Odontograma (+ HallazgoPieza)
- Atributos cabecera: `id:uuid PK`, `tenant_id FK NOT NULL`, `paciente_id FK UNIQUE NOT NULL`, `updated_by FK→Usuario`, `updated_at:timestamptz`.
- Hallazgo: `id:uuid PK`, `odontograma_id FK`, `pieza:int` (FDI 11–48), `cara:enum?`, `estado:text` (vocabulario 18 estados tipo DentalSoft: sano, caries, obturación, corona, endodoncia, implante, ...), `fecha:date`, `observacion:text?`.
- Constraints: pieza válida FDI; solo edita `odontologo`. Índices: `(odontograma_id, pieza)`.

### Presupuesto (+ ItemPresupuesto)
- Atributos: `id:uuid PK`, `tenant_id FK NOT NULL`, `paciente_id FK NOT NULL`, `odontologo_id FK`, `estado:enum(borrador,enviado,aprobado,rechazado,parcialmente_cobrado,cobrado)`, `total:numeric`, `sena_requerida:numeric?`, `token_publico:uuid UNIQUE` (aprobación online), `valido_hasta:date?`.
- Ítem: `id FK`, `nomenclador_id FK?`, `descripcion:text`, `cantidad:int`, `precio_unit:numeric`, `cobertura_os:numeric?`.
- Constraints: total = suma de ítems; cambio de estado solo por flujo válido; aprobación online registra quién/cuándo/IP. Índices: `(tenant_id, estado)`, `token_publico`.

### MovimientoCaja
- Atributos: `id:uuid PK`, `tenant_id FK NOT NULL`, `fecha:timestamptz DEFAULT now()`, `tipo:enum(ingreso,egreso)`, `medio:enum(efectivo,mp_link,mp_terminal,transferencia,os)`, `monto:numeric NOT NULL`, `turno_id FK?`, `presupuesto_id FK?`, `usuario_id FK NOT NULL` (quién), `origen:text` (mostrador/portal/webhook), `concepto:text`, `anulacion_de FK?` (nunca borrado físico).
- Constraints: **trazabilidad total** — sin UPDATE destructivo (anulación con contra-asiento); monto > 0. Índices: `(tenant_id, fecha)`, `(medio, fecha)`.

### Comprobante (ARCA-preparado)
- Atributos: `id:uuid PK`, `tenant_id FK NOT NULL`, `movimiento_id FK?`, `tipo:text` (recibo/factura_manual v1), `numero:text?`, `emisor:enum(manual,arca) DEFAULT manual`, `payload:jsonb` (datos fiscales), `cae:text?`, `estado:enum(pendiente,emitido,anulado)`.
- Relaciones: el adapter `Facturador.emitir(comprobante)` en v1 lo marca manual; en fase 2 llama a ARCA y completa `cae`. Índices: `(tenant_id, estado)`.

### ObraSocial / Nomenclador
- ObraSocial: `id PK`, `tenant_id FK?` (catálogo global + convenios por tenant), `nombre:text`, `codigo:text`, `activa:bool`.
- Nomenclador: `id PK`, `obra_social_id FK NOT NULL`, `codigo:text` (p. ej. 01.01), `practica:text`, `arancel:numeric`, `copago:numeric?`, `vigencia_desde:date`.
- Constraints: `(obra_social_id, codigo, vigencia_desde)` único. Índices: `(obra_social_id, codigo)`, búsqueda trigram en `practica`.

### Borrado lógico (transversal, RN-SEG-06)
- Todas las tablas de negocio llevan `deleted_at:timestamptz?` + `deleted_by FK→Usuario?` (vía `AuditMixin` en C-02); el borrado es lógico y restaurable por `admin`.
- El flag `activo:bool` es on/off operativo (profesional que se va, sillón en mantenimiento), distinto del borrado: desactivar no borra, borrar no desactiva.
- Prohibido el borrado físico salvo purga explícita, auditada y con confirmación; `MovimientoCaja` nunca se purga (append-only, RN-CJ-01).

## Seed data inicial

- Tenant demo (`slug=demo`), 1 `admin`, 1 `recepcion`, 2 profesionales, 3 sillones ("Sillón 1–3"), catálogo OS nacional mínimo + 20 prácticas de nomenclador, plantillas WA (recordatorio 24h/2h, confirmación, oferta de lista de espera), aranceles particulares base, usuario paciente de prueba. Migración inicial crea `tenant_id` + índices de antisolapamiento.
