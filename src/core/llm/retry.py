"""Async retry utilities for LLM adapters."""

from __future__ import annotations

import asyncio
import functools
from typing import Any, Awaitable, Callable

from .exceptions import LLMRetryableError, LLMRequestError


def _extract_call_args(fn: Callable[..., Awaitable[Any]], *args: Any, **kwargs: Any):
    return args, kwargs


def retry_async(
    max_retries: int = 3,
    base: int = 2,
    initial: float = 1.0,
):
    """Async retry decorator with exponential backoff.

    - Retries on LLMRetryableError.
    - Uses exponential backoff: 1s, 2s, 4s (base=2).
    - Honors Retry-After header when available (embedded in exception as attribute where possible).
    - On final failure, raises LLMRequestError wrapping the last error.
    """

    def decorator(func: Callable[..., Awaitable[Any]]):
        @functools.wraps(func)
        async def wrapper(*args: Any, **kwargs: Any):
            last_exc: Exception | None = None
            for attempt in range(max_retries):
                try:
                    return await func(*args, **kwargs)
                except LLMRetryableError as exc:
                    last_exc = exc
                    # Determine delay
                    delay = None
                    # Try to read Retry-After if provided by exception (best-effort)
                    retry_after = getattr(exc, "retry_after", None)
                    if isinstance(retry_after, (int, float)):
                        delay = float(retry_after)
                    # Fallback to exponential backoff
                    if delay is None:
                        delay = initial * (base ** attempt)
                    # Clamp very small or negative delays
                    if delay < 0.001:
                        delay = 0.001
                    await asyncio.sleep(delay)
                    # retry loop
                    continue
            # Exhausted retries
            if last_exc is not None:
                raise LLMRequestError("LLM request failed after retries") from last_exc
            # Should not reach here; fallback
            raise LLMRequestError("LLM request failed after retries (unknown reason)")

        return wrapper

    return decorator
