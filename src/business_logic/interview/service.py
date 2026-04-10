"""Interview service - handles interview-related business logic."""

from datetime import datetime
import random
from typing import List, Optional

from sqlalchemy.orm import Session

from src.business_logic.agents.interview_agent import (
    InterviewAgent,
    interview_agent as default_interview_agent,
)
from src.data_access.entities.interview import (
    InterviewQuestion as InterviewQuestionModel,
    InterviewRecord as InterviewRecordModel,
    InterviewSession as InterviewSessionModel,
)
from src.data_access.repositories import resume_repository
from src.data_access.repositories.interview_repository import (
    interview_question_repository,
    interview_record_repository,
    interview_session_repository,
)
from src.presentation.schemas.interview import (
    InterviewQuestionCreate,
    InterviewQuestionUpdate,
    InterviewRecordCreate,
    InterviewRecordUpdate,
    InterviewSessionCreate,
    InterviewSessionUpdate,
)


class InterviewService:
    """Business logic for interview features."""

    def __init__(self, interview_agent=None, interview_agent_config=None):
        if interview_agent is not None:
            self.interview_agent = interview_agent
        elif interview_agent_config is not None:
            self.interview_agent = InterviewAgent(
                config=interview_agent_config,
                allow_mock_fallback=True,
            )
        else:
            self.interview_agent = default_interview_agent

    def _get_interview_provider(self) -> str:
        config = getattr(self.interview_agent, "config", {}) or {}
        provider = config.get("provider")
        return str(provider) if provider is not None else "unknown-provider"

    def _get_interview_model(self) -> str:
        config = getattr(self.interview_agent, "config", {}) or {}
        model = config.get("model")
        return str(model) if model is not None else "unknown-model"

    async def create_question(
        self, db: Session, question_data: InterviewQuestionCreate
    ) -> InterviewQuestionModel:
        try:
            return interview_question_repository.create(
                db,
                {
                    "question_type": question_data.question_type,
                    "difficulty": question_data.difficulty,
                    "question_text": question_data.question_text,
                    "category": question_data.category,
                    "tags": question_data.tags,
                    "sample_answer": question_data.sample_answer,
                    "reference_material": question_data.reference_material,
                },
            )
        except Exception as e:
            raise Exception(f"创建面试问题失败: {str(e)}")

    async def get_question(
        self, db: Session, question_id: int
    ) -> Optional[InterviewQuestionModel]:
        return interview_question_repository.get_by_id(db, question_id)

    async def get_questions(self, db: Session) -> List[InterviewQuestionModel]:
        return interview_question_repository.get_all(db)

    async def update_question(
        self, db: Session, question_id: int, question_data: InterviewQuestionUpdate
    ) -> Optional[InterviewQuestionModel]:
        return interview_question_repository.update(
            db, question_id, question_data.model_dump(exclude_unset=True)
        )

    async def delete_question(self, db: Session, question_id: int) -> bool:
        return interview_question_repository.delete(db, question_id)

    async def get_questions_by_category(
        self, db: Session, category: str
    ) -> List[InterviewQuestionModel]:
        return interview_question_repository.get_by_field(db, "category", category)

    async def get_random_questions(
        self, db: Session, count: int = 5
    ) -> List[InterviewQuestionModel]:
        all_questions = interview_question_repository.get_all(db)
        if count <= 0 or not all_questions:
            return []
        if len(all_questions) <= count:
            return all_questions
        return random.sample(all_questions, count)

    async def create_session(
        self, db: Session, session_data: InterviewSessionCreate, current_user_id: int
    ) -> InterviewSessionModel:
        payload = session_data.model_dump()
        payload["user_id"] = current_user_id
        return interview_session_repository.create(db, payload)

    async def get_sessions(
        self, db: Session, current_user_id: int
    ) -> List[InterviewSessionModel]:
        return interview_session_repository.get_by_field(db, "user_id", current_user_id)

    async def create_record(
        self, db: Session, record_data: InterviewRecordCreate, current_user_id: int
    ) -> InterviewRecordModel:
        payload = record_data.model_dump(exclude_none=True)
        payload["user_id"] = current_user_id
        return interview_record_repository.create(db, payload)

    async def get_records(
        self, db: Session, current_user_id: int
    ) -> List[InterviewRecordModel]:
        return interview_record_repository.get_by_field(db, "user_id", current_user_id)

    async def update_record(
        self, db: Session, record_id: int, record_data: InterviewRecordUpdate
    ) -> Optional[InterviewRecordModel]:
        return interview_record_repository.update(
            db, record_id, record_data.model_dump(exclude_unset=True)
        )

    async def update_session(
        self, db: Session, session_id: int, session_data: InterviewSessionUpdate
    ) -> Optional[InterviewSessionModel]:
        return interview_session_repository.update(
            db, session_id, session_data.model_dump(exclude_unset=True)
        )

    @staticmethod
    def _resolve_resume_text(resume) -> str:
        processed_content = (getattr(resume, "processed_content", "") or "").strip()
        if processed_content:
            return processed_content
        resume_text = (getattr(resume, "resume_text", "") or "").strip()
        if resume_text:
            return resume_text
        raise ValueError("resume text is empty")

    async def generate_questions_for_job(
        self,
        db: Session,
        current_user_id: int,
        job_context: str,
        resume_id: Optional[int] = None,
        count: int = 5,
    ):
        resume_context = None
        if resume_id is not None:
            resume = resume_repository.get_by_id_and_user_id(db, resume_id, current_user_id)
            if resume is None:
                raise ValueError("resume not found")
            resume_context = self._resolve_resume_text(resume)
        # 从 service 层获取用户 LLM 配置（db 在 async 上下文中，可安全访问）
        # 不在 agent 构造函数中同步 SessionLocal()，避免阻塞 event loop
        from src.business_logic.user_llm_config_service import user_llm_config_service
        user_llm_config = user_llm_config_service.get_config_for_agent(db, current_user_id, "interview_agent")

        user_agent = InterviewAgent(
            user_id=current_user_id,
            user_llm_config=user_llm_config,
            allow_mock_fallback=True,
        )
        return await user_agent.generate_interview_questions(
            job_context=job_context,
            resume_context=resume_context,
            count=count,
        )

    async def generate_interview_questions_preview(
        self,
        db: Session,
        current_user_id: int,
        job_context: str,
        resume_id: Optional[int] = None,
        count: int = 5,
    ):
        return await self.generate_questions_for_job(
            db,
            current_user_id=current_user_id,
            job_context=job_context,
            resume_id=resume_id,
            count=count,
        )

    async def evaluate_answer(
        self,
        question_text: str,
        user_answer: str,
        job_context: Optional[str] = None,
    ):
        return await self.interview_agent.evaluate_interview_answer(
            question_text=question_text,
            user_answer=user_answer,
            job_context=job_context,
        )

    async def evaluate_interview_answer_preview(
        self,
        question_text: str,
        user_answer: str,
        job_context: Optional[str] = None,
    ):
        return await self.evaluate_answer(
            question_text=question_text,
            user_answer=user_answer,
            job_context=job_context,
        )

    async def evaluate_record_answer(
        self,
        db: Session,
        record_id: int,
        current_user_id: int,
        job_context: Optional[str] = None,
    ):
        record = interview_record_repository.get_by_id(db, record_id)
        if record is None or getattr(record, "user_id", None) != current_user_id:
            raise ValueError("interview record not found")

        question_id = getattr(record, "question_id", None)
        user_answer = (getattr(record, "user_answer", "") or "").strip()
        if question_id is None or not user_answer:
            raise ValueError("interview record is missing required evaluation input")

        question = interview_question_repository.get_by_id(db, question_id)
        if question is None:
            raise ValueError("interview question not found")

        evaluation = await self.interview_agent.evaluate_interview_answer(
            question_text=question.question_text,
            user_answer=user_answer,
            job_context=job_context,
        )

        payload = {
            "score": evaluation["score"],
            "feedback": evaluation["feedback"],
            "ai_evaluation": evaluation["raw_content"],
            "provider": evaluation.get("provider") or self._get_interview_provider(),
            "model": evaluation.get("model") or self._get_interview_model(),
            "status": evaluation.get("status", "success"),
            "fallback_used": evaluation.get("fallback_used", False),
            "answered_at": getattr(record, "answered_at", None) or datetime.now(),
        }
        return interview_record_repository.update(db, record_id, payload)

    async def persist_interview_record_evaluation(
        self,
        db: Session,
        record_id: int,
        current_user_id: int,
        job_context: Optional[str] = None,
    ):
        return await self.evaluate_record_answer(
            db,
            record_id=record_id,
            current_user_id=current_user_id,
            job_context=job_context,
        )


interview_service = InterviewService()
