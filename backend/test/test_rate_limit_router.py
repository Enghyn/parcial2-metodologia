"""Integración C-10: rate limiter público (C-10, D8).

Prueba la clase RateLimiter directamente (sin efectos de BD) y el comportamiento
HTTP de los endpoints con límite de escritura.
"""
from __future__ import annotations

from datetime import UTC

import pytest
from fastapi.testclient import TestClient

from app.core.rate_limit import _LIMITERS, RateLimiter
from app.main import create_app

pytestmark = [pytest.mark.integration]


def _limpiar_limiters():
    _LIMITERS.clear()


def test_rate_limiter_bloquea_despues_de_n():
    _limpiar_limiters()
    lim = RateLimiter(max_requests=3, window_seconds=60, clock=lambda: 1000.0)
    assert lim.check("ip1").allowed is True
    assert lim.check("ip1").allowed is True
    assert lim.check("ip1").allowed is True
    resultado = lim.check("ip1")
    assert resultado.allowed is False
    assert resultado.retry_after > 0


def test_rate_limiter_otra_ip_no_afectada():
    _limpiar_limiters()
    lim = RateLimiter(max_requests=2, window_seconds=60, clock=lambda: 1000.0)
    assert lim.check("ip1").allowed is True
    assert lim.check("ip1").allowed is True
    assert lim.check("ip1").allowed is False
    # Otra IP independiente
    assert lim.check("ip2").allowed is True


def test_rate_limiter_ventana_expirada_libera():
    _limpiar_limiters()
    ahora_rel = [1000.0]

    def clock():
        return ahora_rel[0]

    lim = RateLimiter(max_requests=2, window_seconds=60, clock=clock)
    assert lim.check("ip1").allowed is True
    assert lim.check("ip1").allowed is True
    assert lim.check("ip1").allowed is False
    # Avanzar el reloj más allá de la ventana
    ahora_rel[0] = 1000.0 + 61
    assert lim.check("ip1").allowed is True


def test_rate_limit_endpoint_escritura_429():
    """11 POST a /pre-reservas (bucket escritura, max 10) → 429 en la 11ª."""
    _limpiar_limiters()
    app = create_app()
    client = TestClient(app)
    base = "/api/v1/public"
    from datetime import datetime

    base_time = datetime(2027, 12, 1, 9, 0, tzinfo=UTC)
    for i in range(10):
        inicio = base_time.replace(minute=base_time.minute + i * 5)
        r = client.post(
            f"{base}/pre-reservas",
            json={
                "prestacion": "Limpieza",
                "duracion_min": 30,
                "inicio": inicio.isoformat(),
                "profesional_id": "00000000-0000-0000-0000-000000000001",
                "sillon_id": "00000000-0000-0000-0000-000000000002",
            },
        )
        # Las primeras pueden ser 201 o 409 (dependiendo de si existen los recursos),
        # pero nunca 429 mientras no se agote el bucket
        assert r.status_code != 429, f"Request {i+1} inesperadamente 429: {r.text}"
    # La 11ª debe ser 429 (rate limited)
    r = client.post(
        f"{base}/pre-reservas",
        json={
            "prestacion": "Limpieza",
            "duracion_min": 30,
            "inicio": base_time.replace(hour=10).isoformat(),
            "profesional_id": "00000000-0000-0000-0000-000000000001",
            "sillon_id": "00000000-0000-0000-0000-000000000002",
        },
    )
    assert r.status_code == 429, r.text
    assert "Retry-After" in r.headers
    _limpiar_limiters()
