"""OpenAI adapter runtime tests."""

from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
import openai

from src.core.llm import (
    LLMFactory,
    LLMProviderError,
    OpenAIAdapter,
)
from src.core.llm.exceptions import LLMConfigurationError, LLMRequestError


class TestLLMFactoryConfigResolution:
    def test_create_uses_nested_llm_config(self):
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

    @patch.dict("os.environ", {"LLM_PROVIDER": ""}, clear=False)
    def test_create_defaults_to_mock_when_provider_missing(self):
        with patch(
            "src.core.llm.factory.get_settings",
            return_value=SimpleNamespace(LLM_PROVIDER=""),
        ):
            llm = LLMFactory.create(config={"seed": 7})

        assert llm.config["provider"] == "mock"
        assert llm.name == "mock_llm"

    def test_create_rejects_unknown_provider(self):
        with pytest.raises(LLMProviderError):
            LLMFactory.create(provider="unsupported", config={})


class TestOpenAIAdapterRuntime:
    def test_init_requires_api_key(self, monkeypatch):
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)
        monkeypatch.delenv("OPENAI_MODEL", raising=False)
        monkeypatch.delenv("OPENAI_BASE_URL", raising=False)

        with pytest.raises(LLMConfigurationError, match="API key"):
            OpenAIAdapter({"model": "gpt-4o-mini"})

    def test_init_wraps_client_construction_failure(self, monkeypatch):
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)
        monkeypatch.delenv("OPENAI_MODEL", raising=False)
        monkeypatch.delenv("OPENAI_BASE_URL", raising=False)

        with patch("src.core.llm.openai_adapter.AsyncOpenAI", side_effect=RuntimeError("boom")):
            with pytest.raises(LLMConfigurationError, match="initialize OpenAI client"):
                OpenAIAdapter({"api_key": "test-key", "model": "gpt-4o-mini"})

    def test_init_uses_environment_fallback_and_ignores_blank_config(
        self,
        monkeypatch,
    ):
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)
        monkeypatch.delenv("OPENAI_MODEL", raising=False)
        monkeypatch.delenv("OPENAI_BASE_URL", raising=False)
        monkeypatch.setenv("OPENAI_API_KEY", "env-key")
        monkeypatch.setenv("OPENAI_MODEL", "env-model")
        monkeypatch.setenv("OPENAI_BASE_URL", "https://env.example.com/v1")

        client = MagicMock()
        with patch("src.core.llm.openai_adapter.AsyncOpenAI", return_value=client) as mock_openai:
            adapter = OpenAIAdapter(
                {
                    "api_key": "",
                    "model": "",
                    "base_url": "",
                    "llm": {
                        "api_key": "nested-key",
                        "model": "nested-model",
                        "base_url": "https://nested.example.com/v1",
                    },
                }
            )

        assert adapter.api_key == "nested-key"
        assert adapter.model == "nested-model"
        assert adapter.config["base_url"] == ""
        assert mock_openai.call_args.kwargs["api_key"] == "nested-key"
        assert mock_openai.call_args.kwargs["base_url"] == "https://nested.example.com/v1"

    def test_init_uses_environment_values_when_config_is_missing(self, monkeypatch):
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)
        monkeypatch.delenv("OPENAI_MODEL", raising=False)
        monkeypatch.delenv("OPENAI_BASE_URL", raising=False)
        monkeypatch.delenv("OPENAI_TEMPERATURE", raising=False)
        monkeypatch.delenv("OPENAI_MAX_TOKENS", raising=False)
        monkeypatch.delenv("OPENAI_TIMEOUT", raising=False)
        monkeypatch.delenv("OPENAI_MAX_RETRIES", raising=False)
        monkeypatch.setenv("OPENAI_API_KEY", "env-key")
        monkeypatch.setenv("OPENAI_MODEL", "env-model")
        monkeypatch.setenv("OPENAI_BASE_URL", "https://env.example.com/v1")
        monkeypatch.setenv("OPENAI_TEMPERATURE", "0.12")
        monkeypatch.setenv("OPENAI_MAX_TOKENS", "512")
        monkeypatch.setenv("OPENAI_TIMEOUT", "15.5")
        monkeypatch.setenv("OPENAI_MAX_RETRIES", "7")

        client = MagicMock()
        with patch("src.core.llm.openai_adapter.AsyncOpenAI", return_value=client) as mock_openai:
            adapter = OpenAIAdapter({})

        assert adapter.api_key == "env-key"
        assert adapter.model == "env-model"
        assert adapter.temperature == 0.12
        assert adapter.max_tokens == 512
        assert mock_openai.call_args.kwargs["api_key"] == "env-key"
        assert mock_openai.call_args.kwargs["base_url"] == "https://env.example.com/v1"
        assert mock_openai.call_args.kwargs["timeout"] == 15.5
        assert mock_openai.call_args.kwargs["max_retries"] == 7
        assert adapter.config.get("base_url") is None

    def test_init_uses_nested_runtime_config_and_coerces_numeric_values(self, monkeypatch):
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)
        monkeypatch.delenv("OPENAI_MODEL", raising=False)
        monkeypatch.delenv("OPENAI_BASE_URL", raising=False)
        monkeypatch.delenv("OPENAI_TEMPERATURE", raising=False)
        monkeypatch.delenv("OPENAI_MAX_TOKENS", raising=False)
        monkeypatch.delenv("OPENAI_TIMEOUT", raising=False)
        monkeypatch.delenv("OPENAI_MAX_RETRIES", raising=False)

        client = MagicMock()
        with patch("src.core.llm.openai_adapter.AsyncOpenAI", return_value=client) as mock_openai:
            adapter = OpenAIAdapter(
                {
                    "api_key": "test-key",
                    "model": "gpt-4o-mini",
                    "temperature": "not-a-number",
                    "max_tokens": "still-invalid",
                    "timeout": "oops",
                    "max_retries": "nope",
                    "llm": {
                        "temperature": "0.25",
                        "max_tokens": "1024",
                        "timeout": "30",
                        "max_retries": "9",
                    },
                }
            )

        assert adapter.temperature == 0.25
        assert adapter.max_tokens == 1024
        assert mock_openai.call_args.kwargs["timeout"] == 30.0
        assert mock_openai.call_args.kwargs["max_retries"] == 9

    def test_init_falls_back_to_environment_for_invalid_numeric_top_level_config(self, monkeypatch):
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)
        monkeypatch.delenv("OPENAI_MODEL", raising=False)
        monkeypatch.delenv("OPENAI_BASE_URL", raising=False)
        monkeypatch.delenv("OPENAI_TEMPERATURE", raising=False)
        monkeypatch.delenv("OPENAI_MAX_TOKENS", raising=False)
        monkeypatch.delenv("OPENAI_TIMEOUT", raising=False)
        monkeypatch.delenv("OPENAI_MAX_RETRIES", raising=False)
        monkeypatch.setenv("OPENAI_API_KEY", "env-key")
        monkeypatch.setenv("OPENAI_MODEL", "env-model")
        monkeypatch.setenv("OPENAI_TEMPERATURE", "0.42")
        monkeypatch.setenv("OPENAI_MAX_TOKENS", "256")
        monkeypatch.setenv("OPENAI_TIMEOUT", "15.5")
        monkeypatch.setenv("OPENAI_MAX_RETRIES", "7")

        client = MagicMock()
        with patch("src.core.llm.openai_adapter.AsyncOpenAI", return_value=client) as mock_openai:
            adapter = OpenAIAdapter(
                {
                    "api_key": "",
                    "model": "",
                    "temperature": "not-a-number",
                    "max_tokens": "still-invalid",
                    "timeout": "oops",
                    "max_retries": "nope",
                }
            )

        assert adapter.api_key == "env-key"
        assert adapter.model == "env-model"
        assert adapter.temperature == 0.42
        assert adapter.max_tokens == 256
        assert mock_openai.call_args.kwargs["timeout"] == 15.5
        assert mock_openai.call_args.kwargs["max_retries"] == 7

    @pytest.mark.asyncio
    async def test_generate_uses_responses_api(self):
        response = SimpleNamespace(
            output_text="mock summary"
        )
        client = MagicMock()
        client.responses.create = AsyncMock(return_value=response)

        with patch("src.core.llm.openai_adapter.AsyncOpenAI", return_value=client):
            adapter = OpenAIAdapter({"api_key": "test-key", "model": "gpt-4o-mini"})

            result = await adapter.generate(
                "Summarize the resume",
                system_prompt="You are helpful",
                max_tokens=128,
                temperature=0.3,
            )

        assert result == "mock summary"
        client.responses.create.assert_awaited_once()
        kwargs = client.responses.create.await_args.kwargs
        assert kwargs["model"] == "gpt-4o-mini"
        assert kwargs["temperature"] == 0.3
        assert kwargs["max_output_tokens"] == 128
        assert kwargs["input"][0]["role"] == "system"
        assert kwargs["input"][1]["content"] == "Summarize the resume"

    @pytest.mark.asyncio
    async def test_generate_reads_text_from_output_content_items(self):
        response = SimpleNamespace(
            output=[
                SimpleNamespace(
                    content=[SimpleNamespace(text="content item summary")]
                )
            ]
        )
        client = MagicMock()
        client.responses.create = AsyncMock(return_value=response)

        with patch("src.core.llm.openai_adapter.AsyncOpenAI", return_value=client):
            adapter = OpenAIAdapter({"api_key": "test-key", "model": "gpt-4o-mini"})

            result = await adapter.generate("Summarize the resume")

        assert result == "content item summary"

    @pytest.mark.asyncio
    async def test_generate_and_chat_use_configured_runtime_defaults_when_not_overridden(self):
        response = SimpleNamespace(output_text="mock summary")
        chat_response = SimpleNamespace(
            choices=[SimpleNamespace(message=SimpleNamespace(content="mock reply"))]
        )
        client = MagicMock()
        client.responses.create = AsyncMock(return_value=response)
        client.chat.completions.create = AsyncMock(return_value=chat_response)

        with patch("src.core.llm.openai_adapter.AsyncOpenAI", return_value=client):
            adapter = OpenAIAdapter(
                {
                    "api_key": "test-key",
                    "model": "gpt-4o-mini",
                    "temperature": "0.2",
                    "max_tokens": "128",
                }
            )

            generated = await adapter.generate("Summarize the resume")
            chat = await adapter.chat([{"role": "user", "content": "Hello"}])

        assert generated == "mock summary"
        assert chat["content"] == "mock reply"

        generate_kwargs = client.responses.create.await_args.kwargs
        chat_kwargs = client.chat.completions.create.await_args.kwargs
        assert generate_kwargs["temperature"] == 0.2
        assert generate_kwargs["max_output_tokens"] == 128
        assert chat_kwargs["temperature"] == 0.2
        assert chat_kwargs["max_tokens"] == 128

    @pytest.mark.asyncio
    async def test_chat_wraps_client_failure(self):
        client = MagicMock()
        client.chat.completions.create = AsyncMock(side_effect=TimeoutError("timeout"))

        with patch("src.core.llm.openai_adapter.AsyncOpenAI", return_value=client):
            adapter = OpenAIAdapter({"api_key": "test-key", "model": "gpt-4o-mini"})

            with patch("src.core.llm.retry.asyncio.sleep", new=AsyncMock()) as sleep_mock:
                with pytest.raises(LLMRequestError, match="LLM request failed after retries"):
                    await adapter.chat([{"role": "user", "content": "Hello"}])

        assert client.chat.completions.create.await_count == 3
        assert sleep_mock.await_count == 3

    @pytest.mark.asyncio
    async def test_embedding_uses_embeddings_endpoint(self):
        response = SimpleNamespace(
            data=[SimpleNamespace(embedding=[0.1, 0.2, 0.3])]
        )
        client = MagicMock()
        client.embeddings.create = AsyncMock(return_value=response)

        with patch("src.core.llm.openai_adapter.AsyncOpenAI", return_value=client):
            adapter = OpenAIAdapter({"api_key": "test-key", "model": "gpt-4o-mini"})

            embedding = await adapter.get_embedding("Test text")

        assert embedding == [0.1, 0.2, 0.3]
        client.embeddings.create.assert_awaited_once_with(
            model="gpt-4o-mini",
            input="Test text",
        )

    @pytest.mark.asyncio
    async def test_embedding_wraps_client_failure(self):
        client = MagicMock()
        client.embeddings.create = AsyncMock(side_effect=RuntimeError("boom"))

        with patch("src.core.llm.openai_adapter.AsyncOpenAI", return_value=client):
            adapter = OpenAIAdapter({"api_key": "test-key", "model": "gpt-4o-mini"})

            with pytest.raises(LLMRequestError, match="OpenAI embedding request failed"):
                await adapter.get_embedding("Test text")

    @pytest.mark.asyncio
    async def test_chat_retries_transient_openai_errors(self):
        chat_response = SimpleNamespace(
            choices=[SimpleNamespace(message=SimpleNamespace(content="recovered"))]
        )
        client = MagicMock()
        transient_error = openai.RateLimitError(
            "rate limited",
            response=MagicMock(request=MagicMock(), status_code=429),
            body={},
        )
        client.chat.completions.create = AsyncMock(
            side_effect=[transient_error, transient_error, chat_response]
        )

        with patch("src.core.llm.openai_adapter.AsyncOpenAI", return_value=client):
            adapter = OpenAIAdapter({"api_key": "test-key", "model": "gpt-4o-mini"})

            with patch("src.core.llm.retry.asyncio.sleep", new=AsyncMock()) as sleep_mock:
                result = await adapter.chat([{"role": "user", "content": "Hello"}])

        assert result["content"] == "recovered"
        assert client.chat.completions.create.await_count == 3
        assert sleep_mock.await_count == 2

    @pytest.mark.asyncio
    async def test_generate_retries_transient_openai_errors(self):
        response = SimpleNamespace(output_text="recovered")
        client = MagicMock()
        transient_error = openai.APITimeoutError(request=MagicMock())
        client.responses.create = AsyncMock(side_effect=[transient_error, response])

        with patch("src.core.llm.openai_adapter.AsyncOpenAI", return_value=client):
            adapter = OpenAIAdapter({"api_key": "test-key", "model": "gpt-4o-mini"})

            with patch("src.core.llm.retry.asyncio.sleep", new=AsyncMock()) as sleep_mock:
                result = await adapter.generate("Summarize")

        assert result == "recovered"
        assert client.responses.create.await_count == 2
        assert sleep_mock.await_count == 1

    @pytest.mark.asyncio
    async def test_embedding_retries_transient_openai_errors(self):
        response = SimpleNamespace(
            data=[SimpleNamespace(embedding=[0.4, 0.5, 0.6])]
        )
        client = MagicMock()
        transient_error = openai.APIConnectionError(message="disconnected", request=MagicMock())
        client.embeddings.create = AsyncMock(side_effect=[transient_error, response])

        with patch("src.core.llm.openai_adapter.AsyncOpenAI", return_value=client):
            adapter = OpenAIAdapter({"api_key": "test-key", "model": "text-embedding-3-small"})

            with patch("src.core.llm.retry.asyncio.sleep", new=AsyncMock()) as sleep_mock:
                result = await adapter.get_embedding("Retry me")

        assert result == [0.4, 0.5, 0.6]
        assert client.embeddings.create.await_count == 2
        assert sleep_mock.await_count == 1
