# frontend-foundation Specification

## Purpose
Define el cascarón de la SPA React que hospeda la app interna y el portal público, con superficies, tema y convenciones listas para cada feature.

## Requirements

### Requirement: Superficies privada y públicas

El sistema SHALL enrutar `/app/*` como superficie privada (requiere sesión JWT; sin sesión redirige al login) y `/reservar/*` y `/p/*` como superficies públicas sin autenticación.

#### Scenario: Acceso privado sin sesión

- **WHEN** un visitante sin sesión abre `/app/agenda`
- **THEN** es redirigido al login sin mostrar contenido interno

#### Scenario: Acceso público sin sesión

- **WHEN** un visitante sin sesión abre `/reservar/demo` o `/p/turno/<token>`
- **THEN** la página pública carga sin pedir login

### Requirement: Tema Tailwind v4 CSS-first

El sistema SHALL configurar Tailwind v4 con `@import "tailwindcss"` + tokens semánticos en `@theme` (sin archivo de config), base `* @apply border-border` y `body @apply bg-background text-foreground antialiased`.

#### Scenario: Build de estilos

- **WHEN** se compila el frontend
- **THEN** no existe `tailwind.config.*` y los tokens del tema resuelven en las clases usadas

### Requirement: Cliente API tipado con tipado estricto

El sistema SHALL exponer un cliente API tipado bajo `tsconfig` estricto (sin `any`), componentes en `PascalCase`, y superficies públicas redactadas en rioplatense con precios en ARS.

#### Scenario: Chequeo de tipos

- **WHEN** se ejecuta `tsc --noEmit`
- **THEN** el proyecto compila sin errores ni usos de `any`

#### Scenario: Texto público

- **WHEN** se renderiza una ruta pública
- **THEN** los textos usan voseo rioplatense y los montos se muestran en ARS

### Requirement: Layout raíz src/test única del frontend (§5)

El sistema SHALL mantener todo el código frontend bajo `frontend/src/`
(con `frontend/src/index.html` como entry) y SHALL reservar
`frontend/test/` (junto al código del lado, con `.gitkeep` si vacía) como
única ubicación para tests frontend. Los manifiestos y configs frontend
SHALL vivir en `frontend/`: `frontend/package.json`
(+ `package-lock.json`), `frontend/tsconfig.json`
(`include = ["src", "test"]`), `frontend/tsconfig.node.json`,
`frontend/vite.config.ts` (`root = "src"`), `frontend/eslint.config.js`
y `frontend/Dockerfile` (nombre canónico KB 08). Ningún manifiesto
frontend en raíz (`package.json`, `tsconfig*.json`, `vite.config.ts`,
`eslint.config.js`, `Dockerfile.frontend`) SHALL existir.

#### Scenario: Árbol frontend canónico

- **WHEN** se inspecciona el árbol del repo
- **THEN** el código productivo vive bajo `frontend/src/`, cualquier test
  futuro vive bajo `frontend/test/`, los manifiestos viven en `frontend/`,
  y NO existe `src/frontend/`, ni `test/frontend/`, ni manifiesto frontend
  en raíz, ni una segunda ubicación de tests
