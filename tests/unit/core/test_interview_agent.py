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
    async def test_llm_errors_are_wrapped_without_fallback(self):
        """当 allow_mock_fallback=False 时，LLM 调用失败应抛出异常。"""
        self.llm.generate = AsyncMock(side_effect=RuntimeError("boom"))

        with pytest.raises(InterviewLLMError, match="failed to generate interview questions"):
            await self.agent.generate_interview_questions("backend role")

    @pytest.mark.asyncio
    async def test_generate_interview_questions_falls_back_to_mock_on_api_failure(self):
        """当 allow_mock_fallback=True 且 LLM API 调用失败时，应 fallback 到 mock。"""
        agent = InterviewAgent(
            config={"provider": "zhipu", "api_key": "test-key"},
            allow_mock_fallback=True,
        )
        # 注入一个会失败的 mock llm
        failing_llm = AsyncMock()
        failing_llm.generate = AsyncMock(side_effect=RuntimeError("API error"))
        agent.llm = failing_llm

        result = await agent.generate_interview_questions(
            job_context="Backend intern role",
            resume_context="Built FastAPI APIs",
            count=2,
        )

        assert result["mode"] == "question_generation"
        assert len(result["questions"]) > 0
        assert result["fallback_used"] is True
        assert result["provider"] == "mock"

    @pytest.mark.asyncio
    async def test_evaluate_interview_answer_falls_back_to_mock_on_api_failure(self):
        """当 allow_mock_fallback=True 且 LLM API 调用失败时，evaluate_interview_answer 应 fallback。"""
        agent = InterviewAgent(
            config={"provider": "zhipu", "api_key": "test-key"},
            allow_mock_fallback=True,
        )
        failing_llm = AsyncMock()
        failing_llm.generate = AsyncMock(side_effect=RuntimeError("API error"))
        agent.llm = failing_llm

        result = await agent.evaluate_interview_answer(
            question_text="Explain DI",
            user_answer="It injects dependencies.",
        )

        assert result["mode"] == "answer_evaluation"
        assert result["score"] >= 0
        assert result["fallback_used"] is True
        assert result["provider"] == "mock"

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

    @patch.dict(
        "os.environ",
        {"OPENAI_API_KEY": "", "OPENAI_BASE_URL": "", "LLM_PROVIDER": ""},
        clear=True,
    )
    def test_explicit_openai_without_api_key_raises_provider_error(self):
        with pytest.raises(LLMProviderError, match="OpenAI API key is required"):
            InterviewAgent(config={"provider": "openai"})

    @patch.dict(
        "os.environ",
        {"OPENAI_API_KEY": "", "OPENAI_BASE_URL": "", "LLM_PROVIDER": ""},
        clear=True,
    )
    def test_default_agent_falls_back_to_mock_when_key_is_missing(self):
        agent = InterviewAgent(config={"provider": "openai"}, allow_mock_fallback=True)

        assert agent.llm.name == "mock_llm"

    def test_interview_agent_fallback_to_mock_updates_active_provider(self):
        """
        当 openai 因缺少 API key 触发 fallback 时，_active_provider 必须更新为 'mock'。
        """
        agent = InterviewAgent(
            config={"provider": "openai", "api_key": ""},
            allow_mock_fallback=True,
        )

        assert agent._active_provider == "mock", (
            f"_active_provider 应为 'mock'，实际为 '{agent._active_provider}'。"
            "fallback 时没有更新 _active_provider。"
        )

    @pytest.mark.asyncio
    async def test_interview_agent_fallback_response_has_mock_provider(self):
        """
        fallback 发生后，generate_interview_questions 响应的 provider 必须是 'mock'。
        raw_content 应为可消费的 mock 内容。
        """
        agent = InterviewAgent(
            config={"provider": "openai", "api_key": ""},
            allow_mock_fallback=True,
        )

        result = await agent.generate_interview_questions(
            job_context="Backend intern role",
            resume_context="Built FastAPI APIs",
            count=2,
        )

        assert result["provider"] == "mock", (
            f"响应 provider 应为 'mock'，实际为 '{result['provider']}'。"
        )
        assert result["raw_content"]
        assert result["status"] == "fallback"
        assert result["fallback_used"] is True

    def test_interview_agent_openai_adapter_disables_http_client_retries(self):
        """
        OpenAIAdapter 必须将 HTTP 客户端的 max_retries 设为 0，
        避免两层重试叠加导致 40s+ 长时间挂起。
        """
        agent = InterviewAgent(
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
