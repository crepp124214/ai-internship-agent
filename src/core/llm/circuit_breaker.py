"""In-memory, asynchronous Circuit Breaker for LLM endpoints."""

from __future__ import annotations

import asyncio
import time
from enum import Enum
from typing import Optional

from .exceptions import CircuitBreakerOpenError


class CircuitBreakerState(Enum):
    CLOSED = "closed"
    OPEN = "open"
    HALF_OPEN = "half_open"


class CircuitBreaker:
    """Simple in-memory circuit breaker with async safety."""

    def __init__(self, failure_threshold: int = 5, recovery_timeout: int = 60, name: str = "llm"):
        self.name = name
        self.failure_threshold = int(failure_threshold)
        self.recovery_timeout = int(recovery_timeout)
        self._state = CircuitBreakerState.CLOSED
        self._failure_count = 0
        self._opened_at: Optional[float] = None
        self._half_open_tried = False
        self._lock = asyncio.Lock()

    async def allow_request(self) -> None:
        """Raise CircuitBreakerOpenError if requests are not allowed at the moment."""
        async with self._lock:
            now = time.time()
            if self._state == CircuitBreakerState.OPEN:
                if self._opened_at is None:
                    self._opened_at = now
                if now - self._opened_at >= self.recovery_timeout:
                    self._state = CircuitBreakerState.HALF_OPEN
                    self._half_open_tried = False
                else:
                    raise CircuitBreakerOpenError(f"Circuit breaker '{self.name}' is OPEN")

            if self._state == CircuitBreakerState.HALF_OPEN:
                if self._half_open_tried:
                    # Already tried once in HALF_OPEN, open again on failure by caller
                    raise CircuitBreakerOpenError(f"Circuit breaker '{self.name}' is HALF_OPEN and already tried")
                # First trial in HALF_OPEN is allowed; mark as tried
                self._half_open_tried = True
            # If CLOSED, allow requests freely

    async def on_success(self) -> None:
        async with self._lock:
            self._state = CircuitBreakerState.CLOSED
            self._failure_count = 0
            self._opened_at = None
            self._half_open_tried = False

    async def on_failure(self) -> None:
        async with self._lock:
            if self._state == CircuitBreakerState.HALF_OPEN:
                # A failure in HALF_OPEN immediately opens the circuit again
                self._state = CircuitBreakerState.OPEN
                self._opened_at = time.time()
                self._half_open_tried = False
                self._failure_count = 0
                return
            # In CLOSED state, count failures; open if threshold reached
            self._failure_count += 1
            if self._failure_count >= self.failure_threshold:
                self._state = CircuitBreakerState.OPEN
                self._opened_at = time.time()
                self._half_open_tried = False
                self._failure_count = 0

    async def state(self) -> CircuitBreakerState:
        async with self._lock:
            return self._state

    async def is_open(self) -> bool:
        return (await self.state()) == CircuitBreakerState.OPEN
