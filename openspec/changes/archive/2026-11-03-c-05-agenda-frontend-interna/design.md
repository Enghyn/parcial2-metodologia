# Design — C-05: agenda-frontend-interna

## Context

C-04 dejó el contrato HTTP estable (`GET/POST /api/v1/turnos`, `PATCH /api/v1/turnos/:id/estado`, RBAC por rol) y el frontend tiene el cascarón: router con `/app/agenda` → placeholder `AppHomePage`, `useAuthStore` solo con `accessToken`, cliente API que inyecta Bearer, Tailwind v4 CSS-first, tsconfig strict. No hay runner de tests frontend (no Vitest); la verificación es `tsc --noEmit` + `eslint` + `vite build`, más smoke E2E con `playwright-cli`. Ver proposal.md (Why/What) y `openspec/specs/agenda/spec.md` (contrato HTTP) / `openspec/specs/auth/spec.md` (login).

## Goals / Non-Goals

**Goals:**
- Reemplazar el placeholder de `/app/agenda` por la agenda real con columnas por sillón, navegación de fecha y código de colores por estado.
- Cablear el login real (`POST /api/v1/auth/login`) + perfil (`GET /api/v1/auth/me`) + persistencia del token.
- Proveer modal de alta y acción rápida de cambio de estado, reutilizando los endpoints de C-04.
- Mantener tipado estricto (R7), gating cosmético por rol (R8), superficies en es-AR (R10).

**Non-Goals:**
- No modificar backend ni migraciones (R5).
- No agregar Vitest ni otro runner de tests frontend (alcance acotado); verificación por type-check/build + Playwright smoke.
- No implementar catálogo de prestaciones ni duración automática (KB 10, fase 2): el modal carga `duracion_min` manualmente.
- No implementar bloqueos en la UI (US-003) ni agenda propia por odontólogo ni máquina de estados estricta (deferido a cambios futuros; C-04 acepta cualquier valor del catálogo).
- No implementar vistas de pacientes/odontograma/caja (C-07/C-08).

## Decisions

### D1 — Estructura de carpetas (espejo del backend por feature)

```
frontend/src/
├── app/
│   ├── AuthContext.tsx        # useAuthStore extendido (token + user + rol + persistencia)
│   ├── pages.tsx              # LoginPage real, AgendaPage wrapper, (resto placeholders)
│   └── router.tsx             # sin cambios de rutas; /app/agenda → AgendaPage
├── features/
│   ├── agenda/
│   │   ├── index.ts           # barrel público del feature
│   │   ├── AgendaPage.tsx     # vista principal (columnas + fecha + modal)
│   │   ├── AgendaColumn.tsx   # columna por sillón
│   │   ├── TurnoCard.tsx      # bloque de turno (color por estado)
│   │   ├── DateSelector.tsx   # hoy/prev/next
│   │   ├── TurnoModal.tsx     # alta de turno
│   │   ├── EstadoTurnoMenu.tsx# acción rápida cambio de estado
│   │   ├── estadoColor.ts     # mapa estado → clases Tailwind
│   │   └── types.ts           # tipos del feature (TurnoView, etc.)
│   └── auth/
│       ├── index.ts
│       ├── LoginForm.tsx
│       └── useAuth.ts         # hook login/logout/me
└── shared/
    └── api/
        ├── client.ts          # existente (sin cambios de contrato)
        ├── auth.ts            # login(), me() tipados
        └── agenda.ts          # listarTurnos, crearTurno, cambiarEstadoTurno tipados
```

Regla R7: componentes en `PascalCase`, funciones/variables en `camelCase`, sin `any`. Imports directos (sin barrel-file imports pesados; el barrel `features/agenda/index.ts` solo re-exporta el entrypoint).

### D2 — State management (Zustand)

- `useAuthStore` se extiende:
  ```ts
  interface AuthState {
    accessToken: string | null;
    user: UsuarioPerfil | null;   // { id, nombre, email, rol }
    login: (email: string, password: string) => Promise<void>;
    logout: () => void;
    hydrate: () => void;         // lee token de localStorage al montar
  }
  ```
  - `login` llama `api/auth.login`, guarda token + llama `me()`, persiste token en `localStorage` (`odonto.accessToken`).
  - `logout` limpia store + `localStorage`.
  - `hydrate` se invoca una vez en el montaje de `AppRouter` (o `RequireAuth`) para restaurar sesión tras recarga.
- `useAgendaStore` (nuevo, en `features/agenda`) guarda `fechaSeleccionada`, `turnos`, `sillones`, `profesionales`, `pacientes`, `loading`, `error` y acciones `cargar(fecha)`, `crear(datos)`, `cambiarEstado(id, estado)`. Reusa `Promise.all` para cargar sillones/profesionales/pacientes/turnos en paralelo (vercel-react-best-practices: start promises early, await late).
- No se usa SWR/React Query (no instalado); el store centraliza el fetch manual. Se evita duplicar requests con un flag `loading`.

### D3 — Data fetching y cliente API

- `shared/api/auth.ts`:
  ```ts
  export interface LoginInput { email: string; password: string; }  // extra no aplica (cliente)
  export interface TokenOut { access_token: string; token_type: "bearer"; expires_in: number; }
  export interface UsuarioPerfil { id: string; nombre: string; email: string; rol: "admin" | "recepcion" | "odontologo"; }
  export function login(input: LoginInput): Promise<TokenOut>;
  export function me(): Promise<UsuarioPerfil>;
  ```
- `shared/api/agenda.ts`:
  ```ts
  export interface TurnoOut { id: string; paciente_id: string; profesional_id: string; sillon_id: string; prestacion: string; inicio: string; fin: string; duracion_min: number; estado: EstadoTurno; token_publico: string; sena_monto: string; notas: string | null; created_at: string; updated_at: string; }
  export type EstadoTurno = "reservado" | "confirmado" | "presente" | "atendido" | "cancelado";
  export interface TurnoCreateInput { paciente_id: string; profesional_id: string; sillon_id: string; prestacion: string; inicio: string; duracion_min: number; sena_monto?: string; notas?: string | null; }
  export function listarTurnos(filtros: { fecha?: string; profesional_id?: string; sillon_id?: string }): Promise<TurnoOut[]>;
  export function crearTurno(input: TurnoCreateInput): Promise<TurnoOut>;
  export function cambiarEstadoTurno(id: string, estado: EstadoTurno): Promise<TurnoOut>;
  ```
- `listarTurnos` construye query string con `URLSearchParams` (sin `any`). `inicio` se envía en ISO 8601 UTC.
- El cliente existente ya inyecta Bearer desde `useAuthStore.getState()`. Se reusa sin cambios; `login` se llama sin token (el cliente agrega token si existe, inofensivo).
- Sillones/profesionales/pacientes: no hay endpoints dedicados de listado en C-04 (pacientes en C-07). Para el modal de alta se necesitan listas. Decisión: en C-05 se consumen endpoints existentes si existen; de lo contrario se dejan como datos mockeados/estáticos del seed (3 sillones, 2 profesionales, 2 pacientes) cargados por una función `cargarCatalogos()` que llama a endpoints que C-07 agregará, con fallback a constantes del seed para no bloquear. **Open question resuelta**: para no bloquear C-05, el modal usa listas provistas por un `CatalogosProvider` que intenta `GET /api/v1/sillones`, `GET /api/v1/profesionales`, `GET /api/v1/pacientes`; si responden 404, usa fallback estático del seed (Sillón 1/2/3, Dr. Pérez/Dra. Gómez, María López/Juan Pérez). Esto mantiene la UI funcional y se cablea a endpoints reales en C-07 sin cambio de contrato de la agenda. (Alternativa considerada: hardcodear solo ids del seed; rechazada porque acopla la UI a ids fijos.)

### D4 — Componentes y árbol de render

```
AgendaPage
├── header: título + usuario/rol + botón "Cerrar sesión" + botón "Nuevo turno" (gated)
├── DateSelector (fecha actual/anterior/siguiente)
├── grid: AgendaColumn × N (sillones activos)
│   └── TurnoCard × M (turnos del sillón)
│       └── EstadoTurnoMenu (acción rápida)
└── TurnoModal (portal/overlay) — alta de turno
```

- `AgendaColumn` recibe `sillon` y `turnos` filtrados por `sillon_id`; ordena por `inicio`.
- `TurnoCard` muestra horario (inicio–fin en hora local `es-AR`), paciente (nombre resuelto por `paciente_id` contra catálogo), profesional, prestación, estado badge.
- `EstadoTurnoMenu` ofrece `presente` y `cancelado` (y `confirmado` si rol admin/recepcion); invoca `cambiarEstadoTurno`.
- `TurnoModal` usa `<form>` controlado; validación mínima en cliente (campos requeridos, `duracion_min > 0`); el backend valida el resto (R8: no confiar en frontend para permisos, pero validación de forma es UX).

### D5 — Mapa de colores por estado (Tailwind v4)

Definido en `estadoColor.ts` como función pura `estadoClasses(estado): string` (sin `any`), usando clases semánticas de Tailwind:

| Estado | Clases (borde + fondo + texto) |
|---|---|
| `reservado` | `border-sky-300 bg-sky-50 text-sky-900` |
| `confirmado` | `border-blue-400 bg-blue-50 text-blue-900` |
| `presente` | `border-amber-400 bg-amber-50 text-amber-900` |
| `atendido` | `border-emerald-400 bg-emerald-50 text-emerald-900` |
| `cancelado` | `border-rose-300 bg-rose-50 text-rose-900 line-through opacity-60` |

Se evita hardcodear colores en componentes; todo pasa por `estadoClasses`. Se podría extender `@theme` con tokens `--color-estado-*`, pero se mantiene con clases utilitarias estándar para no tocar `index.css` (alcance acotado). Decisión: si en el futuro se requiere dark mode, migrar a tokens `@theme`.

### D6 — Formato de fechas y horas

- Fecha seleccionada como `string` ISO `YYYY-MM-DD` (zona local del navegador). Se construye el rango del día en UTC para el filtro `fecha` del backend (el backend filtra por fecha calendario en UTC según C-04). Para evitar desfases, se envía `fecha=YYYY-MM-DD` (date) y el backend resuelve el día en UTC. Se asume que el usuario opera en la zona horaria del consultorio (AR, UTC-3); los turnos se crean con `inicio` en ISO UTC.
- Horas en bloques: `new Date(inicio).toLocaleTimeString("es-AR", { hour: "2-digit", minute: "2-digit" })`.
- `DateSelector`: botones "Anterior", "Hoy", "Siguiente" que ajustan la fecha con `date-fns`? No instalado. Se usa `Date` nativo: `addDays(date, ±1)` helper en `features/agenda/dateUtils.ts` (puro, testeable por tsc). Evita nueva dependencia.

### D7 — Auth wiring (login)

- `LoginPage` se reemplaza por un componente que renderiza `LoginForm`. `LoginForm` usa `useAuthStore().login`. En éxito, `navigate("/app/agenda")`. En error, muestra `error.message` (del `ApiError`).
- `RequireAuth` lee `accessToken` del store; si null redirige a `/login`. Tras `hydrate()`, si hay token persistido, se restaura.
- `hydrate()` se llama en `main.tsx` antes de render, o en `AppRouter` con `useEffect`. Se prefiere llamar en `main.tsx` sincrónicamente leyendo `localStorage` para evitar flash de login. Implementación: `useAuthStore.getState().hydrate()` antes de `createRoot().render`.

### D8 — Verificación (sin runner frontend)

- Gate 1: `npm run lint` (eslint, max-warnings 0) — sin `any`, sin unused.
- Gate 2: `npm run build` (tsc --noEmit && vite build) — tipado estricto + build.
- Gate 3 (opcional): smoke E2E con `playwright-cli` contra stack levantado: login con `recepcion@consultorio.com` / `recepcion123`, ver agenda, crear turno, marcar presente. Se documenta como task pero no bloquea si Playwright no está disponible.
- No se agregan tests unitarios frontend (no runner). Los helpers puros (`estadoClasses`, `addDays`, formateo de fecha) se verifican por tsc + revisión.

### D9 — Manejo de errores

- `crearTurno`/`cambiarEstadoTurno` capturan `ApiError` y exponen `message` al UI (modal o toast simple). No se introduce librería de toast; se usa un estado `error` local en el modal/store y se renderiza inline (R10: mensajes en es-AR; el backend ya responde en es-AR).

### D10 — Riesgos

- **[Catálogos no disponibles hasta C-07]** → fallback estático del seed en `CatalogosProvider` (D3); se cablea a endpoints reales en C-07 sin cambio de contrato.
- **[Zona horaria]** → filtro por `fecha` date (UTC) y `inicio` ISO UTC; se documenta que el consultorio opera en AR.
- **[Sin tests automatizados frontend]** → gates tsc/eslint/build + smoke Playwright; se acepta como limitación del MVP.
- **[Condición de carrera en alta]** → el backend valida antisolapamiento; la UI solo muestra el 409. Aceptado (igual que C-04).
- **[Persistencia de token en localStorage (XSS)]** → R9: no se loguean tokens; el MVP académico acepta localStorage. Alternativa (httpOnly cookie) requeriría backend changes (fuera de scope). Documentado.

## Migration Plan

- Sin migración Alembic (sin cambio de esquema; R5).
- Deploy: implementar los archivos del árbol D1, actualizar `pages.tsx`/`AuthContext.tsx`, correr `npm run lint && npm run build`.
- Rollback: revertir los archivos frontend; no hay datos ni esquema que revertir. El placeholder anterior queda en git history.

## Open Questions

- Ninguna bloquea la implementación. Nota para C-07: cablear `CatalogosProvider` a los endpoints reales de pacientes/profesionales/sillones y reemplazar el fallback estático. Nota para C-06: reusar `estadoClasses`, `DateSelector` y el patrón de columnas para el portal público de huecos.