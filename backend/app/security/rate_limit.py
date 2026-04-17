from __future__ import annotations

import time
from collections import defaultdict

from fastapi import HTTPException, Request

_WINDOW_SEC = 60
_MAX_REQUESTS = 40

_store: dict[str, list[float]] = defaultdict(list)


def check_rate_limit(request: Request) -> None:
    client = request.client.host if request.client else "unknown"
    now = time.monotonic()
    window_start = now - _WINDOW_SEC
    bucket = _store[client]
    bucket[:] = [t for t in bucket if t > window_start]
    if len(bucket) >= _MAX_REQUESTS:
        raise HTTPException(
            status_code=429,
            detail="Muitas requisições. Aguarde um momento.",
        )
    bucket.append(now)
