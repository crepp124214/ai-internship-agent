from __future__ import annotations

from src.utils.config_loader import (
    Settings,
    _validate_runtime_security,
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
