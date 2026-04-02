"""Tests for rate limiting middleware."""

from __future__ import annotations

import pytest
from unittest.mock import AsyncMock, patch

from src.presentation.api.middleware.rate_limit import (
    MemoryRateLimitBackend,
    RedisRateLimitBackend,
    RateLimitMiddleware,
    _get_backend,
)


class TestMemoryRateLimitBackend:
    """Test the in-memory sliding window backend."""

    @pytest.mark.asyncio
    async def test_allows_within_limit(self):
        """Requests within limit should be allowed."""
        backend = MemoryRateLimitBackend()
        for i in range(5):
            result = await backend.is_allowed("test-key", limit=10, window_seconds=60)
            assert result is True

    @pytest.mark.asyncio
    async def test_blocks_when_limit_exceeded(self):
        """Requests exceeding limit should be blocked."""
        backend = MemoryRateLimitBackend()
        # Fill up to limit
        for _ in range(5):
            await backend.is_allowed("test-key", limit=5, window_seconds=60)
        # Next request should be blocked
        result = await backend.is_allowed("test-key", limit=5, window_seconds=60)
        assert result is False

    @pytest.mark.asyncio
    async def test_different_keys_independent(self):
        """Different rate limit keys should be independent."""
        backend = MemoryRateLimitBackend()
        # Fill one key
        for _ in range(5):
            await backend.is_allowed("key-a", limit=5, window_seconds=60)
        # Other key should still be allowed
        result = await backend.is_allowed("key-b", limit=5, window_seconds=60)
        assert result is True

    @pytest.mark.asyncio
    async def test_window_expiry(self):
        """Old entries should expire after window_seconds."""
        backend = MemoryRateLimitBackend()
        # Manually add old entries
        old_time = backend._store["old-key"]
        old_time.clear()

        # Add entries with old timestamps
        import time
        now = time.time()
        backend._store["old-key"] = [(now - 120, 1.0), (now - 119, 2.0)]

        # Should allow since old entries are outside window
        result = await backend.is_allowed("old-key", limit=2, window_seconds=60)
        assert result is True


class TestRedisRateLimitBackend:
    """Test the Redis sliding window backend."""

    @pytest.mark.asyncio
    async def test_is_allowed_returns_true_when_redis_unavailable(self):
        """Redis failures should fail-open (allow request)."""
        backend = RedisRateLimitBackend(redis_url="redis://localhost:9999")

        # Patch _get_client to raise an exception
        with patch.object(backend, "_get_client", side_effect=Exception("Redis unavailable")):
            result = await backend.is_allowed("test-key", limit=5, window_seconds=60)
            assert result is True  # Fail open


class TestRateLimitMiddleware:
    """Test the RateLimitMiddleware integration."""

    @pytest.mark.asyncio
    async def test_health_endpoint_excluded(self):
        """Health endpoints should not be rate limited."""
        middleware = RateLimitMiddleware(app=AsyncMock())
        request = AsyncMock()
        request.url.path = "/health"
        request.client = AsyncMock(host="127.0.0.1")

        call_next = AsyncMock()
        await middleware.dispatch(request, call_next)
        call_next.assert_called_once()

    @pytest.mark.asyncio
    async def test_ready_endpoint_excluded(self):
        """Ready endpoint should not be rate limited."""
        middleware = RateLimitMiddleware(app=AsyncMock())
        request = AsyncMock()
        request.url.path = "/ready"
        request.client = AsyncMock(host="127.0.0.1")

        call_next = AsyncMock()
        await middleware.dispatch(request, call_next)
        call_next.assert_called_once()

    @pytest.mark.asyncio
    async def test_metrics_endpoint_excluded(self):
        """Metrics endpoint should not be rate limited."""
        middleware = RateLimitMiddleware(app=AsyncMock())
        request = AsyncMock()
        request.url.path = "/metrics"
        request.client = AsyncMock(host="127.0.0.1")

        call_next = AsyncMock()
        await middleware.dispatch(request, call_next)
        call_next.assert_called_once()


class TestGetBackend:
    """Test backend selection."""

    def test_get_backend_returns_memory_by_default(self):
        """By default (localhost Redis), should return memory backend."""
        # Reset global
        import src.presentation.api.middleware.rate_limit as rl_module
        old_redis = rl_module._redis_backend
        rl_module._redis_backend = None

        # Patch get_settings to return a localhost URL
        with patch("src.presentation.api.middleware.rate_limit.get_settings") as mock_settings:
            mock_settings.return_value.REDIS_URL = "redis://localhost:6379/0"
            backend = _get_backend()
            assert isinstance(backend, MemoryRateLimitBackend)

        rl_module._redis_backend = old_redis
