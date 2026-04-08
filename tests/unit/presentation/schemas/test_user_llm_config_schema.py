import pytest
from datetime import datetime
from pydantic import ValidationError
from src.presentation.schemas.user_llm_config import (
    UserLlmConfigBase,
    UserLlmConfigCreate,
    UserLlmConfigResponse,
)


def test_user_llm_config_create_valid():
    data = UserLlmConfigCreate(
        agent="resume_agent",
        provider="openai",
        model="gpt-4o-mini",
        api_key="sk-test-123",
        base_url=None,
        temperature=0.7,
    )
    assert data.agent == "resume_agent"
    assert data.api_key == "sk-test-123"


def test_user_llm_config_create_requires_agent():
    with pytest.raises(ValidationError):
        UserLlmConfigCreate(provider="openai", model="gpt-4o-mini", api_key="sk-test")


def test_user_llm_config_response_excludes_api_key():
    response = UserLlmConfigResponse(
        agent="resume_agent",
        provider="openai",
        model="gpt-4o-mini",
        base_url=None,
        temperature=0.7,
        is_active=True,
        updated_at=datetime.now(),
    )
    assert not hasattr(response, "api_key")
    assert not hasattr(response, "api_key_encrypted")


def test_temperature_range():
    data = UserLlmConfigCreate(
        agent="resume_agent",
        provider="openai",
        model="gpt-4o-mini",
        api_key="sk-test",
        temperature=1.5,
    )
    assert data.temperature == 1.5
