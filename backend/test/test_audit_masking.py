"""Tests unitarios de enmascarado de auditoría (C-20)."""
from app.modules.audit.masking import enmascarar


def test_campo_sensible_se_redacta() -> None:
    assert enmascarar({"observacion": "secreto"}) == {"observacion": "[REDACTED]"}


def test_campo_no_sensible_intacto() -> None:
    assert enmascarar({"prestacion": "Consulta"}) == {"prestacion": "Consulta"}


def test_anidado() -> None:
    assert enmascarar({"detalle": {"notas": "x", "monto": 10}}) == {
        "detalle": {"notas": "[REDACTED]", "monto": 10}
    }


def test_lista() -> None:
    assert enmascarar([{"diagnostico": "caries"}, {"monto": 5}]) == [
        {"diagnostico": "[REDACTED]"},
        {"monto": 5},
    ]


def test_none() -> None:
    assert enmascarar(None) is None
