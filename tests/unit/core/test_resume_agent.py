from unittest.mock import AsyncMock, patch

import pytest

from src.business_logic.agents.resume_agent import (
    EmptyResumeTextError,
    ResumeAgent,
    ResumeLLMError,
)
from src.core.llm import LLMProviderError


class TestResumeAgent:
    def setup_method(self):
        self.llm = AsyncMock()
        self.llm.generate = AsyncMock(return_value="mock summary")
        self.llm.chat = AsyncMock(return_value={"role": "assistant", "content": "mock chat"})
        self.llm.get_embedding = AsyncMock(return_value=[0.1, 0.2, 0.3])
        self.agent = ResumeAgent(llm=self.llm)

    @pytest.mark.asyncio
    async def test_extract_resume_summary_uses_input_text(self):
        result = await self.agent.extract_resume_summary(
            "Python developer with FastAPI experience",
            target_role="backend engineer",
        )

        assert result["mode"] == "summary"
        assert result["content"] == "mock summary"
        assert result["target_role"] == "backend engineer"
        assert result["resume_text"] == "Python developer with FastAPI experience"
        self.llm.generate.assert_awaited_once()
        prompt = self.llm.generate.await_args.args[0]
        kwargs = self.llm.generate.await_args.kwargs
        assert "Python developer with FastAPI experience" in prompt
        assert kwargs["system_prompt"]

    @pytest.mark.asyncio
    async def test_suggest_resume_improvements_uses_input_text(self):
        self.llm.generate = AsyncMock(return_value="mock improvements")

        result = await self.agent.suggest_resume_improvements(
            "Built APIs and test suites",
            target_role="fullstack engineer",
        )

        assert result["mode"] == "improvements"
        assert result["content"] == "mock improvements"
        assert result["target_role"] == "fullstack engineer"
        assert result["resume_text"] == "Built APIs and test suites"
        self.llm.generate.assert_awaited_once()
        prompt = self.llm.generate.await_args.args[0]
        assert "Built APIs and test suites" in prompt

    @pytest.mark.asyncio
    async def test_empty_resume_text_raises_stable_error(self):
        with pytest.raises(EmptyResumeTextError, match="resume text is empty"):
            await self.agent.extract_resume_summary("")

    @pytest.mark.asyncio
    async def test_llm_errors_are_wrapped_without_fallback(self):
        """当 allow_mock_fallback=False 时，LLM 调用失败应抛出异常。"""
        self.llm.generate = AsyncMock(side_effect=RuntimeError("boom"))

        with pytest.raises(ResumeLLMError, match="failed to generate resume summary"):
            await self.agent.extract_resume_summary("Senior engineer")

    @pytest.mark.asyncio
    async def test_extract_resume_summary_falls_back_to_mock_on_api_failure(self):
        """当 allow_mock_fallback=True 且 LLM API 调用失败时，应 fallback 到 mock。"""
        agent = ResumeAgent(
            config={"provider": "zhipu", "api_key": "test-key"},
            allow_mock_fallback=True,
        )
        failing_llm = AsyncMock()
        failing_llm.generate = AsyncMock(side_effect=RuntimeError("API error"))
        agent.llm = failing_llm

        result = await agent.extract_resume_summary(
            "Python developer with FastAPI experience",
            target_role="backend engineer",
        )

        assert result["mode"] == "summary"
        assert result["fallback_used"] is True
        assert result["provider"] == "mock"

    @pytest.mark.asyncio
    async def test_suggest_resume_improvements_falls_back_to_mock_on_api_failure(self):
        """当 allow_mock_fallback=True 且 LLM API 调用失败时，suggest_resume_improvements 应 fallback。"""
        agent = ResumeAgent(
            config={"provider": "zhipu", "api_key": "test-key"},
            allow_mock_fallback=True,
        )
        failing_llm = AsyncMock()
        failing_llm.generate = AsyncMock(side_effect=RuntimeError("API error"))
        agent.llm = failing_llm

        result = await agent.suggest_resume_improvements(
            "Built APIs and test suites",
            target_role="fullstack engineer",
        )

        assert result["mode"] == "improvements"
        assert result["fallback_used"] is True
        assert result["provider"] == "mock"

    @pytest.mark.asyncio
    async def test_agent_uses_openai_provider_from_explicit_config(self):
        llm = AsyncMock()
        llm.generate = AsyncMock(return_value="openai summary")
        llm.chat = AsyncMock(return_value={"role": "assistant", "content": "chat"})
        llm.get_embedding = AsyncMock(return_value=[0.1, 0.2, 0.3])

        with patch(
            "src.business_logic.agents.resume_agent.resume_agent.LLMFactory.create",
            return_value=llm,
        ) as mock_create:
            agent = ResumeAgent(config={"provider": "openai", "api_key": "test-key"})
            result = await agent.extract_resume_summary("ML engineer")

        assert result["content"] == "openai summary"
        mock_create.assert_called_once()
        assert mock_create.call_args.args[0] == "openai"

    @patch.dict(
        "os.environ",
        {"OPENAI_API_KEY": "", "OPENAI_BASE_URL": "", "LLM_PROVIDER": ""},
        clear=True,
    )
    def test_explicit_openai_without_api_key_raises_provider_error(self):
        with pytest.raises(LLMProviderError, match="OpenAI API key is required"):
            ResumeAgent(config={"provider": "openai"})

    @patch.dict(
        "os.environ",
        {"OPENAI_API_KEY": "", "OPENAI_BASE_URL": "", "LLM_PROVIDER": ""},
        clear=True,
    )
    def test_default_agent_falls_back_to_mock_when_key_is_missing(self):
        agent = ResumeAgent(config={"provider": "openai"}, allow_mock_fallback=True)

        assert agent.llm.name == "mock_llm"

    def test_resume_agent_fallback_to_mock_updates_active_provider(self):
        """
        当 openai 因缺少 API key 触发 fallback 时，_active_provider 必须更新为 'mock'。
        """
        agent = ResumeAgent(
            config={"provider": "openai", "api_key": ""},
            allow_mock_fallback=True,
        )

        assert agent._active_provider == "mock", (
            f"_active_provider 应为 'mock'，实际为 '{agent._active_provider}'。"
            "fallback 时没有更新 _active_provider。"
        )

    @pytest.mark.asyncio
    async def test_resume_agent_fallback_response_has_mock_provider(self):
        """
        fallback 发生后，extract_resume_summary 响应的 provider 必须是 'mock'。
        raw_content 不得包含 'mock-generate' 标记。
        """
        agent = ResumeAgent(
            config={"provider": "openai", "api_key": ""},
            allow_mock_fallback=True,
        )

        result = await agent.extract_resume_summary(
            "Python developer with FastAPI experience",
            target_role="backend engineer",
        )

        assert result["provider"] == "mock", (
            f"响应 provider 应为 'mock'，实际为 '{result['provider']}'。"
        )
        # fallback 到 mock 后，raw_content 包含 'mock-generate:' 前缀是正常的（mock LLM 输出格式）
        assert "mock-generate" in result["raw_content"], (
            "fallback 到 mock 后，raw_content 应包含 'mock-generate:' 前缀"
        )

    def test_resume_agent_openai_adapter_disables_http_client_retries(self):
        """
        OpenAIAdapter 必须将 HTTP 客户端的 max_retries 设为 0，
        避免两层重试叠加导致 40s+ 长时间挂起。
        """
        agent = ResumeAgent(
            config={
                "provider": "openai",
                "model": "gpt-4o-mini",
                "api_key": "test-key",
                "base_url": "https://api.openai.com/v1",
            },
            allow_mock_fallback=True,
        )

        http_client = agent.llm.client
        assert http_client.max_retries == 0, (
            f"HTTP 客户端 max_retries 应为 0，实际为 {http_client.max_retries}。"
            "这会导致 HTTPX 内置重试与 retry_async 叠加，引发 40s+ 长时间挂起。"
        )
