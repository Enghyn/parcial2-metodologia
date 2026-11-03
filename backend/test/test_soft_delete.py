"""Guardas de borrado lógico (R13 / RN-SEG-02)."""
from datetime import UTC, datetime

import pytest

from app.core.errors import SoftDeleteError
from app.db.base import _reject_physical_delete
from app.modules.admin.models import Usuario
from app.modules.agenda.models import Sillon
from app.modules.clinica.models import Paciente


def test_paciente_conserva_la_fila_y_marca_deleted_at() -> None:
    paciente = Paciente(nombre="Ana Pérez", dni="30111222", telefono="1144556677")
    assert paciente.deleted_at is None

    paciente.soft_delete()

    assert paciente.nombre == "Ana Pérez"
    assert paciente.dni == "30111222"
    assert isinstance(paciente.deleted_at, datetime)
    assert paciente.deleted_at.tzinfo is not None


def test_delete_fisico_de_entidad_de_negocio_es_rechazado() -> None:
    with pytest.raises(SoftDeleteError):
        _reject_physical_delete(None, None, Paciente(nombre="Ana", dni="1", telefono="2"))


def test_delete_fisico_de_usuario_no_lo_bloquea_esta_guarda() -> None:
    _reject_physical_delete(None, None, Usuario(nombre="Admin", email="a@b.com", password_hash="x", rol="admin"))


def test_sillon_tambien_usa_borrado_logico() -> None:
    sillon = Sillon(nombre="Sillón 1")
    with pytest.raises(SoftDeleteError):
        _reject_physical_delete(None, None, sillon)


def test_deleted_at_es_zona_horaria_utc_cercana_al_presente() -> None:
    sillon = Sillon(nombre="Sillón 2")
    sillon.soft_delete()
    assert sillon.deleted_at is not None
    delta = datetime.now(UTC) - sillon.deleted_at
    assert delta.total_seconds() < 5
