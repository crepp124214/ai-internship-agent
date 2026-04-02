from unittest.mock import AsyncMock, patch

import pytest

from src.core.llm import LLMProviderError


class TestTrackerAgent:
    def setup_method(self):
        self.llm = AsyncMock()
        self.llm.generate = AsyncMock(
            return_value=(
                "Summary: Strong backend progress.\n"
                "Next steps:\n"
                "- Follow up with recruiter\n"
                "- Tailor resume keywords\n"
                "Risks:\n"
                "- Limited SQL exposure\n"
                "- No recent application update"
            )
        )

    @pytest.mark.asyncio
    async def test_advise_next_steps_returns_structured_result(self):
        from src.business_logic.agents.tracker_agent import TrackerAgent

        agent = TrackerAgent(llm=self.llm)

        result = await agent.advise_next_steps(
            application_context="Applied 3 days ago; status: applied",
            job_context="Backend intern role",
            resume_context="Built FastAPI APIs",
        )

        assert result["mode"] == "tracker_advice"
        assert result["summary"] == "Strong backend progress."
        assert result["next_steps"] == [
            "Follow up with recruiter",
            "Tailor resume keywords",
        ]
        assert result["risks"] == [
            "Limited SQL exposure",
            "No recent application update",
        ]

    @pytest.mark.asyncio
    async def test_advise_next_steps_rejects_empty_application_context(self):
        from src.business_logic.agents.tracker_agent import EmptyTrackerAdviceInputError, TrackerAgent

        agent = TrackerAgent(llm=self.llm)

        with pytest.raises(EmptyTrackerAdviceInputError, match="application context is empty"):
            await agent.advise_next_steps(application_context="")

    @pytest.mark.asyncio
    async def test_advise_next_steps_wraps_llm_errors(self):
        from src.business_logic.agents.tracker_agent import TrackerAgent, TrackerLLMError

        self.llm.generate = AsyncMock(side_effect=RuntimeError("boom"))
        agent = TrackerAgent(llm=self.llm)

        with pytest.raises(TrackerLLMError, match="failed to generate tracker advice"):
            await agent.advise_next_steps(application_context="applied yesterday")

    def test_tracker_agent_uses_openai_provider_from_explicit_config(self):
        from src.business_logic.agents.tracker_agent import TrackerAgent

        llm = AsyncMock()
        llm.generate = AsyncMock(return_value="Summary: ready.\nNext steps:\n- follow up\nRisks:\n- none")

        with patch(
            "src.business_logic.agents.tracker_agent.tracker_agent.LLMFactory.create",
            return_value=llm,
        ) as mock_create:
            agent = TrackerAgent(config={"provider": "openai", "api_key": "test-key"})

        assert agent.llm is llm
        mock_create.assert_called_once()
        assert mock_create.call_args.args[0] == "openai"

    def test_explicit_openai_without_api_key_raises_provider_error(self):
        from src.business_logic.agents.tracker_agent import TrackerAgent

        with pytest.raises(LLMProviderError, match="OpenAI API key is required"):
            TrackerAgent(config={"provider": "openai"})

    def test_default_agent_falls_back_to_mock_when_key_is_missing(self):
        from src.business_logic.agents.tracker_agent import TrackerAgent

        agent = TrackerAgent(config={"provider": "openai"}, allow_mock_fallback=True)

        assert agent.llm.name == "mock_llm"
