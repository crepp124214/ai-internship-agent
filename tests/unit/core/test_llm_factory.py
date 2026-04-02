import pytest
from types import SimpleNamespace
from unittest.mock import patch

from src.core.llm import LLMFactory, MockLLMAdapter, OpenAIAdapter


def test_factory_prefers_explicit_provider_over_config():
    llm = LLMFactory.create(
        provider="mock",
        config={
            "provider": "openai",
            "api_key": "test-key",
            "model": "gpt-4",
            "llm": {"provider": "openai"},
        },
    )

    assert isinstance(llm, MockLLMAdapter)
    assert llm.config["provider"] == "mock"


def test_factory_prefers_top_level_provider_over_nested_llm_provider():
    llm = LLMFactory.create(
        config={
            "provider": "openai",
            "api_key": "test-key",
            "model": "gpt-4",
            "llm": {"provider": "mock", "model": "nested-model"},
        }
    )

    assert isinstance(llm, OpenAIAdapter)
    assert llm.config["provider"] == "openai"


def test_factory_uses_nested_provider_when_top_level_missing():
    llm = LLMFactory.create(
        config={
            "llm": {
                "provider": "openai",
                "api_key": "test-key",
                "model": "gpt-4o-mini",
            }
        }
    )

    assert isinstance(llm, OpenAIAdapter)
    assert llm.config["provider"] == "openai"
    assert llm.model == "gpt-4o-mini"


def test_factory_uses_nested_provider_when_top_level_provider_is_blank():
    llm = LLMFactory.create(
        config={
            "provider": "   ",
            "llm": {
                "provider": "openai",
                "api_key": "test-key",
                "model": "gpt-4o-mini",
            },
        }
    )

    assert isinstance(llm, OpenAIAdapter)
    assert llm.config["provider"] == "openai"


def test_factory_prefers_environment_default_provider_when_provider_missing(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "mock")

    with patch("src.core.llm.factory.get_settings", return_value=SimpleNamespace(LLM_PROVIDER="openai")):
        llm = LLMFactory.create(config={"seed": 7})

    assert isinstance(llm, MockLLMAdapter)
    assert llm.config["provider"] == "mock"


def test_factory_uses_settings_default_provider_when_environment_missing(monkeypatch):
    monkeypatch.delenv("LLM_PROVIDER", raising=False)

    with patch("src.core.llm.factory.get_settings", return_value=SimpleNamespace(LLM_PROVIDER="openai")):
        llm = LLMFactory.create(config={"seed": 7, "api_key": "test-key", "model": "gpt-4o-mini"})

    assert isinstance(llm, OpenAIAdapter)
    assert llm.config["provider"] == "openai"


def test_factory_uses_settings_default_provider_when_config_provider_is_blank(monkeypatch):
    monkeypatch.delenv("LLM_PROVIDER", raising=False)

    with patch("src.core.llm.factory.get_settings", return_value=SimpleNamespace(LLM_PROVIDER="openai")):
        llm = LLMFactory.create(config={"provider": " ", "seed": 7, "api_key": "test-key", "model": "gpt-4o-mini"})

    assert isinstance(llm, OpenAIAdapter)
    assert llm.config["provider"] == "openai"


def test_factory_returns_mock_provider():
    llm = LLMFactory.create("mock", {"model": "resume-test"})

    assert isinstance(llm, MockLLMAdapter)
    assert llm.config["model"] == "resume-test"


def test_factory_returns_openai_provider():
    llm = LLMFactory.create("openai", {"api_key": "test-key", "model": "gpt-4"})

    assert isinstance(llm, OpenAIAdapter)


def test_factory_rejects_unknown_provider():
    with pytest.raises(ValueError, match="Unsupported LLM provider"):
        LLMFactory.create("unknown", {})


@pytest.mark.asyncio
async def test_mock_provider_is_deterministic():
    llm = LLMFactory.create("mock", {"model": "resume-test"})

    generated = await llm.generate("Summarize this resume")
    chat = await llm.chat([{"role": "user", "content": "Hello"}])
    embedding = await llm.get_embedding("Hello")

    assert "Summarize this resume" in generated
    assert chat["role"] == "assistant"
    assert "Hello" in chat["content"]
    assert len(embedding) == 3
    assert all(isinstance(value, float) for value in embedding)
