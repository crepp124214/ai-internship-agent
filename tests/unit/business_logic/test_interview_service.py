"""Unit tests for the interview service."""

from datetime import datetime
from types import SimpleNamespace
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from src.business_logic.interview.service import InterviewService
from src.presentation.schemas.interview import (
    InterviewRecordCreate,
    InterviewQuestionSetCreate,
    InterviewQuestionSetUpdate,
    InterviewQuestionUpdate,
    InterviewSessionCreate,
    InterviewRecordUpdate,
    InterviewSessionUpdate,
)


class TestInterviewService:
    def setup_method(self):
        self.interview_agent = MagicMock()
        self.interview_agent.generate_interview_questions = AsyncMock()
        self.interview_agent.evaluate_interview_answer = AsyncMock()
        self.service = InterviewService(interview_agent=self.interview_agent)
        self.mock_db = MagicMock()

    @pytest.mark.asyncio
    async def test_update_question_uses_partial_payload(self):
        """Updating a question should forward only provided fields."""
        question_data = InterviewQuestionUpdate(question_text="Updated question")
        mock_question = MagicMock(id=42)

        with patch("src.business_logic.interview.service.interview_question_repository") as mock_repo:
            mock_repo.update.return_value = mock_question

            result = await self.service.update_question(self.mock_db, 42, question_data)

            assert result is mock_question
            mock_repo.update.assert_called_once_with(
                self.mock_db,
                42,
                {"question_text": "Updated question"},
            )

    @pytest.mark.asyncio
    async def test_update_session_uses_partial_payload(self):
        """Updating a session should forward only provided fields."""
        session_data = InterviewSessionUpdate(duration=45, completed=1)
        mock_session = MagicMock(id=7)

        with patch("src.business_logic.interview.service.interview_session_repository") as mock_repo:
            mock_repo.update.return_value = mock_session

            result = await self.service.update_session(self.mock_db, 7, session_data)

            assert result is mock_session
            mock_repo.update.assert_called_once_with(
                self.mock_db,
                7,
                {"duration": 45, "completed": 1},
            )

    @pytest.mark.asyncio
    async def test_update_record_uses_partial_payload(self):
        """Updating a record should forward only provided fields."""
        record_data = InterviewRecordUpdate(score=95, feedback="Great answer")
        mock_record = MagicMock(id=11)

        with patch("src.business_logic.interview.service.interview_record_repository") as mock_repo:
            mock_repo.update.return_value = mock_record

            result = await self.service.update_record(self.mock_db, 11, record_data)

            assert result is mock_record
            mock_repo.update.assert_called_once_with(
                self.mock_db,
                11,
                {"score": 95, "feedback": "Great answer"},
            )

    @pytest.mark.asyncio
    async def test_get_questions_by_category_delegates_to_repository(self):
        """Category lookup should use the interview question repository."""
        mock_questions = [MagicMock(id=1), MagicMock(id=2)]

        with patch("src.business_logic.interview.service.interview_question_repository") as mock_repo:
            mock_repo.get_by_field.return_value = mock_questions

            result = await self.service.get_questions_by_category(self.mock_db, "backend")

            assert result is mock_questions
            mock_repo.get_by_field.assert_called_once_with(self.mock_db, "category", "backend")

    @pytest.mark.asyncio
    async def test_get_random_questions_limits_result_count(self):
        """Random question retrieval should return a bounded, non-repeating sample."""
        mock_questions = [MagicMock(id=i) for i in range(1, 6)]

        with patch("src.business_logic.interview.service.interview_question_repository") as mock_repo:
            mock_repo.get_all.return_value = mock_questions
            with patch("src.business_logic.interview.service.random.sample") as mock_sample:
                mock_sample.return_value = [mock_questions[4], mock_questions[1], mock_questions[3]]
                result = await self.service.get_random_questions(self.mock_db, count=3)

        assert [question.id for question in result] == [5, 2, 4]
        mock_sample.assert_called_once_with(mock_questions, 3)
        mock_repo.get_all.assert_called_once_with(self.mock_db)

    @pytest.mark.asyncio
    async def test_get_random_questions_returns_all_when_count_exceeds_pool(self):
        """Random question retrieval should return all questions when the pool is smaller than count."""
        mock_questions = [MagicMock(id=1), MagicMock(id=2)]

        with patch("src.business_logic.interview.service.interview_question_repository") as mock_repo:
            mock_repo.get_all.return_value = mock_questions
            result = await self.service.get_random_questions(self.mock_db, count=5)

        assert result == mock_questions

    @pytest.mark.asyncio
    async def test_create_session_injects_current_user_id(self):
        """Creating a session should add the authenticated user id."""
        session_data = InterviewSessionCreate(job_id=9, duration=30, total_questions=5)
        mock_session = MagicMock(id=101)

        with patch("src.business_logic.interview.service.interview_session_repository") as mock_repo:
            mock_repo.create.return_value = mock_session

            result = await self.service.create_session(self.mock_db, session_data, current_user_id=55)

            assert result is mock_session
            mock_repo.create.assert_called_once_with(
                self.mock_db,
                {
                    "job_id": 9,
                    "session_type": "technical",
                    "duration": 30,
                    "total_questions": 5,
                    "average_score": None,
                    "completed": 0,
                    "user_id": 55,
                },
            )

    @pytest.mark.asyncio
    async def test_list_sessions_filters_by_current_user_id(self):
        """Listing sessions should scope results to the authenticated user."""
        mock_sessions = [MagicMock(id=1), MagicMock(id=2)]

        with patch("src.business_logic.interview.service.interview_session_repository") as mock_repo:
            mock_repo.get_by_field.return_value = mock_sessions

            result = await self.service.get_sessions(self.mock_db, current_user_id=55)

            assert result is mock_sessions
            mock_repo.get_by_field.assert_called_once_with(self.mock_db, "user_id", 55)

    @pytest.mark.asyncio
    async def test_create_record_injects_current_user_id(self):
        """Creating a record should add the authenticated user id."""
        record_data = InterviewRecordCreate(
            job_id=9,
            question_id=77,
            user_answer="answer",
            ai_evaluation="",
            score=90,
            feedback="good",
        )
        mock_record = MagicMock(id=202)

        with patch("src.business_logic.interview.service.interview_record_repository") as mock_repo:
            mock_repo.create.return_value = mock_record

            result = await self.service.create_record(self.mock_db, record_data, current_user_id=55)

            assert result is mock_record
            mock_repo.create.assert_called_once_with(
                self.mock_db,
                {
                    "job_id": 9,
                    "question_id": 77,
                    "user_answer": "answer",
                    "ai_evaluation": "",
                    "score": 90,
                    "feedback": "good",
                    "status": "success",
                    "fallback_used": False,
                    "user_id": 55,
                },
            )

    @pytest.mark.asyncio
    async def test_list_records_filters_by_current_user_id(self):
        """Listing records should scope results to the authenticated user."""
        mock_records = [MagicMock(id=3)]

        with patch("src.business_logic.interview.service.interview_record_repository") as mock_repo:
            mock_repo.get_by_field.return_value = mock_records

            result = await self.service.get_records(self.mock_db, current_user_id=55)

            assert result is mock_records
            mock_repo.get_by_field.assert_called_once_with(self.mock_db, "user_id", 55)

    @pytest.mark.asyncio
    async def test_generate_questions_for_job_uses_optional_resume_context(self):
        resume = SimpleNamespace(processed_content="", resume_text="Built FastAPI services")

        with patch("src.business_logic.interview.service.resume_repository") as mock_resume_repo:
            with patch("src.business_logic.interview.service.InterviewAgent") as MockInterviewAgent:
                mock_resume_repo.get_by_id_and_user_id.return_value = resume

                mock_agent = MagicMock()
                mock_agent.generate_interview_questions = AsyncMock(return_value={
                    "mode": "question_generation",
                    "questions": [{"question_text": "Explain dependency injection."}],
                })
                MockInterviewAgent.return_value = mock_agent

                result = await self.service.generate_questions_for_job(
                    self.mock_db,
                    current_user_id=55,
                    job_context="Backend intern role",
                    resume_id=9,
                )

        assert len(result["questions"]) == 1
        mock_agent.generate_interview_questions.assert_awaited_once_with(
            job_context="Backend intern role",
            resume_context="Built FastAPI services",
            count=5,
        )
        mock_resume_repo.get_by_id_and_user_id.assert_called_once_with(self.mock_db, 9, 55)

    @pytest.mark.asyncio
    async def test_generate_interview_questions_preview_delegates_to_existing_generation_flow(self):
        with patch.object(
            self.service,
            "generate_questions_for_job",
            new=AsyncMock(return_value={"questions": []}),
        ) as mock_generate:
            result = await self.service.generate_interview_questions_preview(
                self.mock_db,
                current_user_id=55,
                job_context="Backend intern role",
                resume_id=9,
                count=3,
            )

        assert result == {"questions": []}
        mock_generate.assert_awaited_once_with(
            self.mock_db,
            current_user_id=55,
            job_context="Backend intern role",
            resume_id=9,
            count=3,
        )

    @pytest.mark.asyncio
    async def test_evaluate_answer_delegates_to_interview_agent(self):
        self.interview_agent.evaluate_interview_answer.return_value = {
            "mode": "answer_evaluation",
            "score": 91,
            "feedback": "Clear answer.",
        }

        result = await self.service.evaluate_answer(
            question_text="Explain dependency injection",
            user_answer="It injects dependencies into handlers.",
            job_context="Backend intern role",
        )

        assert result["score"] == 91
        self.interview_agent.evaluate_interview_answer.assert_awaited_once_with(
            question_text="Explain dependency injection",
            user_answer="It injects dependencies into handlers.",
            job_context="Backend intern role",
        )

    @pytest.mark.asyncio
    async def test_evaluate_interview_answer_preview_delegates_to_existing_evaluation_flow(self):
        with patch.object(
            self.service,
            "evaluate_answer",
            new=AsyncMock(return_value={"score": 91}),
        ) as mock_evaluate:
            result = await self.service.evaluate_interview_answer_preview(
                question_text="Explain dependency injection",
                user_answer="It injects dependencies into handlers.",
                job_context="Backend intern role",
            )

        assert result == {"score": 91}
        mock_evaluate.assert_awaited_once_with(
            question_text="Explain dependency injection",
            user_answer="It injects dependencies into handlers.",
            job_context="Backend intern role",
        )

    def test_service_can_build_default_agent_from_config(self):
        with patch("src.business_logic.interview.service.InterviewAgent") as mock_agent_cls:
            mock_instance = MagicMock()
            mock_agent_cls.return_value = mock_instance

            service = InterviewService(
                interview_agent=None,
                interview_agent_config={"provider": "mock", "model": "mock-model"},
            )

        assert service.interview_agent is mock_instance
        mock_agent_cls.assert_called_once_with(
            config={"provider": "mock", "model": "mock-model"},
            allow_mock_fallback=True,
        )

    @pytest.mark.asyncio
    async def test_evaluate_record_answer_persists_generated_feedback(self):
        record = SimpleNamespace(
            id=7,
            user_id=55,
            job_id=9,
            question_id=3,
            user_answer="It injects dependencies into handlers.",
            answered_at=None,
        )
        question = SimpleNamespace(question_text="Explain dependency injection")
        updated_record = SimpleNamespace(id=7, score=94, feedback="Clear answer", ai_evaluation="raw eval")
        self.interview_agent.evaluate_interview_answer.return_value = {
            "score": 94,
            "feedback": "Clear answer",
            "raw_content": "raw eval",
            "provider": "mock",
            "model": "mock-model",
        }

        with patch("src.business_logic.interview.service.interview_record_repository") as mock_record_repo:
            with patch("src.business_logic.interview.service.interview_question_repository") as mock_question_repo:
                mock_record_repo.get_by_id.return_value = record
                mock_question_repo.get_by_id.return_value = question
                mock_record_repo.update.return_value = updated_record

                result = await self.service.evaluate_record_answer(
                    self.mock_db,
                    record_id=7,
                    current_user_id=55,
                )

        assert result is updated_record
        self.interview_agent.evaluate_interview_answer.assert_awaited_once_with(
            question_text="Explain dependency injection",
            user_answer="It injects dependencies into handlers.",
            job_context=None,
        )
        update_payload = mock_record_repo.update.call_args.args[2]
        assert update_payload["score"] == 94
        assert update_payload["feedback"] == "Clear answer"
        assert update_payload["ai_evaluation"] == "raw eval"
        assert update_payload["provider"] == "mock"
        assert update_payload["model"] == "mock-model"
        assert isinstance(update_payload["answered_at"], datetime)

    @pytest.mark.asyncio
    async def test_evaluate_record_answer_persists_provider_and_model_metadata(self):
        record = SimpleNamespace(
            id=8,
            user_id=55,
            job_id=9,
            question_id=3,
            user_answer="It injects dependencies into handlers.",
            answered_at=None,
        )
        question = SimpleNamespace(question_text="Explain dependency injection")
        updated_record = SimpleNamespace(
            id=8,
            score=94,
            feedback="Clear answer",
            ai_evaluation="raw eval",
            provider="mock",
            model="mock-model",
        )
        self.interview_agent.evaluate_interview_answer.return_value = {
            "score": 94,
            "feedback": "Clear answer",
            "raw_content": "raw eval",
            "provider": "mock",
            "model": "mock-model",
        }

        with patch("src.business_logic.interview.service.interview_record_repository") as mock_record_repo:
            with patch("src.business_logic.interview.service.interview_question_repository") as mock_question_repo:
                mock_record_repo.get_by_id.return_value = record
                mock_question_repo.get_by_id.return_value = question
                mock_record_repo.update.return_value = updated_record

                result = await self.service.evaluate_record_answer(
                    self.mock_db,
                    record_id=8,
                    current_user_id=55,
                )

        assert result is updated_record
        update_payload = mock_record_repo.update.call_args.args[2]
        assert update_payload["provider"] == "mock"
        assert update_payload["model"] == "mock-model"
        assert result.provider == "mock"
        assert result.model == "mock-model"

    @pytest.mark.asyncio
    async def test_evaluate_record_answer_rejects_records_from_other_users(self):
        record = SimpleNamespace(
            id=7,
            user_id=99,
            job_id=9,
            question_id=3,
            user_answer="answer",
            answered_at=None,
        )

        with patch("src.business_logic.interview.service.interview_record_repository") as mock_record_repo:
            mock_record_repo.get_by_id.return_value = record

            with pytest.raises(ValueError, match="interview record not found"):
                await self.service.evaluate_record_answer(
                    self.mock_db,
                    record_id=7,
                    current_user_id=55,
                )

    @pytest.mark.asyncio
    async def test_persist_interview_record_evaluation_delegates_to_existing_record_flow(self):
        with patch.object(
            self.service,
            "evaluate_record_answer",
            new=AsyncMock(return_value=SimpleNamespace(id=8)),
        ) as mock_persist:
            result = await self.service.persist_interview_record_evaluation(
                self.mock_db,
                record_id=8,
                current_user_id=55,
                job_context="Backend intern role",
            )

        assert result.id == 8
        mock_persist.assert_awaited_once_with(
            self.mock_db,
            record_id=8,
            current_user_id=55,
            job_context="Backend intern role",
        )

    @pytest.mark.asyncio
    async def test_evaluate_record_answer_requires_question_and_answer(self):
        record = SimpleNamespace(
            id=7,
            user_id=55,
            job_id=9,
            question_id=None,
            user_answer="",
            answered_at=None,
        )

        with patch("src.business_logic.interview.service.interview_record_repository") as mock_record_repo:
            mock_record_repo.get_by_id.return_value = record

            with pytest.raises(ValueError, match="interview record is missing required evaluation input"):
                await self.service.evaluate_record_answer(
                    self.mock_db,
                    record_id=7,
                    current_user_id=55,
                )

    @pytest.mark.asyncio
    async def test_generate_questions_for_job_uses_user_llm_config(self):
        """用户配置了 LLM 时，generate_questions_for_job 应使用用户配置而非默认 mock。"""
        resume = SimpleNamespace(processed_content="", resume_text="Built FastAPI services")
        user_id = 55
        mock_user_config = {
            "provider": "zhipu",
            "model": "glm-4.5-air",
            "api_key": "user-key",
            "base_url": None,
            "temperature": 0.7,
        }

        with patch("src.business_logic.interview.service.resume_repository") as mock_resume_repo:
            with patch("src.business_logic.interview.service.InterviewAgent") as MockInterviewAgent:
                with patch("src.business_logic.user_llm_config_service.user_llm_config_service") as mock_ullcs:
                    mock_resume_repo.get_by_id_and_user_id.return_value = resume

                    # Mock agent instance returned by InterviewAgent constructor
                    mock_agent_instance = MagicMock()
                    mock_agent_instance.generate_interview_questions = AsyncMock(return_value={
                        "mode": "question_generation",
                        "questions": [{"question_text": "Explain FastAPI."}],
                        "provider": "zhipu",
                        "model": "glm-4.5-air",
                    })
                    mock_agent_instance.config = mock_user_config
                    MockInterviewAgent.return_value = mock_agent_instance

                    # Override autouse fixture to return actual user config
                    mock_ullcs.get_config_for_agent.return_value = mock_user_config

                    result = await self.service.generate_questions_for_job(
                        self.mock_db,
                        current_user_id=user_id,
                        job_context="Backend intern role",
                        resume_id=9,
                    )

        # 验证创建 agent 时传入了 user_id 和 user_llm_config
        MockInterviewAgent.assert_called_once_with(
            user_id=user_id,
            user_llm_config=mock_user_config,
            allow_mock_fallback=True,
        )
        # 验证返回的 provider 和 model 来自用户配置
        assert result["provider"] == "zhipu"
        assert result["model"] == "glm-4.5-air"

    @pytest.mark.asyncio
    async def test_create_question_set_serializes_questions(self):
        persisted = SimpleNamespace(id=1, user_id=55, title="题集")
        payload = InterviewQuestionSetCreate(
            title="后端题集",
            job_id=9,
            resume_id=7,
            questions=[
                {
                    "question_number": 1,
                    "question_text": "介绍 FastAPI 经验",
                    "question_type": "technical",
                    "difficulty": "medium",
                    "category": "backend",
                }
            ],
        )

        with patch("src.business_logic.interview.service.interview_question_set_repository") as mock_repo:
            mock_repo.create.return_value = persisted
            result = await self.service.create_question_set(self.mock_db, payload, current_user_id=55)

        assert result is persisted
        create_payload = mock_repo.create.call_args.args[1]
        assert create_payload["user_id"] == 55
        assert "questions_json" in create_payload
        assert "FastAPI" in create_payload["questions_json"]

    @pytest.mark.asyncio
    async def test_update_question_set_requires_owner(self):
        with patch.object(self.service, "get_question_set", new=AsyncMock(return_value=None)):
            result = await self.service.update_question_set(
                self.mock_db,
                question_set_id=1,
                question_set_data=InterviewQuestionSetUpdate(title="新题集"),
                current_user_id=55,
            )
        assert result is None

    @pytest.mark.asyncio
    async def test_start_coach_from_question_set_uses_bound_job_resume(self):
        question_set = SimpleNamespace(
            id=3,
            user_id=55,
            job_id=9,
            resume_id=7,
            questions_json='[{"question_number": 1}, {"question_number": 2}]',
        )

        with patch.object(self.service, "get_question_set", new=AsyncMock(return_value=question_set)):
            with patch("src.business_logic.interview.coach_service.coach_service") as mock_coach:
                mock_coach.start_session = AsyncMock(return_value={"session_id": 22, "total_questions": 2})

                result = await self.service.start_coach_from_question_set(
                    self.mock_db,
                    question_set_id=3,
                    current_user=SimpleNamespace(id=55),
                )

        assert result["session_id"] == 22
        mock_coach.start_session.assert_called_once_with(
            db=self.mock_db,
            user=SimpleNamespace(id=55),
            jd_id=9,
            resume_id=7,
            question_count=2,
        )
