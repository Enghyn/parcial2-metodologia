"""Tests puros del RateLimiter (C-10, D8)."""
from __future__ import annotations

import math

import pytest

from app.core.rate_limit import RateLimiter, RateLimitResult


def test_admite_hasta_el_maximo_y_rechaza_el_siguiente():
    clock = {"t": 0.0}
    lim = RateLimiter(max_requests=3, window_seconds=10.0, clock=lambda: clock["t"])
    assert lim.check("k").allowed is True
    assert lim.check("k").allowed is True
    assert lim.check("k").allowed is True
    r = lim.check("k")
    assert r.allowed is False
    assert r.retry_after > 0
    assert isinstance(r.retry_after, int)


def test_retry_after_en_segundos_mayor_a_cero():
    clock = {"t": 0.0}
    lim = RateLimiter(max_requests=1, window_seconds=5.0, clock=lambda: clock["t"])
    lim.check("k")
    r = lim.check("k")
    assert r.allowed is False
    assert r.retry_after >= 1
    assert r.retry_after <= 5


def test_ventana_se_reinicia_al_avanzar_el_reloj():
    clock = {"t": 0.0}
    lim = RateLimiter(max_requests=1, window_seconds=5.0, clock=lambda: clock["t"])
    assert lim.check("k").allowed is True
    assert lim.check("k").allowed is False
    clock["t"] = 5.1
    assert lim.check("k").allowed is True


def test_buckets_independientes_no_se_contaminan():
    clock = {"t": 0.0}
    lim = RateLimiter(max_requests=1, window_seconds=10.0, clock=lambda: clock["t"])
    assert lim.check("a").allowed is True
    assert lim.check("b").allowed is True
    assert lim.check("a").allowed is False
    assert lim.check("b").allowed is False


def test_claves_distintas_no_se_contaminan():
    clock = {"t": 0.0}
    lim = RateLimiter(max_requests=2, window_seconds=10.0, clock=lambda: clock["t"])
    lim.check("x")
    lim.check("x")
    # "y" tiene su propio bucket
    assert lim.check("y").allowed is True
    assert lim.check("y").allowed is True
    assert lim.check("y").allowed is False


def test_result_bool_iter_getitem():
    clock = {"t": 0.0}
    lim = RateLimiter(max_requests=1, window_seconds=10.0, clock=lambda: clock["t"])
    lim.check("k")
    r = lim.check("k")
    assert bool(r) is False
    assert list(r) == [False, r.retry_after]
    assert r[0] is False
    assert r[1] == r.retry_after
    with pytest.raises(IndexError):
        _ = r[2]
    assert r.retry_after_seconds == r.retry_after


def test_aliases_de_constructor():
    clock = {"t": 0.0}
    for kwargs in (
        {"limit": 2, "window": 5.0},
        {"max": 2, "window_s": 5.0},
        {"capacity": 2, "window_size": 5.0},
        {"max_count": 2, "ttl": 5.0},
    ):
        lim = RateLimiter(clock=lambda: clock["t"], **kwargs)
        assert lim.max_requests == 2
        assert lim.window_seconds == 5.0
        assert lim.check("k").allowed is True


def test_aliases_de_metodos():
    clock = {"t": 0.0}
    lim = RateLimiter(max_requests=1, window_seconds=10.0, clock=lambda: clock["t"])
    assert lim.allow("k") is True
    assert lim.acquire("k") is False
    assert lim.is_allowed("k") is False
    assert lim.permit("k") is False
    r = lim.hit("k")
    assert isinstance(r, RateLimitResult)


def test_window_cero_o_negativa_no_rompe():
    clock = {"t": 0.0}
    lim = RateLimiter(max_requests=1, window_seconds=0.0, clock=lambda: clock["t"])
    assert lim.check("k").allowed is True
    # con ventana 0, el anterior se purga inmediatamente
    assert lim.check("k").allowed is True
