from unittest.mock import AsyncMock, patch

import pytest

from src.business_logic.agents.interview_agent import (
    EmptyInterviewInputError,
    InterviewAgent,
    InterviewAgentError,
    InterviewLLMError,
)
from src.core.llm import LLMProviderError


class TestInterviewAgent:
    def setup_method(self):
        self.llm = AsyncMock()
        self.llm.generate = AsyncMock(
            return_value=(
                "Question: Explain dependency injection.\n"
                "Question: How do you test FastAPI applications?"
            )
        )
        self.agent = InterviewAgent(llm=self.llm)

    @pytest.mark.asyncio
    async def test_generate_interview_questions_returns_structured_list(self):
        result = await self.agent.generate_interview_questions(
            job_context="Backend intern role focused on FastAPI and SQL",
            resume_context="Built REST APIs with Python",
            count=2,
        )

        assert result["mode"] == "question_generation"
        assert result["count"] == 2
        assert len(result["questions"]) == 2
        assert result["questions"][0]["question_text"] == "Explain dependency injection."
        self.llm.generate.assert_awaited_once()

    @pytest.mark.asyncio
    async def test_evaluate_interview_answer_returns_structured_result(self):
        self.llm.generate = AsyncMock(
            return_value="Score: 88\nFeedback: Strong answer with clear examples."
        )

        result = await self.agent.evaluate_interview_answer(
            question_text="Explain dependency injection",
            user_answer="It wires dependencies into handlers.",
            job_context="Backend intern role",
        )

        assert result["mode"] == "answer_evaluation"
        assert result["score"] == 88
        assert "Strong answer" in result["feedback"]

    @pytest.mark.asyncio
    async def test_missing_job_context_raises_stable_error(self):
        with pytest.raises(EmptyInterviewInputError, match="job context is empty"):
            await self.agent.generate_interview_questions(job_context="")

    @pytest.mark.asyncio
    async def test_missing_answer_input_raises_stable_error(self):
        with pytest.raises(EmptyInterviewInputError, match="question text is empty"):
            await self.agent.evaluate_interview_answer("", "answer")

    @pytest.mark.asyncio
    async def test_llm_errors_are_wrapped(self):
        self.llm.generate = AsyncMock(side_effect=RuntimeError("boom"))

        with pytest.raises(InterviewLLMError, match="failed to generate interview questions"):
            await self.agent.generate_interview_questions("backend role")

    @pytest.mark.asyncio
    async def test_agent_uses_openai_provider_from_explicit_config(self):
        llm = AsyncMock()
        llm.generate = AsyncMock(return_value="Question: Tell me about a project.")

        with patch(
            "src.business_logic.agents.interview_agent.interview_agent.LLMFactory.create",
            return_value=llm,
        ) as mock_create:
            agent = InterviewAgent(config={"provider": "openai", "api_key": "test-key"})
            result = await agent.generate_interview_questions("ML intern")

        assert len(result["questions"]) == 1
        mock_create.assert_called_once()
        assert mock_create.call_args.args[0] == "openai"

    def test_explicit_openai_without_api_key_raises_provider_error(self):
        with pytest.raises(LLMProviderError, match="OpenAI API key is required"):
            InterviewAgent(config={"provider": "openai"})

    def test_default_agent_falls_back_to_mock_when_key_is_missing(self):
        agent = InterviewAgent(config={"provider": "openai"}, allow_mock_fallback=True)

        assert agent.llm.name == "mock_llm"
