# Spec Delta

## Purpose

Re-mapear el layout frontend del contenedor por lado con configs en raíz
(opción 1 de `restructure-por-lado`) al árbol KB 08 literal (opción 2):
manifiestos y configs DENTRO de `frontend/`, sin cambiar superficies, tema
ni convenciones.

## MODIFIED Requirements

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
