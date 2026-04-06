"""
Rate limiting middleware with pluggable backends.

- Redis sliding window (production default when Redis is available)
- In-memory sliding window (fallback / testing)
"""
from __future__ import annotations

import time
from abc import ABC, abstractmethod
from collections import defaultdict
from typing import Optional

from fastapi import HTTPException, Request, status
from starlette.middleware.base import BaseHTTPMiddleware

from src.utils.config_loader import (
    RATE_LIMIT_BACKEND,
    RATE_LIMIT_REQUESTS,
    RATE_LIMIT_WINDOW_SECONDS,
    get_settings,
)


# ---------------------------------------------------------------------------
# Backend abstraction
# ---------------------------------------------------------------------------

class RateLimitBackend(ABC):
    """Abstract rate limit backend."""

    @abstractmethod
    async def is_allowed(self, key: str, limit: int, window_seconds: int) -> bool:
        """Return True if the request is allowed, False if rate limited."""
        raise NotImplementedError


class MemoryRateLimitBackend(RateLimitBackend):
    """In-memory sliding window backend (fallback / testing)."""

    def __init__(self) -> None:
        # {key: [(timestamp, unique_id), ...]}
        self._store: dict[str, list[tuple[float, float]]] = defaultdict(list)
        self._counter: dict[str, float] = defaultdict(float)

    async def is_allowed(self, key: str, limit: int, window_seconds: int) -> bool:
        now = time.time()
        window_start = now - window_seconds

        # Remove expired entries
        entries = self._store[key]
        self._store[key] = [(ts, uid) for ts, uid in entries if ts > window_start]

        if len(self._store[key]) >= limit:
            return False

        # Record this request
        self._counter[key] += 1
        self._store[key].append((now, self._counter[key]))
        return True


class RedisRateLimitBackend(RateLimitBackend):
    """Redis sliding window backend using ZADD + ZREMRANGEBYSCORE + ZCARD."""

    def __init__(
        self,
        redis_url: str = "redis://localhost:6379/0",
        key_prefix: str = "ratelimit",
    ) -> None:
        self._redis_url = redis_url
        self._key_prefix = key_prefix
        self._client: Optional["redis.asyncio.Redis"] = None

    async def _get_client(self) -> "redis.asyncio.Redis":
        if self._client is None:
            import redis.asyncio  # type: ignore

            self._client = redis.asyncio.from_url(self._redis_url, decode_responses=True)
        return self._client

    async def is_allowed(self, key: str, limit: int, window_seconds: int) -> bool:
        full_key = f"{self._key_prefix}:{key}"
        now = time.time()
        window_start = now - window_seconds

        try:
            client = await self._get_client()

            # Use pipeline for atomicity
            async with client.pipeline(transaction=True) as pipe:
                # Remove old entries outside the window
                pipe.zremrangebyscore(full_key, 0, window_start)
                # Count entries in current window
                pipe.zcard(full_key)
                results = await pipe.execute()
                count = results[1]

                if count >= limit:
                    return False

                # Add this request with current timestamp as score and unique member
                uid = f"{now}:{count}"
                await client.zadd(full_key, {uid: now})
                # Set expiry on key so it auto-cleanup
                await client.expire(full_key, window_seconds + 1)
                return True

        except Exception:
            # Redis unavailable - fail open (allow request)
            return True


# ---------------------------------------------------------------------------
# Backend selection
# ---------------------------------------------------------------------------

_redis_backend: Optional[RedisRateLimitBackend] = None
_memory_backend: MemoryRateLimitBackend = MemoryRateLimitBackend()


def _backend_mode() -> str:
    return (RATE_LIMIT_BACKEND or "auto").strip().lower()


def _get_backend() -> RateLimitBackend:
    """Return backend according to RATE_LIMIT_BACKEND policy."""
    global _redis_backend

    settings = get_settings()
    redis_url = getattr(settings, "REDIS_URL", "redis://localhost:6379/0")
    mode = _backend_mode()

    if mode == "memory":
        return _memory_backend

    if mode == "redis":
        if _redis_backend is None:
            _redis_backend = RedisRateLimitBackend(redis_url=redis_url)
        return _redis_backend

    # auto mode: keep previous behavior, fallback to memory for localhost default
    if _redis_backend is None:
        if redis_url and redis_url != "redis://localhost:6379/0":
            _redis_backend = RedisRateLimitBackend(redis_url=redis_url)
            return _redis_backend
        return _memory_backend
    return _redis_backend


def get_rate_limit_runtime_config() -> dict[str, str | int]:
    """Expose rate limit runtime configuration for startup logging."""
    settings = get_settings()
    redis_url = getattr(settings, "REDIS_URL", "redis://localhost:6379/0")

    mode = _backend_mode()
    if mode == "memory":
        selected = "memory"
    elif mode == "redis":
        selected = "redis"
    else:
        selected = "redis" if redis_url and redis_url != "redis://localhost:6379/0" else "memory"

    return {
        "mode": mode,
        "selected_backend": selected,
        "requests": RATE_LIMIT_REQUESTS,
        "window_seconds": RATE_LIMIT_WINDOW_SECONDS,
    }


# ---------------------------------------------------------------------------
# Middleware
# ---------------------------------------------------------------------------

class RateLimitMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        # Exclude health/readiness/metrics endpoints from rate limiting
        if request.url.path in ("/health", "/ready", "/metrics"):
            return await call_next(request)

        # Use IP address as the rate limit key
        client_ip = request.client.host if request.client else "unknown"
        key = f"ip:{client_ip}"

        backend = _get_backend()
        allowed = await backend.is_allowed(
            key,
            limit=RATE_LIMIT_REQUESTS,
            window_seconds=RATE_LIMIT_WINDOW_SECONDS,
        )

        if not allowed:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail="Rate limit exceeded. Try again later.",
            )

        return await call_next(request)
