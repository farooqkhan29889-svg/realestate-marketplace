import time
import threading
from collections import defaultdict, deque

from fastapi import HTTPException, Request, status


class _RateLimiter:
    """Minimal in-memory sliding-window limiter.

    Fine for a single-process deployment. For multiple workers/instances, swap
    this for a Redis-backed limiter so limits are shared across processes.
    """

    def __init__(self) -> None:
        self._hits: dict[str, deque] = defaultdict(deque)
        self._lock = threading.Lock()

    def hit(self, key: str, max_calls: int, period_seconds: int) -> None:
        now = time.monotonic()
        with self._lock:
            window = self._hits[key]
            while window and now - window[0] > period_seconds:
                window.popleft()
            if len(window) >= max_calls:
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail="Too many attempts. Please wait a moment and try again.",
                )
            window.append(now)


_limiter = _RateLimiter()


def rate_limit(request: Request, action: str, max_calls: int, period_seconds: int) -> None:
    if request is None:
        return
    ip = request.client.host if request.client else "unknown"
    _limiter.hit(f"{action}:{ip}", max_calls, period_seconds)
