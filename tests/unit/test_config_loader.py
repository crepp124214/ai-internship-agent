from __future__ import annotations

from src.utils.config_loader import (
    Settings,
    _validate_runtime_security,
    _load_rate_limit_settings,
)


def test_validate_runtime_security_allows_placeholder_secret_in_development():
    settings = Settings(APP_ENV="development", SECRET_KEY="change-me-before-production")
    _validate_runtime_security(settings)


def test_validate_runtime_security_rejects_placeholder_secret_in_production():
    settings = Settings(APP_ENV="production", SECRET_KEY="change-me-before-production")

    try:
        _validate_runtime_security(settings)
        assert False, "Expected ValueError for insecure production SECRET_KEY"
    except ValueError as exc:
        assert "Insecure SECRET_KEY" in str(exc)


def test_validate_runtime_security_accepts_strong_secret_in_production():
    settings = Settings(APP_ENV="production", SECRET_KEY="prod-super-strong-secret-key-123")
    _validate_runtime_security(settings)


def test_validate_runtime_security_rejects_samesite_none_without_secure():
    settings = Settings(
        APP_ENV="production",
        SECRET_KEY="prod-super-strong-secret-key-123",
        AUTH_REFRESH_COOKIE_SAMESITE="none",
        AUTH_REFRESH_COOKIE_SECURE=False,
    )
    try:
        _validate_runtime_security(settings)
        assert False, "Expected ValueError for SameSite=None without Secure"
    except ValueError as exc:
        assert "AUTH_REFRESH_COOKIE_SECURE must be true" in str(exc)


def test_validate_runtime_security_accepts_samesite_none_with_secure():
    settings = Settings(
        APP_ENV="production",
        SECRET_KEY="prod-super-strong-secret-key-123",
        AUTH_REFRESH_COOKIE_SAMESITE="none",
        AUTH_REFRESH_COOKIE_SECURE=True,
    )
    _validate_runtime_security(settings)  # Should not raise


def test_load_rate_limit_settings_invalid_backend_defaults_to_auto(monkeypatch):
    # Patch os.getenv BEFORE the module is reloaded so the function re-reads env
    with monkeypatch.context() as m:
        m.setenv("RATE_LIMIT_REQUESTS", "100")
        m.setenv("RATE_LIMIT_WINDOW_SECONDS", "60")
        m.setenv("RATE_LIMIT_BACKEND", "invalid-backend")

        import importlib
        import src.utils.config_loader as cl
        importlib.reload(cl)

        rate_requests, window_seconds, backend = cl._load_rate_limit_settings()
        assert rate_requests == 100
        assert window_seconds == 60
        assert backend == "auto"
