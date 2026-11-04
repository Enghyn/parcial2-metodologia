"""Carreras de C-07 sin base: el UNIQUE(dni) se traduce a 409."""
import pytest
from fastapi import HTTPException
from sqlalchemy.exc import IntegrityError

from app.modules.clinica.schemas import PacienteCreate
from app.modules.clinica.service import PacienteService


class _SesionDuplicada:
    def __init__(self) -> None:
        self.rolled = False

    def scalar(self, *args: object, **kwargs: object) -> object:
        return None

    def add(self, entidad: object) -> None:
        self.entidad = entidad

    def commit(self) -> None:
        raise IntegrityError("INSERT", {}, Exception("duplicate"))

    def rollback(self) -> None:
        self.rolled = True


def test_crear_duplicado_por_carrera_responde_409() -> None:
    sesion = _SesionDuplicada()
    with pytest.raises(HTTPException) as exc:
        PacienteService(sesion).crear(  # type: ignore[arg-type]
            PacienteCreate(nombre="Test", dni="1", telefono="2")
        )
    assert exc.value.status_code == 409
    assert sesion.rolled is True
