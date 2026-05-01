from __future__ import annotations

from collections import defaultdict, deque
from dataclasses import dataclass
from datetime import datetime, timezone
from threading import Lock

from fastapi import HTTPException, Request, status


@dataclass(slots=True)
class RateLimitResult:
    allowed: bool
    retry_after_seconds: int = 0


class RateLimiter:
    def __init__(self, *, max_requests: int, window_seconds: int) -> None:
        self.max_requests = max_requests
        self.window_seconds = window_seconds
        self._requests: dict[str, deque[float]] = defaultdict(deque)
        self._lock = Lock()

    def check(self, identifier: str) -> RateLimitResult:
        now = datetime.now(timezone.utc).timestamp()
        with self._lock:
            queue = self._requests[identifier]
            while queue and (now - queue[0]) > self.window_seconds:
                queue.popleft()

            if len(queue) >= self.max_requests:
                retry_after = max(1, int(self.window_seconds - (now - queue[0])))
                return RateLimitResult(allowed=False, retry_after_seconds=retry_after)

            queue.append(now)
            return RateLimitResult(allowed=True)

    async def depends(self, request: Request) -> None:
        identifier = request.client.host if request.client else "unknown"
        result = self.check(identifier)
        if not result.allowed:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Rate limit exceeded. Please try again later.",
                headers={"Retry-After": str(result.retry_after_seconds)},
            )

