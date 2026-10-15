# Archive note — mudanza-completa-configs

- Archivado: 2026-10-15 vía `openspec archive mudanza-completa-configs -y` (tercero/ÚLTIMO en orden 1→2→3 — sus paths son los vigentes).
- Deltas sincronizados a `openspec/specs/`: backend-foundation (~1), frontend-foundation (~1), local-platform (~1) — paths vigentes `backend/...` + `frontend/...`.
- Estado final del árbol: `backend/{src,test,pyproject.toml,alembic.ini,Dockerfile}` + `frontend/{src,test,package.json,...}` + configs raíz (compose, .env.example, CI, README).
- Warning no bloqueante: deltas `Purpose` ignorados (specs ya tienen Purpose).
- Estado: tasks todas [x] en working tree, sin commitear (R11).
- Limitación conocida (no bloqueante): sin Docker en esta máquina — `compose up` / `alembic upgrade` reales contra PG15 verificados por parse + uvicorn local; CI pendiente.
