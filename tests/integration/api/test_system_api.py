"""System-level API smoke tests."""

from unittest.mock import patch

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
    with patch("src.main.check_database_connection") as mock_check:
        response = client.get("/ready")

    assert response.status_code == 200
    assert response.json() == {"status": "ready"}
    mock_check.assert_called_once_with()


def test_ready_endpoint_returns_503_when_database_check_fails():
    with patch(
        "src.main.check_database_connection",
        side_effect=Exception("database check failed: boom"),
    ) as mock_check:
        response = client.get("/ready")

    assert response.status_code == 503
    assert response.json()["detail"] == "service not ready: database check failed: boom"
    mock_check.assert_called_once_with()
