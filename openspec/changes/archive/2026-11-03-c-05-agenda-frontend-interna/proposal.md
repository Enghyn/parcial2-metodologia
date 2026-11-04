# Proposal — C-05: agenda-frontend-interna

## Why

C-04 dejó listos los endpoints internos de agenda (`GET/POST /api/v1/turnos`, `PATCH /api/v1/turnos/:id/estado`) y el RBAC, pero la superficie `/app/agenda` sigue siendo un placeholder (`AppHomePage`) y el `AuthContext` no invoca `POST /api/v1/auth/login`. Sin esta capa, recepción y odontólogos no pueden operar la agenda diaria (US-001, US-002, Flujo 2) ni marcar estados (`presente`/`cancelado`), y C-07/C-08 quedan bloqueados. Ahora que el contrato HTTP está estable, se puede construir la UI estrictamente tipada sin tocar backend.

## What Changes

- Nueva capability `internal-agenda`: contrato de comportamiento de la agenda interna en React (visualización por sillón, navegación de fecha, código de colores por estado, modal de alta, acción rápida de cambio de estado).
- Implementación frontend bajo `frontend/src/features/agenda/` y `frontend/src/app/pages.tsx` (reemplazo del placeholder `AppHomePage` por la vista real de agenda), reutilizando el cliente API tipado y el store de auth.
- Cableado de autenticación: formulario de login (`/login`) que invoca `POST /api/v1/auth/login`, persiste el `access_token` en `useAuthStore` y redirige a `/app/agenda`; cierre de sesión con limpieza de token (US-010).
- Funciones tipadas para los endpoints de agenda (`listarTurnos`, `crearTurno`, `cambiarEstadoTurno`) y para auth (`login`, `me`) en `shared/api/`.
- Componentes en `PascalCase` sin `any` (R7): `AgendaPage`, `AgendaColumn`, `TurnoCard`, `TurnoModal`, `EstadoTurnoBadge`, `DateSelector`, `LoginForm`.
- Sin cambios de backend ni migraciones Alembic. Sin nueva dependencia de test runner (verificación por `tsc --noEmit` + `eslint` + `vite build`; smoke E2E con `playwright-cli` si está disponible).

## Capabilities

### New Capabilities
- `internal-agenda`: Comportamiento observable de la agenda interna del consultorio: vista diaria en columnas por sillón físico (Sillón 1/2/3), selector de fecha (hoy/anterior/siguiente), código de colores por estado del turno, modal de alta de turno y acción rápida para actualizar el estado, con gating cosmético por rol (R8) y superficies en es-AR (R10).

### Modified Capabilities
- (ninguna — el contrato HTTP de `agenda` y `auth` no cambia; este change consume los endpoints existentes sin modificar requisitos).

## Impact

- **Código**: `frontend/src/app/pages.tsx` (reemplazo de `AppHomePage`/`LoginPage` placeholder), `frontend/src/app/AuthContext.tsx` (extensión del store con `user`/`rol` y persistencia opcional), `frontend/src/shared/api/client.ts` (nuevas funciones tipadas), nuevo árbol `frontend/src/features/agenda/*`, `frontend/src/features/auth/*`.
- **Dependencias**: sin nuevas (reusa React 18, react-router-dom, Zustand, Tailwind v4 ya instalados). No se agrega Vitest (R: alcance acotado); verificación por type-check/build y Playwright.
- **Tests**: no hay runner frontend. Verificación: `npm run lint`, `npm run build` (incluye `tsc --noEmit`). Smoke E2E opcional con `playwright-cli` contra el stack levantado.
- **Consumidores futuros**: C-07 (clinica/odontograma) y C-08 (caja) reusan el store de auth, el cliente API y el patrón de modal/columnas. C-06 (reserva pública) reusa el patrón de columnas/huecos para el portal público.