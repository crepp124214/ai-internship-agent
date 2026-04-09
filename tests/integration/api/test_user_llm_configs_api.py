"""User LLM Configs API integration tests."""

from dataclasses import dataclass
from datetime import datetime
from types import SimpleNamespace
from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from src.data_access.database import Base, get_db
from src.main import app
from src.presentation.api.deps import get_current_user


@dataclass
class MockUserLlmConfig:
    """Mock UserLlmConfig object for testing."""
    id: int
    user_id: int
    agent: str
    provider: str
    model: str
    base_url: str
    temperature: float
    is_active: bool
    updated_at: datetime


engine = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="module", autouse=True)
def setup_database():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def db_session():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture
def client(db_session):
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


def _set_current_user(user_id):
    app.dependency_overrides[get_current_user] = lambda: SimpleNamespace(id=user_id)


def test_get_llm_configs_requires_authentication(client):
    response = client.get("/api/v1/users/llm-configs/")
    assert response.status_code == 401


def test_get_llm_configs_returns_empty_list_for_new_user(client):
    _set_current_user(999)

    with patch(
        "src.presentation.api.v1.user_llm_configs.user_llm_config_service.get_user_configs",
        return_value=[],
    ):
        response = client.get("/api/v1/users/llm-configs/")

    assert response.status_code == 200
    assert response.json() == []


def test_get_llm_configs_returns_user_configs(client):
    _set_current_user(1)
    mock_config = MockUserLlmConfig(
        id=1,
        user_id=1,
        agent="resume_agent",
        provider="openai",
        model="gpt-4",
        base_url=None,
        temperature=0.7,
        is_active=True,
        updated_at=datetime.now(),
    )

    with patch(
        "src.presentation.api.v1.user_llm_configs.user_llm_config_service.get_user_configs",
        return_value=[mock_config],
    ):
        response = client.get("/api/v1/users/llm-configs/")

    assert response.status_code == 200
    payload = response.json()
    assert len(payload) == 1
    assert payload[0]["agent"] == "resume_agent"
    assert payload[0]["provider"] == "openai"


def test_save_llm_config_requires_authentication(client):
    response = client.post(
        "/api/v1/users/llm-configs/",
        json={
            "agent": "resume_agent",
            "provider": "openai",
            "model": "gpt-4",
            "api_key": "sk-test-key",
            "temperature": 0.7,
        },
    )
    assert response.status_code == 401


def test_save_llm_config_creates_new_config(client):
    _set_current_user(1)
    mock_config = MockUserLlmConfig(
        id=1,
        user_id=1,
        agent="resume_agent",
        provider="openai",
        model="gpt-4",
        base_url=None,
        temperature=0.7,
        is_active=True,
        updated_at=datetime.now(),
    )

    with patch(
        "src.presentation.api.v1.user_llm_configs.user_llm_config_service.save_config",
        return_value=mock_config,
    ):
        response = client.post(
            "/api/v1/users/llm-configs/",
            json={
                "agent": "resume_agent",
                "provider": "openai",
                "model": "gpt-4",
                "api_key": "sk-test-key",
                "temperature": 0.7,
            },
        )

    assert response.status_code == 200
    payload = response.json()
    assert payload["agent"] == "resume_agent"
    assert payload["provider"] == "openai"
    assert payload["model"] == "gpt-4"


def test_save_llm_config_returns_500_on_service_error(client):
    _set_current_user(1)

    with patch(
        "src.presentation.api.v1.user_llm_configs.user_llm_config_service.save_config",
        side_effect=RuntimeError("database error"),
    ):
        response = client.post(
            "/api/v1/users/llm-configs/",
            json={
                "agent": "resume_agent",
                "provider": "openai",
                "model": "gpt-4",
                "api_key": "sk-test-key",
            },
        )

    assert response.status_code == 500
    # 统一错误格式: code, message, retryable
    # 未知异常隐藏内部细节
    body = response.json()
    assert body["code"] == "INTERNAL_ERROR"
    assert body["retryable"] is True


def test_delete_llm_config_requires_authentication(client):
    response = client.delete("/api/v1/users/llm-configs/resume_agent")
    assert response.status_code == 401


def test_delete_llm_config_returns_404_when_not_found(client):
    _set_current_user(999)

    with patch(
        "src.presentation.api.v1.user_llm_configs.user_llm_config_service.delete_config",
        return_value=False,
    ):
        response = client.delete("/api/v1/users/llm-configs/resume_agent")

    assert response.status_code == 404
    # 统一错误格式: code, message, retryable
    body = response.json()
    assert body["code"] == "RESOURCE_NOT_FOUND"
    assert "Config not found" in body["message"]


def test_delete_llm_config_returns_204_on_success(client):
    _set_current_user(1)

    with patch(
        "src.presentation.api.v1.user_llm_configs.user_llm_config_service.delete_config",
        return_value=True,
    ):
        response = client.delete("/api/v1/users/llm-configs/resume_agent")

    assert response.status_code == 204
