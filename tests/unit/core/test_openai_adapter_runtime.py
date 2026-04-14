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
        # max_retries 必须为 0，禁用 HTTPX 内置重试，避免与 retry_async 装饰器叠加
        # 造成 40s+ 长时间挂起。所有重试统一由 retry_async 处理。
        assert mock_openai.call_args.kwargs["max_retries"] == 0
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
        # max_retries 强制为 0，不接受用户配置的 max_retries
        assert mock_openai.call_args.kwargs["max_retries"] == 0

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
        # max_retries 强制为 0，不接受环境变量中的 OPENAI_MAX_RETRIES
        assert mock_openai.call_args.kwargs["max_retries"] == 0

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
    async def test_chat_disables_zhipu_thinking_by_default(self):
        chat_response = SimpleNamespace(
            choices=[SimpleNamespace(message=SimpleNamespace(content="usable content"))]
        )
        client = MagicMock()
        client.chat.completions.create = AsyncMock(return_value=chat_response)
        client.responses.create = AsyncMock(
            side_effect=openai.NotFoundError(
                "not found",
                response=MagicMock(request=MagicMock(), status_code=404),
                body={},
            )
        )

        with patch("src.core.llm.openai_adapter.AsyncOpenAI", return_value=client):
            adapter = OpenAIAdapter(
                {
                    "provider": "zhipu",
                    "api_key": "test-key",
                    "model": "glm-4.7",
                    "base_url": "https://open.bigmodel.cn/api/paas/v4",
                }
            )

            result = await adapter.generate("Generate a short summary")

        assert result == "usable content"
        chat_kwargs = client.chat.completions.create.await_args.kwargs
        assert chat_kwargs["extra_body"] == {"thinking": {"type": "disabled"}}
        client.responses.create.assert_not_awaited()

    @pytest.mark.asyncio
    async def test_generate_skips_responses_api_for_minimax_profile(self):
        chat_response = SimpleNamespace(
            choices=[SimpleNamespace(message=SimpleNamespace(content="minimax content"))]
        )
        client = MagicMock()
        client.chat.completions.create = AsyncMock(return_value=chat_response)
        client.responses.create = AsyncMock()

        with patch("src.core.llm.openai_adapter.AsyncOpenAI", return_value=client):
            adapter = OpenAIAdapter(
                {
                    "provider": "minimax",
                    "api_key": "test-key",
                    "model": "abab6.5s-chat",
                    "base_url": "https://api.minimax.chat/v1",
                }
            )

            result = await adapter.generate("Generate a short summary")

        assert result == "minimax content"
        client.responses.create.assert_not_awaited()
        client.chat.completions.create.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_generate_retries_transient_openai_errors(self):
        """验证 retry_async 在真正的可重试错误（如 RateLimitError）上重试。

        APITimeoutError 不应触发重试（httpx 已等待 timeout 秒，重试只会增加延迟），
        但 RateLimitError 等真正的可重试错误应该被 retry_async 重试。
        """
        response = SimpleNamespace(output_text="recovered")
        client = MagicMock()
        rate_limit_error = openai.RateLimitError(
            "rate limited",
            response=MagicMock(request=MagicMock(), status_code=429),
            body={},
        )
        client.responses.create = AsyncMock(side_effect=[rate_limit_error, response])

        with patch("src.core.llm.openai_adapter.AsyncOpenAI", return_value=client):
            adapter = OpenAIAdapter({"api_key": "test-key", "model": "gpt-4o-mini"})

            with patch("src.core.llm.retry.asyncio.sleep", new=AsyncMock()) as sleep_mock:
                result = await adapter.generate("Summarize")

        assert result == "recovered"
        assert client.responses.create.await_count == 2

    def test_init_defaults_to_10s_timeout_when_not_specified(self, monkeypatch):
        """修复回归：timeout=None 时 OS TCP 重传导致连接黑洞地址挂起 30s+。

        当 config 中未指定 timeout 时，OpenAIAdapter 应使用默认 10s timeout，
        避免连接 127.0.0.1:9 这类黑洞地址时长时间挂起。
        """
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)
        monkeypatch.delenv("OPENAI_TIMEOUT", raising=False)
        monkeypatch.setenv("OPENAI_API_KEY", "test-key")

        client = MagicMock()
        with patch("src.core.llm.openai_adapter.AsyncOpenAI", return_value=client) as mock_openai:
            adapter = OpenAIAdapter({})

        # timeout 必须为 10.0（默认值），不能是 None
        assert mock_openai.call_args.kwargs["timeout"] == 10.0
        # max_retries 强制为 0
        assert mock_openai.call_args.kwargs["max_retries"] == 0

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

    def test_deepseek_uses_chat_completion_not_responses_api(self, monkeypatch):
        """DeepSeek does not support responses API; verify model/env var resolution."""
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)
        monkeypatch.delenv("DEEPSEEK_API_KEY", raising=False)
        monkeypatch.setenv("DEEPSEEK_API_KEY", "deepseek-test-key")

        client = MagicMock()
        with patch("src.core.llm.openai_adapter.AsyncOpenAI", return_value=client):
            adapter = OpenAIAdapter(
                {
                    "provider": "deepseek",
                    "model": "deepseek-chat",
                }
            )

        assert adapter.provider_name == "deepseek"
        assert adapter.api_key == "deepseek-test-key"
        assert adapter.model == "deepseek-chat"

    def test_qwen_resolves_correct_env_vars(self, monkeypatch):
        """Qwen should use QWEN_MODEL and QWEN_API_KEY env vars."""
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)
        monkeypatch.delenv("QWEN_API_KEY", raising=False)
        monkeypatch.setenv("QWEN_API_KEY", "qwen-test-key")
        monkeypatch.setenv("QWEN_MODEL", "qwen-plus")

        client = MagicMock()
        with patch("src.core.llm.openai_adapter.AsyncOpenAI", return_value=client):
            adapter = OpenAIAdapter({"provider": "qwen"})

        assert adapter.provider_name == "qwen"
        assert adapter.api_key == "qwen-test-key"
        assert adapter.model == "qwen-plus"

    def test_moonshot_resolves_correct_env_vars(self, monkeypatch):
        """Moonshot should use MOONSHOT_MODEL and MOONSHOT_API_KEY env vars."""
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)
        monkeypatch.setenv("MOONSHOT_API_KEY", "moonshot-test-key")
        monkeypatch.setenv("MOONSHOT_MODEL", "moonshot-v1-8k")

        client = MagicMock()
        with patch("src.core.llm.openai_adapter.AsyncOpenAI", return_value=client):
            adapter = OpenAIAdapter({"provider": "moonshot"})

        assert adapter.provider_name == "moonshot"
        assert adapter.api_key == "moonshot-test-key"
        assert adapter.model == "moonshot-v1-8k"

    def test_siliconflow_resolves_correct_env_vars(self, monkeypatch):
        """SiliconFlow should use SILICONFLOW_MODEL and SILICONFLOW_API_KEY env vars."""
        monkeypatch.delenv("OPENAI_API_KEY", raising=False)
        monkeypatch.setenv("SILICONFLOW_API_KEY", "sf-test-key")
        monkeypatch.setenv("SILICONFLOW_MODEL", "deepseek-chat")

        client = MagicMock()
        with patch("src.core.llm.openai_adapter.AsyncOpenAI", return_value=client):
            adapter = OpenAIAdapter({"provider": "siliconflow"})

        assert adapter.provider_name == "siliconflow"
        assert adapter.api_key == "sf-test-key"
        assert adapter.model == "deepseek-chat"

    @pytest.mark.asyncio
    async def test_generate_uses_responses_api_for_openai(self):
        """OpenAI (the provider) should try responses API first."""
        response = SimpleNamespace(output_text="hello from openai")
        client = MagicMock()
        client.responses.create = AsyncMock(return_value=response)

        with patch("src.core.llm.openai_adapter.AsyncOpenAI", return_value=client):
            adapter = OpenAIAdapter(
                {
                    "provider": "openai",
                    "api_key": "test-key",
                    "model": "gpt-4o-mini",
                }
            )
            result = await adapter.generate("Say hello")

        assert result == "hello from openai"
        client.responses.create.assert_awaited_once()
        client.chat.completions.create.assert_not_called()

    @pytest.mark.asyncio
    async def test_generate_uses_chat_for_deepseek(self):
        """DeepSeek should skip responses API and go straight to chat completions."""
        chat_response = SimpleNamespace(
            choices=[SimpleNamespace(message=SimpleNamespace(content="deepseek reply"))]
        )
        client = MagicMock()
        client.chat.completions.create = AsyncMock(return_value=chat_response)
        client.responses.create = AsyncMock()

        with patch("src.core.llm.openai_adapter.AsyncOpenAI", return_value=client):
            adapter = OpenAIAdapter(
                {
                    "provider": "deepseek",
                    "api_key": "test-key",
                    "model": "deepseek-chat",
                }
            )
            result = await adapter.generate("Say hello")

        assert result == "deepseek reply"
        client.responses.create.assert_not_called()
        client.chat.completions.create.assert_awaited_once()
