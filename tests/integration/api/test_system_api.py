"""System-level API smoke tests."""

from unittest.mock import AsyncMock, patch

from fastapi.testclient import TestClient

from src.main import app


client = TestClient(app)


def test_root_endpoint_exposes_navigation_links():
    response = client.get("/")

    assert response.status_code == 200

    payload = response.json()
    assert payload["version"] == "0.1.0"
    assert payload["docs"] == "/docs"
    assert payload["health"] == "/health"
    assert payload["ready"] == "/ready"
    assert isinstance(payload["message"], str)
    assert payload["message"]


def test_health_endpoint_reports_liveness():
    response = client.get("/health")

    assert response.status_code == 200
    assert response.json() == {"status": "healthy"}


def test_ready_endpoint_reports_readiness_when_database_is_available():
    from src.business_logic.readiness import ReadinessStatus, ReadinessState

    mock_status = ReadinessStatus(state=ReadinessState.READY)

    with patch("src.main.check_readiness", new_callable=AsyncMock, return_value=mock_status) as mock_check:
        response = client.get("/ready")

    assert response.status_code == 200
    assert response.json() == {"status": "ready"}
    mock_check.assert_called_once_with()


def test_ready_endpoint_returns_503_when_database_check_fails():
    from src.business_logic.readiness import ReadinessStatus, ReadinessState

    mock_status = ReadinessStatus(
        state=ReadinessState.NOT_READY,
        reason="database: connection failed",
    )

    with patch("src.main.check_readiness", new_callable=AsyncMock, return_value=mock_status) as mock_check:
        response = client.get("/ready")

    assert response.status_code == 503
    # 统一错误格式: code, message, retryable, request_id
    body = response.json()
    assert body["code"] == "SERVICE_NOT_READY"
    assert body["retryable"] is True
    mock_check.assert_called_once_with()
