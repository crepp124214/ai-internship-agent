"""Tests for rate limiting middleware."""

from __future__ import annotations

from unittest.mock import AsyncMock, patch

import pytest

from src.presentation.api.middleware.rate_limit import (
    MemoryRateLimitBackend,
    RateLimitMiddleware,
    RedisRateLimitBackend,
    _get_backend,
    get_rate_limit_runtime_config,
)


class TestMemoryRateLimitBackend:
    """Test the in-memory sliding window backend."""

    @pytest.mark.asyncio
    async def test_allows_within_limit(self):
        """Requests within limit should be allowed."""
        backend = MemoryRateLimitBackend()
        for _ in range(5):
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

    def setup_method(self):
        import src.presentation.api.middleware.rate_limit as rl_module

        self.rl_module = rl_module
        self.old_redis = rl_module._redis_backend

    def teardown_method(self):
        self.rl_module._redis_backend = self.old_redis

    def test_get_backend_returns_memory_when_mode_memory(self):
        self.rl_module._redis_backend = None

        with patch("src.presentation.api.middleware.rate_limit.RATE_LIMIT_BACKEND", "memory"):
            backend = _get_backend()
            assert isinstance(backend, MemoryRateLimitBackend)

    def test_get_backend_returns_redis_when_mode_redis(self):
        self.rl_module._redis_backend = None

        with patch("src.presentation.api.middleware.rate_limit.RATE_LIMIT_BACKEND", "redis"):
            with patch("src.presentation.api.middleware.rate_limit.get_settings") as mock_settings:
                mock_settings.return_value.REDIS_URL = "redis://redis:6379/0"
                backend = _get_backend()
                assert isinstance(backend, RedisRateLimitBackend)

    def test_get_backend_returns_memory_in_auto_mode_with_default_local_redis(self):
        self.rl_module._redis_backend = None

        with patch("src.presentation.api.middleware.rate_limit.RATE_LIMIT_BACKEND", "auto"):
            with patch("src.presentation.api.middleware.rate_limit.get_settings") as mock_settings:
                mock_settings.return_value.REDIS_URL = "redis://localhost:6379/0"
                backend = _get_backend()
                assert isinstance(backend, MemoryRateLimitBackend)

    def test_get_backend_returns_redis_in_auto_mode_with_non_default_redis(self):
        self.rl_module._redis_backend = None

        with patch("src.presentation.api.middleware.rate_limit.RATE_LIMIT_BACKEND", "auto"):
            with patch("src.presentation.api.middleware.rate_limit.get_settings") as mock_settings:
                mock_settings.return_value.REDIS_URL = "redis://redis:6379/0"
                backend = _get_backend()
                assert isinstance(backend, RedisRateLimitBackend)


class TestRateLimitRuntimeConfig:
    def test_runtime_config_reports_selected_backend(self):
        with patch("src.presentation.api.middleware.rate_limit.RATE_LIMIT_BACKEND", "auto"):
            with patch("src.presentation.api.middleware.rate_limit.get_settings") as mock_settings:
                mock_settings.return_value.REDIS_URL = "redis://localhost:6379/0"
                config = get_rate_limit_runtime_config()
                assert config["selected_backend"] == "memory"
