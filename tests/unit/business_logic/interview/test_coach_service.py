"""Unit tests for coach service."""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from src.business_logic.interview.coach_service import CoachService


class TestCoachService:
    def setup_method(self):
        self.service = CoachService()

    @pytest.mark.asyncio
    async def test_start_session_uses_user_llm_config(self):
        """用户配置了 LLM 时，coach start 应使用用户配置。"""
        mock_db = MagicMock()
        mock_user = MagicMock()
        mock_user.id = 55

        mock_job = MagicMock()
        mock_job.id = 2
        mock_job.title = "Backend Intern"
        mock_job.description = "Python, FastAPI"

        mock_resume = MagicMock()
        mock_resume.id = 2
        mock_resume.user_id = 55
        mock_resume.processed_content = "Built APIs"

        mock_session = MagicMock()
        mock_session.id = 1

        user_llm_config = {
            "provider": "zhipu",
            "model": "glm-4.5-air",
            "api_key": "user-key",
            "base_url": None,
            "temperature": 0.7,
        }

        with patch("src.business_logic.interview.coach_service.user_llm_config_service") as mock_cfg_svc:
            with patch("src.business_logic.interview.coach_service.InterviewSessionManager") as MockManager:
                with patch("src.business_logic.interview.coach_service.InterviewCoachAgent") as MockCoachAgent:
                    with patch("src.business_logic.interview.coach_service.ReviewReportGenerator") as MockReportGen:
                        mock_cfg_svc.get_config_for_agent.return_value = user_llm_config

                        # Mock manager instance
                        mock_manager_instance = MagicMock()
                        mock_manager_instance.start.return_value = {
                            "session_id": 1,
                            "opening_message": "你好",
                            "first_question": "自我介绍",
                            "total_questions": 5,
                        }
                        MockManager.return_value = mock_manager_instance

                        result = self.service.start_session(
                            db=mock_db,
                            user=mock_user,
                            jd_id=2,
                            resume_id=2,
                            question_count=5,
                        )

        # Verify user config was fetched
        mock_cfg_svc.get_config_for_agent.assert_called_once_with(mock_db, 55, "interview_agent")

        # Verify LiteLLMAdapter was created with user config
        from src.core.llm.litellm_adapter import LiteLLMAdapter
        MockCoachAgent.assert_called_once()
        call_kwargs = MockCoachAgent.call_args.kwargs
        assert call_kwargs.get("llm") is not None
        llm_instance = call_kwargs["llm"]
        assert isinstance(llm_instance, LiteLLMAdapter)
        assert llm_instance.model == "glm-4.5-air"

    @pytest.mark.asyncio
    async def test_start_session_falls_back_to_default_llm_without_user_config(self):
        """用户未配置 LLM 时，coach start 应使用默认配置。"""
        mock_db = MagicMock()
        mock_user = MagicMock()
        mock_user.id = 55

        mock_session = MagicMock()
        mock_session.id = 1

        with patch("src.business_logic.interview.coach_service.user_llm_config_service") as mock_cfg_svc:
            with patch("src.business_logic.interview.coach_service.InterviewSessionManager") as MockManager:
                with patch("src.business_logic.interview.coach_service.InterviewCoachAgent") as MockCoachAgent:
                    with patch("src.business_logic.interview.coach_service.ReviewReportGenerator") as MockReportGen:
                        mock_cfg_svc.get_config_for_agent.return_value = None  # No user config

                        mock_manager_instance = MagicMock()
                        mock_manager_instance.start.return_value = {
                            "session_id": 1,
                            "opening_message": "你好",
                            "first_question": "自我介绍",
                            "total_questions": 5,
                        }
                        MockManager.return_value = mock_manager_instance

                        result = self.service.start_session(
                            db=mock_db,
                            user=mock_user,
                            jd_id=2,
                            resume_id=2,
                            question_count=5,
                        )

        # Verify LiteLLMAdapter was created with default config
        MockCoachAgent.assert_called_once()
        call_kwargs = MockCoachAgent.call_args.kwargs
        llm_instance = call_kwargs.get("llm")
        assert llm_instance is not None
