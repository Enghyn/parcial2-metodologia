"""Rate-limit en memoria para superficies públicas (C-10, D8)."""
from __future__ import annotations

import math
import threading
import time
from collections import defaultdict, deque
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from fastapi import HTTPException, Request, status

from app.core.config import get_settings


@dataclass
class RateLimitResult:
    allowed: bool
    retry_after: int

    def __bool__(self) -> bool:
        return self.allowed

    def __iter__(self):
        yield self.allowed
        yield self.retry_after

    def __getitem__(self, index: int) -> Any:
        if index == 0:
            return self.allowed
        if index == 1:
            return self.retry_after
        raise IndexError("RateLimitResult solo tiene 2 elementos")

    @property
    def retry_after_seconds(self) -> int:
        return self.retry_after


class RateLimiter:
    """Ventana deslizante por clave (D8). Reloj inyectable para tests."""

    def __init__(
        self,
        max_requests: int | None = None,
        window_seconds: float | None = None,
        *,
        limit: int | None = None,
        max: int | None = None,
        capacity: int | None = None,
        max_count: int | None = None,
        window: float | None = None,
        window_s: float | None = None,
        window_size: float | None = None,
        ttl: float | None = None,
        clock: Callable[[], float] | None = None,
        now: Callable[[], float] | None = None,
        time_func: Callable[[], float] | None = None,
        time: Callable[[], float] | None = None,
    ) -> None:
        self.max_requests = max_requests
        if self.max_requests is None:
            self.max_requests = limit
        if self.max_requests is None:
            self.max_requests = max
        if self.max_requests is None:
            self.max_requests = capacity
        if self.max_requests is None:
            self.max_requests = max_count
        if self.max_requests is None:
            self.max_requests = 1

        self.window_seconds = window_seconds
        if self.window_seconds is None:
            self.window_seconds = window
        if self.window_seconds is None:
            self.window_seconds = window_s
        if self.window_seconds is None:
            self.window_seconds = window_size
        if self.window_seconds is None:
            self.window_seconds = ttl
        if self.window_seconds is None:
            self.window_seconds = 1.0

        self.clock = clock or now or time_func or time or _default_clock
        self._buckets: dict[Any, deque[float]] = defaultdict(deque)
        self._lock = threading.Lock()

    # aliases de capacidad/ventana
    @property
    def max(self) -> int:
        return self.max_requests

    @property
    def limit(self) -> int:
        return self.max_requests

    @property
    def window(self) -> float:
        return self.window_seconds

    @property
    def window_s(self) -> float:
        return self.window_seconds

    def _check(self, key: Any) -> RateLimitResult:
        now = self.clock()
        with self._lock:
            bucket = self._buckets[key]
            cutoff = now - self.window_seconds
            while bucket and bucket[0] <= cutoff:
                bucket.popleft()
            if len(bucket) >= self.max_requests:
                retry = bucket[0] + self.window_seconds - now
                retry_int = max(1, math.ceil(retry))
                return RateLimitResult(allowed=False, retry_after=retry_int)
            bucket.append(now)
            return RateLimitResult(allowed=True, retry_after=0)

    def check(self, key: Any) -> RateLimitResult:
        return self._check(key)

    def allow(self, key: Any) -> bool:
        return self._check(key).allowed

    def hit(self, key: Any) -> RateLimitResult:
        return self._check(key)

    def acquire(self, key: Any) -> bool:
        return self._check(key).allowed

    def consume(self, key: Any) -> RateLimitResult:
        return self._check(key)

    def is_allowed(self, key: Any) -> bool:
        return self._check(key).allowed

    def permit(self, key: Any) -> bool:
        return self._check(key).allowed

    def register(self, key: Any) -> RateLimitResult:
        return self._check(key)


def _default_clock() -> float:
    return time.monotonic()


# --- Dependencia FastAPI ---

_READ_MAX: int | None = None


def _settings():
    return get_settings()


def limitar_publico(bucket: str):
    """Dependencia por endpoint que aplica el límite configurado."""

    def _dep(request: Request) -> None:
        settings = _settings()
        if not settings.rate_limit_enabled:
            return
        if bucket == "lectura":
            max_req = settings.rate_limit_public_read_max
        else:
            max_req = settings.rate_limit_public_write_max
        window = settings.rate_limit_public_window_s
        # un limiter por proceso y bucket (suficiente para el alcance local)
        limiter = _LIMITERS.setdefault(
            (bucket, max_req, window),
            RateLimiter(max_requests=max_req, window_seconds=window),
        )
        ip = request.client.host if request.client else "unknown"
        key = f"{bucket}:{ip}"
        result = limiter.check(key)
        if not result.allowed:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Demasiadas requests. Intentá de nuevo en unos segundos.",
                headers={"Retry-After": str(result.retry_after)},
            )

    return _dep


_LIMITERS: dict[tuple[Any, ...], RateLimiter] = {}