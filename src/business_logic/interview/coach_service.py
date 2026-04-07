from src.business_logic.interview.interview_coach_agent import InterviewCoachAgent
from src.business_logic.interview.session_manager import InterviewSessionManager
from src.business_logic.interview.review_report_generator import ReviewReportGenerator


class CoachService:
    """面试对练服务"""

    def __init__(self):
        self._session_manager: dict[int, InterviewSessionManager] = {}

    def _get_manager(self, user_id: int) -> InterviewSessionManager:
        if user_id not in self._session_manager:
            from src.core.llm.litellm_adapter import LiteLLMAdapter
            llm = LiteLLMAdapter()
            coach_agent = InterviewCoachAgent(llm=llm)
            manager = InterviewSessionManager(
                interview_agent=coach_agent,
                review_report_generator=ReviewReportGenerator(),
            )
            self._session_manager[user_id] = manager
        return self._session_manager[user_id]

    def start_session(
        self, db, user, jd_id: int, resume_id: int, question_count: int = 5
    ):
        manager = self._get_manager(user.id)
        return manager.start(db, user, jd_id, resume_id, question_count)

    def submit_answer(self, db, user, session_id: int, answer: str):
        manager = self._get_manager(user.id)
        return manager.submit_answer(db, user, session_id, answer)

    def submit_followup_answers(self, db, user, session_id: int, followup_answers: list[dict]):
        manager = self._get_manager(user.id)
        return manager.submit_followup_answers(db, user, session_id, followup_answers)

    def end_session(self, db, user, session_id: int, followup_skipped: bool = False):
        manager = self._get_manager(user.id)
        return manager.end_session(db, user, session_id, followup_skipped)


coach_service = CoachService()