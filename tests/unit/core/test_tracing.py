"""Tests for OpenTelemetry tracing infrastructure."""

from __future__ import annotations

import pytest


class TestTracingSetup:
    """Test tracing initialization and configuration."""

    def test_setup_tracing_returns_provider(self):
        """setup_tracing should return a TracerProvider."""
        from src.core.tracing import setup_tracing

        # Should not raise
        tp = setup_tracing()
        assert tp is not None
        # Should have get_tracer method
        assert hasattr(tp, "get_tracer")

    def test_get_tracer_returns_tracer_after_setup(self):
        """get_tracer(name) should return a tracer after setup_tracing is called."""
        from src.core.tracing import setup_tracing, get_tracer

        setup_tracing()
        # Should not raise - get_tracer takes a name argument
        tracer = get_tracer("test-tracer")
        assert tracer is not None

    def test_get_tracer_before_init_raises(self):
        """get_tracer should raise RuntimeError if called before setup_tracing."""
        import src.core.tracing as tracing_module

        old = tracing_module._tracer_provider
        tracing_module._tracer_provider = None
        try:
            with pytest.raises(RuntimeError, match="not been initialized"):
                from src.core.tracing import get_tracer
                get_tracer("test")
        finally:
            tracing_module._tracer_provider = old

    def test_setup_tracing_is_idempotent(self):
        """Calling setup_tracing twice should not raise."""
        from src.core.tracing import setup_tracing

        # Should not raise
        tp1 = setup_tracing()
        tp2 = setup_tracing()
        assert tp1 is not None
        assert tp2 is not None


class TestTracingConfig:
    """Test tracing config module."""

    def test_init_tracing_returns_provider(self):
        """init_tracing should return a provider object."""
        from src.core.tracing.config import init_tracing

        provider = init_tracing()
        assert provider is not None
        # Should have get_tracer method
        assert hasattr(provider, "get_tracer")

    def test_init_tracing_service_name_default(self):
        """Default service name should be ai-internship-agent."""
        from src.core.tracing.config import init_tracing

        provider = init_tracing()
        attrs = dict(provider.resource.attributes)
        assert attrs.get("service.name") == "ai-internship-agent"

    def test_init_tracing_fallback_when_otel_unavailable(self):
        """init_tracing should return a dummy provider when OTEL packages are unavailable."""
        import sys

        # Simulate unavailable OTEL by temporarily removing the packages
        saved_modules = {k: sys.modules.pop(k) for k in list(sys.modules.keys()) if "opentelemetry" in k}
        try:
            from src.core.tracing.config import init_tracing

            provider = init_tracing()
            # Should not raise; should return a dummy provider
            assert provider is not None
            tracer = provider.get_tracer("test")
            assert tracer is not None
        finally:
            sys.modules.update(saved_modules)
