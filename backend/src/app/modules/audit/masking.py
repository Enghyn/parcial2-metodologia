"""Enmascarado de campos sensibles (salud y PII) en `diff` de auditoría (R9)."""
from __future__ import annotations

from typing import Any

REDACTED = "[REDACTED]"

# Lista de denegación: cualquier clave (case-insensitive) presente acá se redacta.
SENSITIVE_FIELDS: frozenset[str] = frozenset(
    {
        "motivo",
        "motivo_sobreturno",
        "observacion",
        "observaciones",
        "diagnostico",
        "diagnosticos",
        "documento",
        "documentos",
        "dni",
        "notas",
        "nota",
        "texto",
        "anamnesis",
        "antecedentes",
        "tratamiento",
        "evolucion",
        "evoluciones",
        "consentimiento",
        "password",
        "password_hash",
        "token",
        "secret",
    }
)


def _es_sensible(clave: str) -> bool:
    return clave.strip().lower() in SENSITIVE_FIELDS


def enmascarar(valor: Any) -> Any:
    """Redacta recursivamente los campos sensibles de un `diff` (dict/list/primitivo)."""
    if isinstance(valor, dict):
        resultado: dict[str, Any] = {}
        for clave, contenido in valor.items():
            if _es_sensible(str(clave)):
                resultado[clave] = REDACTED
            else:
                resultado[clave] = enmascarar(contenido)
        return resultado
    if isinstance(valor, list):
        return [enmascarar(item) for item in valor]
    if isinstance(valor, tuple):
        return [enmascarar(item) for item in valor]
    return valor


__all__ = ["REDACTED", "SENSITIVE_FIELDS", "enmascarar"]
