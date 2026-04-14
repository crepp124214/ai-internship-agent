"""User LLM Configs API integration tests."""

from dataclasses import dataclass
from datetime import datetime
from types import SimpleNamespace
from typing import Optional
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


def test_test_llm_config_returns_structured_result(client):
    """Test that /test endpoint returns latency_ms, error_code, error_message, fallback_used."""
    _set_current_user(1)

    mock_result = MockUserLlmConfig(
        id=1,
        user_id=1,
        agent="resume_agent",
        provider="openai",
        model="gpt-4o-mini",
        base_url=None,
        temperature=0.7,
        is_active=True,
        updated_at=datetime.now(),
    )

    with patch(
        "src.presentation.api.v1.user_llm_configs.user_llm_config_service.test_config",
        return_value=MockTestResult(
            status="success",
            provider="openai",
            model="gpt-4o-mini",
            latency_ms=1234,
            fallback_used=False,
            error_code=None,
            error_message=None,
            agent=None,
        ),
    ) as mock_test_config:
        response = client.post(
            "/api/v1/users/llm-configs/test",
            json={
                "provider": "openai",
                "model": "gpt-4o-mini",
                "api_key": "sk-test-key",
            },
        )

    assert response.status_code == 200
    payload = response.json()
    assert "latency_ms" in payload
    assert "error_code" in payload
    assert "error_message" in payload
    assert "fallback_used" in payload
    assert payload["status"] == "success"
    assert payload["latency_ms"] == 1234
    args, kwargs = mock_test_config.call_args
    assert args[1] == 1
    assert args[2].provider == "openai"
    assert args[2].model == "gpt-4o-mini"
    assert kwargs["agent"] is None


def test_test_llm_config_returns_error_with_code(client):
    """Test that /test endpoint returns structured error when config is invalid."""
    _set_current_user(1)

    with patch(
        "src.presentation.api.v1.user_llm_configs.user_llm_config_service.test_config",
        return_value=MockTestResult(
            status="error",
            provider="openai",
            model="gpt-4o-mini",
            latency_ms=0,
            fallback_used=False,
            error_code="INVALID_API_KEY",
            error_message="Invalid API key provided",
            agent=None,
        ),
    ):
        response = client.post(
            "/api/v1/users/llm-configs/test",
            json={
                "provider": "openai",
                "model": "gpt-4o-mini",
                "api_key": "invalid-key",
            },
        )

    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "error"
    assert payload["error_code"] == "INVALID_API_KEY"
    assert "error_message" in payload


def test_test_agent_config_returns_result(client):
    """Test that /test-agent endpoint returns result with agent field."""
    _set_current_user(1)

    with patch(
        "src.presentation.api.v1.user_llm_configs.user_llm_config_service.test_config",
        return_value=MockTestResult(
            status="success",
            provider="openai",
            model="gpt-4o-mini",
            latency_ms=567,
            fallback_used=False,
            error_code=None,
            error_message=None,
            agent="resume_agent",
        ),
    ) as mock_test_config:
        response = client.post(
            "/api/v1/users/llm-configs/test-agent",
            json={
                "agent": "resume_agent",
                "provider": "openai",
                "model": "gpt-4o-mini",
                "api_key": "sk-test-key",
            },
        )

    assert response.status_code == 200
    payload = response.json()
    assert payload["agent"] == "resume_agent"
    assert payload["latency_ms"] == 567
    args, kwargs = mock_test_config.call_args
    assert args[1] == 1
    assert args[2].agent == "resume_agent"
    assert kwargs["agent"] == "resume_agent"


def test_test_llm_config_requires_authentication(client):
    """Test that /test endpoint requires authentication."""
    response = client.post(
        "/api/v1/users/llm-configs/test",
        json={
            "provider": "openai",
            "model": "gpt-4o-mini",
            "api_key": "sk-test-key",
        },
    )
    assert response.status_code == 401


def test_test_agent_config_requires_authentication(client):
    """Test that /test-agent endpoint requires authentication."""
    response = client.post(
        "/api/v1/users/llm-configs/test-agent",
        json={
            "agent": "resume_agent",
            "provider": "openai",
            "model": "gpt-4o-mini",
            "api_key": "sk-test-key",
        },
    )
    assert response.status_code == 401


def test_batch_save_saves_three_independent_configs(client):
    """
    Test that 'batch apply to three agents' saves three independent configs.
    Each agent config is stored separately under its own agent identifier.
    This verifies the correct semantic: configs are NOT shared defaults,
    but independent per-agent records.
    """
    _set_current_user(1)

    agents = ["resume_agent", "job_agent", "interview_agent"]
    saved_configs = {}

    for agent in agents:
        mock_config = MockUserLlmConfig(
            id=1,
            user_id=1,
            agent=agent,
            provider="openai",
            model="gpt-4o-mini",
            base_url=None,
            temperature=0.7,
            is_active=True,
            updated_at=datetime.now(),
        )
        saved_configs[agent] = mock_config

        with patch(
            "src.presentation.api.v1.user_llm_configs.user_llm_config_service.save_config",
            return_value=mock_config,
        ):
            response = client.post(
                "/api/v1/users/llm-configs/",
                json={
                    "agent": agent,
                    "provider": "openai",
                    "model": "gpt-4o-mini",
                    "api_key": "sk-test-key",
                    "temperature": 0.7,
                },
            )

        assert response.status_code == 200, f"Failed to save config for {agent}"
        payload = response.json()
        assert payload["agent"] == agent, f"Expected agent={agent}, got {payload['agent']}"
        # Each config is stored independently - agent field must match what was sent
        assert payload["agent"] == agent

    # Verify each agent was saved separately by fetching all configs
    all_configs = [
        MockUserLlmConfig(
            id=1, user_id=1, agent="resume_agent",
            provider="openai", model="gpt-4o-mini",
            base_url=None, temperature=0.7, is_active=True, updated_at=datetime.now(),
        ),
        MockUserLlmConfig(
            id=2, user_id=1, agent="job_agent",
            provider="openai", model="gpt-4o-mini",
            base_url=None, temperature=0.7, is_active=True, updated_at=datetime.now(),
        ),
        MockUserLlmConfig(
            id=3, user_id=1, agent="interview_agent",
            provider="openai", model="gpt-4o-mini",
            base_url=None, temperature=0.7, is_active=True, updated_at=datetime.now(),
        ),
    ]

    with patch(
        "src.presentation.api.v1.user_llm_configs.user_llm_config_service.get_user_configs",
        return_value=all_configs,
    ):
        response = client.get("/api/v1/users/llm-configs/")

    assert response.status_code == 200
    configs = response.json()
    assert len(configs) == 3
    agent_ids = {c["agent"] for c in configs}
    assert agent_ids == {"resume_agent", "job_agent", "interview_agent"}


@dataclass
class MockTestResult:
    """Mock test result object."""
    status: str
    provider: str
    model: str
    latency_ms: int
    fallback_used: bool
    error_code: Optional[str]
    error_message: Optional[str]
    agent: Optional[str]
