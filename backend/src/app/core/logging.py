"""Logger estructurado sin PHI (R9: nunca datos de salud en logs)."""
import json
import logging
from typing import Any

_PHI_KEYS = frozenset(
    {
        "diagnostico",
        "historia_clinica",
        "odontograma",
        "hallazgo",
        "pieza",
        "tratamiento",
        "evolucion",
        "consentimiento",
        "dni",
        "telefono",
        "email",
    }
)


def redact(obj: Any) -> Any:
    """Reemplaza valores de claves sensibles por '[redacted]' (recursivo)."""
    if isinstance(obj, dict):
        return {k: ("[redacted]" if k.lower() in _PHI_KEYS else redact(v)) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [redact(v) for v in obj]
    return obj


class JsonFormatter(logging.Formatter):
    def format(self, record: logging.LogRecord) -> str:
        payload = {"level": record.levelname, "logger": record.name, "message": record.getMessage()}
        extra = {k: v for k, v in record.__dict__.items() if k not in ("message", "msg", "args", "levelname", "levelno", "pathname", "filename", "module", "exc_info", "exc_text", "stack_info", "lineno", "funcName", "created", "msecs", "relativeCreated", "thread", "threadName", "processName", "process", "name")}
        if extra:
            payload["extra"] = redact(extra)
        return json.dumps(payload, ensure_ascii=False)


def get_logger(name: str) -> logging.Logger:
    logger = logging.getLogger(name)
    if not logger.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(JsonFormatter())
        logger.addHandler(handler)
    logger.setLevel(logging.INFO)
    logger.propagate = False
    return logger
