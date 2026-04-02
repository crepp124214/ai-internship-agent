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
    async def test_llm_errors_are_wrapped(self):
        self.llm.generate = AsyncMock(side_effect=RuntimeError("boom"))

        with pytest.raises(ResumeLLMError, match="failed to generate resume summary"):
            await self.agent.extract_resume_summary("Senior engineer")

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

    def test_explicit_openai_without_api_key_raises_provider_error(self):
        with pytest.raises(LLMProviderError, match="OpenAI API key is required"):
            ResumeAgent(config={"provider": "openai"})

    def test_default_agent_falls_back_to_mock_when_key_is_missing(self):
        agent = ResumeAgent(config={"provider": "openai"}, allow_mock_fallback=True)

        assert agent.llm.name == "mock_llm"
