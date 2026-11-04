# Tasks — C-06b public patient privacy

> **TDD estricto.** Comandos backend desde `backend/`. La suite de integración requiere PostgreSQL migrado y sembrado.

## 1. Safety net y RED

- [x] 1.1 Correr `python -m pytest -q` con `DATABASE_URL` y registrar la línea base (esperado: 224 passed, 7 skipped).
- [x] 1.2 **RED**: agregar a `test_public_service.py` casos que fallen: paciente existente con teléfono distinto conserva el original; email distinto conserva el original; DNI con `deleted_at` responde 409 y no reactiva; paciente nuevo se crea.

## 2. Green del servicio

- [x] 2.1 **GREEN**: modificar `_find_or_create_paciente` para que un paciente activo se reutilice sin asignar `telefono`/`email`.
- [x] 2.2 **GREEN**: si el DNI existe con `deleted_at` no nulo, lanzar `HTTPException(409, "Contactá al consultorio...")` sin tocar la ficha.
- [x] 2.3 **TRIANGULATE**: agregar el caso de paciente nuevo con email nulo y el caso de email existente que no debe borrarse.
- [x] 2.4 **REFACTOR**: extraer un helper `_buscar_por_dni` y dejar el flujo en tres ramas legibles; correr la suite pública.

## 3. Verificación

- [x] 3.1 Correr `python -m pytest test/test_public_service.py test/test_public_router.py -q` con PostgreSQL.
- [x] 3.2 Correr toda la suite `python -m pytest -q` con PostgreSQL.
- [x] 3.3 Ejecutar `openspec validate "c-06b-public-patient-privacy" --strict`.

## Workflow follow-up

- Revisión humana del design antes de aplicar.
- Aplicar con TDD y actualizar los checkboxes.
- Archivar con `openspec archive "c-06b-public-patient-privacy" -y`.
- Continuar con `chore-quality-gate`.
