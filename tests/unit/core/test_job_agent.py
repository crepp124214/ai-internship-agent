from unittest.mock import AsyncMock, patch

import pytest

import src.business_logic.agents.job_agent as job_agent_module
from src.core.llm import LLMProviderError


class TestJobAgent:
    def setup_method(self):
        self.llm = AsyncMock()
        self.llm.generate = AsyncMock(return_value="Score: 86\nFeedback: Strong fit.")
        self.llm.chat = AsyncMock(return_value={"role": "assistant", "content": "mock chat"})
        self.llm.get_embedding = AsyncMock(return_value=[0.1, 0.2, 0.3])

    @pytest.mark.asyncio
    async def test_match_job_to_resume_returns_structured_result(self):
        agent = job_agent_module.JobAgent(llm=self.llm)

        result = await agent.match_job_to_resume(
            job_context="Backend intern role",
            resume_context="Built FastAPI APIs and tests",
        )

        assert result["mode"] == "job_match"
        assert result["job_context"] == "Backend intern role"
        assert result["resume_context"] == "Built FastAPI APIs and tests"
        assert result["score"] == 86
        assert "Strong fit" in result["feedback"]

    @pytest.mark.asyncio
    async def test_match_job_to_resume_rejects_empty_resume_text(self):
        agent = job_agent_module.JobAgent(llm=self.llm)

        with pytest.raises(job_agent_module.EmptyJobResumeTextError, match="resume text is empty"):
            await agent.match_job_to_resume(
                job_context="Backend intern role",
                resume_context="",
            )

    @pytest.mark.asyncio
    async def test_match_job_to_resume_wraps_llm_errors(self):
        self.llm.generate = AsyncMock(side_effect=RuntimeError("boom"))
        agent = job_agent_module.JobAgent(llm=self.llm)

        with pytest.raises(job_agent_module.JobMatchLLMError, match="failed to match job and resume"):
            await agent.match_job_to_resume(
                job_context="Backend intern role",
                resume_context="Built FastAPI APIs and tests",
            )

    def test_job_agent_uses_openai_provider_from_explicit_config(self):
        agent = job_agent_module.JobAgent(config={"provider": "openai", "api_key": "test-key"})

        assert agent.llm is not None

    @patch.dict(
        "os.environ",
        {"OPENAI_API_KEY": "", "OPENAI_BASE_URL": "", "LLM_PROVIDER": ""},
        clear=True,
    )
    def test_job_agent_rejects_openai_without_api_key(self):
        with pytest.raises(LLMProviderError, match="OpenAI API key is required"):
            job_agent_module.JobAgent(config={"provider": "openai"})
