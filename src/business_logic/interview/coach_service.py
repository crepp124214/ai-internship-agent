from sqlalchemy.orm import Session
import inspect

from src.business_logic.interview.interview_coach_agent import InterviewCoachAgent
from src.business_logic.interview.session_manager import InterviewSessionManager
from src.business_logic.interview.review_report_generator import ReviewReportGenerator
from src.business_logic.user_llm_config_service import user_llm_config_service


class CoachService:
    """面试对练服务"""

    def __init__(self):
        self._session_manager: dict[int, InterviewSessionManager] = {}

    def _get_manager(self, db: Session, user_id: int) -> InterviewSessionManager:
        if user_id not in self._session_manager:
            # 尝试加载用户 LLM 配置
            user_config = user_llm_config_service.get_config_for_agent(db, user_id, "interview_agent")
            from src.core.llm.litellm_adapter import LiteLLMAdapter
            if user_config:
                llm = LiteLLMAdapter(
                    model=user_config.get("model", "gpt-4o-mini"),
                    api_key=user_config.get("api_key"),
                    base_url=user_config.get("base_url"),
                    temperature=user_config.get("temperature", 0.7),
                )
            else:
                llm = LiteLLMAdapter()
            coach_agent = InterviewCoachAgent(llm=llm)
            manager = InterviewSessionManager(
                interview_agent=coach_agent,
                review_report_generator=ReviewReportGenerator(),
            )
            self._session_manager[user_id] = manager
        return self._session_manager[user_id]

    def start_session(
        self, db: Session, user, jd_id: int, resume_id: int, question_count: int = 5
    ):
        manager = self._get_manager(db, user.id)
        return manager.start(db, user, jd_id, resume_id, question_count)

    def submit_answer(self, db: Session, user, session_id: int, answer: str):
        """Submit answer - handles both sync and async manager methods for compatibility."""
        manager = self._get_manager(db, user.id)
        result = manager.submit_answer(db, user, session_id, answer)
        # If result is a coroutine (async method), we need to handle it
        if inspect.iscoroutine(result):
            # This shouldn't happen with the current sync implementation,
            # but kept for future compatibility
            raise RuntimeError("Async submit_answer not supported in sync context")
        return result

    def submit_followup_answers(self, db: Session, user, session_id: int, followup_answers: list[dict]):
        """Submit followup answers - handles both sync and async manager methods."""
        manager = self._get_manager(db, user.id)
        result = manager.submit_followup_answers(db, user, session_id, followup_answers)
        if inspect.iscoroutine(result):
            raise RuntimeError("Async submit_followup_answers not supported in sync context")
        return result

    def end_session(self, db: Session, user, session_id: int, followup_skipped: bool = False):
        manager = self._get_manager(db, user.id)
        return manager.end_session(db, user, session_id, followup_skipped)


coach_service = CoachService()