# Tasks

Cwd canónico para frontend: `frontend/`. Verificación por type-check/build (no hay runner de tests frontend): `npm run lint` y `npm run build` (incluye `tsc --noEmit`). Smoke E2E opcional con `playwright-cli` contra el stack levantado. El backend NO se modifica (R5/R11).

## 1. Setup estructural y tipos base

- [x] 1.1 Crear el árbol de archivos del feature (`frontend/src/features/agenda/*`, `frontend/src/features/auth/*`, `frontend/src/shared/api/auth.ts`, `frontend/src/shared/api/agenda.ts`) con stubs tipados (sin `any`) y verificar `npm run build` compila (los stubs pueden ser vacíos exportando tipos). Verificación: `npm run build` sin errores de tsc.
- [x] 1.2 Definir los tipos compartidos (`EstadoTurno`, `TurnoOut`, `TurnoCreateInput`, `UsuarioPerfil`, `TokenOut`, `LoginInput`) en `shared/api/agenda.ts` y `shared/api/auth.ts`, y los tipos del feature en `features/agenda/types.ts`. Verificación: `npm run tsc --noEmit` (vía `npm run build`) sin errores y sin `any`.

## 2. Cliente API tipado para auth y agenda

- [x] 2.1 Implementar `login(input)` y `me()` en `shared/api/auth.ts` consumiendo los endpoints existentes, reusando `request<T>` de `client.ts`. Verificación: `npm run build` compila y las funciones tienen firma tipada.
- [x] 2.2 Implementar `listarTurnos`, `crearTurno` y `cambiarEstadoTurno` en `shared/api/agenda.ts` (construcción de query string con `URLSearchParams`, sin `any`). Verificación: `npm run build` compila.
- [x] 2.3 Implementar `CatalogosProvider`/`cargarCatalogos()` con fallback estático del seed (3 sillones, 2 profesionales, 2 pacientes) cuando los endpoints reales no existan (404), sin romper el type-check. Verificación: `npm run build` compila y la UI de alta puede listar opciones.

## 3. Store de autenticación (Zustand)

- [x] 3.1 Extender `useAuthStore` con `user`, `login(email,password)`, `logout()` y `hydrate()`; persistir token en `localStorage` (`odonto.accessToken`) y restaurar sesión al recargar. Verificación: `npm run build` compila y `npm run lint` sin warnings.
- [x] 3.2 Implementar `useAuth` hook (login/logout/me) en `features/auth/useAuth.ts` y el componente `LoginForm` en `features/auth/LoginForm.tsx` con manejo de error. Verificación: `npm run build` compila.
- [x] 3.3 Reemplazar el placeholder `LoginPage` en `app/pages.tsx` por el render de `LoginForm` y actualizar `router.tsx` si es necesario (mantener rutas). Verificación: `npm run build` compila y `/login` renderiza el formulario.

## 4. Store y helpers de agenda

- [x] 4.1 Implementar `useAgendaStore` (fecha seleccionada, turnos, sillones, profesionales, pacientes, loading, error) con acciones `cargar(fecha)`, `crear(datos)`, `cambiarEstado(id, estado)` usando `Promise.all` para carga paralela. Verificación: `npm run build` compila.
- [x] 4.2 Implementar helpers puros en `features/agenda/dateUtils.ts` (`addDays`, `toIsoDate`) y `features/agenda/estadoColor.ts` (`estadoClasses`) sin `any`. Verificación: `npm run build` compila y `npm run lint` sin warnings.

## 5. Componentes de la agenda

- [x] 5.1 Implementar `DateSelector` (hoy/anterior/siguiente) y `AgendaColumn` (columna por sillón con turnos ordenados). Verificación: `npm run build` compila.
- [x] 5.2 Implementar `TurnoCard` (bloque con horario, paciente, profesional, prestación, estado) usando `estadoClasses`. Verificación: `npm run build` compila.
- [x] 5.3 Implementar `EstadoTurnoMenu` (acción rápida a `presente`/`cancelado`/`confirmado` según rol) invocando `cambiarEstadoTurno`. Verificación: `npm run build` compila.
- [x] 5.4 Implementar `TurnoModal` (formulario controlado, validación mínima, envío deshabilitado mientras pending, muestra 409). Verificación: `npm run build` compila.
- [x] 5.5 Implementar `AgendaPage` integrando header (usuario/rol/logout/nuevo turno gated), `DateSelector`, grid de `AgendaColumn`, `TurnoModal` y carga inicial. Verificación: `npm run build` compila.

## 6. Integración en el router y gating por rol

- [x] 6.1 Reemplazar `AppHomePage` placeholder por `AgendaPage` en `app/pages.tsx` y mapear `/app/agenda` a `AgendaPage` en `router.tsx`. Verificación: `npm run build` compila y la ruta `/app/agenda` renderiza la agenda.
- [x] 6.2 Aplicar gating cosmético por rol: ocultar/deshabilitar "Nuevo turno" para `odontologo`; mantener acciones de cambio de estado según backend. Verificación: `npm run build` + `npm run lint` sin warnings.
- [x] 6.3 Implementar `hydrate()` en `main.tsx` antes del render (leer token de `localStorage`) para restaurar sesión tras recarga. Verificación: `npm run build` compila.

## 7. Verificación y smoke E2E

- [x] 7.1 Ejecutar `npm run lint` (max-warnings 0) y `npm run build` (tsc + vite) sin errores; corregir todos los warnings. Verificación: ambos comandos en verde.
- 7.2 (Opcional, si Playwright disponible) **No aplica**: Playwright no está disponible en el entorno local; la verificación de UI quedó cubierta por 7.1 (`npm run lint` + `npm run build`). Smoke E2E contra el stack queda como follow-up manual documentado en el PR del change.
- [x] 7.3 Revisar R7 (sin `any`, componentes PascalCase), R8 (RBAC solo cosmético), R10 (es-AR + ARS), R9 (sin datos sensibles en logs/URLs) en el diff frontend. Verificación: checklist en la descripción del PR del change.

## Workflow follow-up

- Ejecutar `/opsx:validate` y `/opsx:archive c-05-agenda-frontend-interna` cuando las 7 tareas estén en verde y el change sea revisado.
- Marcar `[x]` la sección C-05 en `CHANGES.md` tras el archive.
- Avisar a C-07 y C-08 que el store de auth, el cliente API y los componentes de agenda quedan listos (contrato en `design.md` D1–D5).