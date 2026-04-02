import asyncio
import pytest

from src.core.llm.circuit_breaker import CircuitBreaker, CircuitBreakerState
from src.core.llm.exceptions import CircuitBreakerOpenError


@pytest.mark.asyncio
async def test_circuit_breaker_opens_after_failures():
    cb = CircuitBreaker(failure_threshold=3, recovery_timeout=1, name="test-cb")
    # Initially CLOSED
    assert (await cb.state()) == CircuitBreakerState.CLOSED

    # Trigger 3 failures -> OPEN
    await cb.allow_request()
    await cb.on_failure()
    await cb.allow_request()
    await cb.on_failure()
    await cb.allow_request()
    await cb.on_failure()

    assert (await cb.state()) == CircuitBreakerState.OPEN

    # While OPEN, requests should be blocked
    with pytest.raises(CircuitBreakerOpenError):
        await cb.allow_request()

    # Wait for recovery timeout, should move to HALF_OPEN on next allow
    await asyncio.sleep(1.1)
    await cb.allow_request()  # should not raise, goes to HALF_OPEN
    # A successful trial should reset to CLOSED
    await cb.on_success()
    assert (await cb.state()) == CircuitBreakerState.CLOSED


@pytest.mark.asyncio
async def test_circuit_breaker_half_open_failure_opens():
    cb = CircuitBreaker(failure_threshold=2, recovery_timeout=1, name="test-cb-2")
    # Open the circuit
    await cb.allow_request()
    await cb.on_failure()
    await cb.allow_request()
    await cb.on_failure()
    assert (await cb.state()) == CircuitBreakerState.OPEN
    # Move to HALF_OPEN after timeout
    await asyncio.sleep(1.1)
    await cb.allow_request()  # HALF_OPEN trial allowed
    # This trial fails
    await cb.on_failure()
    # Should be OPEN again
    assert (await cb.state()) == CircuitBreakerState.OPEN
