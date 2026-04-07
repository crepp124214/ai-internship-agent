import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from src.business_logic.interview.session_manager import InterviewSessionManager, CoachSessionState, AnswerRecord


class TestInterviewSessionManager:
    def setup_method(self):
        self.mock_agent = AsyncMock()
        self.manager = InterviewSessionManager(interview_agent=self.mock_agent)

    @pytest.mark.asyncio
    async def test_submit_answer_returns_score_and_next(self):
        mock_db = MagicMock()
        mock_user = MagicMock()
        mock_user.id = 1

        # Set up in-memory session state
        state = CoachSessionState(
            session_id=1,
            user_id=1,
            resume_id=10,
            jd_text="Python 后端开发",
            question_count=5,
            current_index=0,
            followup_done=False,
            opening_message="你好，我是面试官",
            questions=[
                "请做自我介绍",
                "描述你的项目经验",
            ],
        )
        self.manager._sessions[1] = state

        # Mock agent scoring
        self.mock_agent.evaluate_single_answer = AsyncMock(return_value={
            "score": 75,
            "feedback": "回答基本准确，可以更具体。",
        })

        result = await self.manager.submit_answer(
            db=mock_db,
            user=mock_user,
            session_id=1,
            answer="我使用 FastAPI 做了电商后端项目。",
        )

        assert result["score"] == 75
        assert "feedback" in result
        assert result["is_followup"] is False

    @pytest.mark.asyncio
    async def test_submit_answer_raises_when_session_completed(self):
        """Test that submitting answer to completed session raises error"""
        mock_db = MagicMock()
        mock_user = MagicMock()
        mock_user.id = 1

        # Set up completed session state
        state = CoachSessionState(
            session_id=1,
            user_id=1,
            resume_id=10,
            jd_text="Python 后端开发",
            question_count=5,
            current_index=5,
            followup_done=True,  # Already completed
            opening_message="你好",
            questions=["Q1", "Q2"],
        )
        self.manager._sessions[1] = state

        with pytest.raises(ValueError, match="面试已结束"):
            await self.manager.submit_answer(
                db=mock_db,
                user=mock_user,
                session_id=1,
                answer="晚了",
            )

    def test_end_session_returns_review_report(self):
        """Test ending session returns review report"""
        mock_db = MagicMock()
        mock_user = MagicMock()
        mock_user.id = 1

        # Set up session with answers
        state = CoachSessionState(
            session_id=1,
            user_id=1,
            resume_id=10,
            jd_text="Python 后端开发",
            question_count=3,
            current_index=3,
            followup_done=True,
            opening_message="你好",
            questions=["Q1", "Q2", "Q3"],
            answers=[
                AnswerRecord(question="Q1", answer="A1", score=80, is_followup=False),
                AnswerRecord(question="Q2", answer="A2", score=75, is_followup=False),
            ],
        )
        self.manager._sessions[1] = state

        # Mock InterviewSession query
        mock_session = MagicMock()
        mock_session.status = "completed"
        mock_session.completed = True
        mock_session.average_score = 77.5
        mock_db.query.return_value.filter_by.return_value.first.return_value = mock_session

        result = self.manager.end_session(
            db=mock_db,
            user=mock_user,
            session_id=1,
            followup_skipped=False,
        )

        assert result["session_id"] == 1
        assert "review_report" in result
        assert result["average_score"] == 77.5

    def test_generate_opening_and_questions_falls_back_without_agent(self):
        """Test fallback when no agent is provided"""
        manager = InterviewSessionManager(interview_agent=None)
        opening, questions = manager._generate_opening_and_questions(
            job_title="Python后端",
            jd_text="熟悉FastAPI",
            count=3,
        )

        assert opening == "你好，我是 Python后端 的面试官，我会对你的技术能力进行考察。"
        assert len(questions) == 3

    @pytest.mark.asyncio
    async def test_score_answer_falls_back_without_agent(self):
        """Test fallback scoring when no agent is provided"""
        manager = InterviewSessionManager(interview_agent=None)
        result = await manager._score_answer(
            question="描述你的项目",
            answer="我做了一个电商网站",
            jd_text="Python后端",
        )

        assert "score" in result
        assert "feedback" in result
        assert result["feedback"] == "评分暂不可用"

    @pytest.mark.asyncio
    async def test_submit_answer_raises_when_not_found(self):
        """Test that submitting answer to non-existent session raises error"""
        mock_db = MagicMock()
        mock_user = MagicMock()
        mock_user.id = 1

        with pytest.raises(ValueError, match="Session not found"):
            await self.manager.submit_answer(
                db=mock_db,
                user=mock_user,
                session_id=999,
                answer="test",
            )

    @pytest.mark.asyncio
    async def test_submit_answer_raises_when_unauthorized(self):
        """Test that submitting answer for different user raises error"""
        mock_db = MagicMock()
        mock_user = MagicMock()
        mock_user.id = 2  # Different user

        # Set up session for user 1
        state = CoachSessionState(
            session_id=1,
            user_id=1,
            resume_id=10,
            jd_text="Python 后端开发",
            question_count=5,
            current_index=0,
            followup_done=False,
            opening_message="你好",
            questions=["Q1", "Q2"],
        )
        self.manager._sessions[1] = state

        with pytest.raises(ValueError, match="Unauthorized"):
            await self.manager.submit_answer(
                db=mock_db,
                user=mock_user,
                session_id=1,
                answer="test",
            )

    def test_end_session_raises_when_not_found(self):
        """Test that ending non-existent session raises error"""
        mock_db = MagicMock()
        mock_user = MagicMock()
        mock_user.id = 1

        with pytest.raises(ValueError, match="Session or unauthorized"):
            self.manager.end_session(
                db=mock_db,
                user=mock_user,
                session_id=999,
                followup_skipped=False,
            )