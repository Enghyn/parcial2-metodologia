# Archive Note — C-01-foundation-setup (2026-10-06)

## Estado
Archivado con `openspec archive C-01-foundation-setup -y`. Tasks 16/16 [x].
Specs sincronizadas: `backend-foundation` (6), `frontend-foundation` (4),
`local-platform` (5). `openspec validate --all` en verde (3 specs).
Layout canónico §5: raíz `src/backend` + `src/frontend`, raíz
`test/backend` + `test/frontend`; sin carpetas sueltas `backend/`/`frontend`.

## Limitación conocida (NO bloquea el archive)
- Sin Docker en la máquina: `docker compose up --build` + `alembic upgrade head`
  real contra PG15 NO verificados en vivo (YAML parseado + `uvicorn` local 200
  en su lugar). Re-verificar compose + migraciones en máquina con Docker antes
  de C-02.
- Sin repo git en la máquina: los `git mv` del §5 se ejecutaron como `Move-Item`.
