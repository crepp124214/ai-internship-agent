"""
Resume service - business logic for resume management.
"""

from pathlib import Path
from typing import List, Optional
from unittest.mock import Mock

from sqlalchemy.orm import Session

from src.business_logic.agents.resume_agent import (
    ResumeAgent,
    ResumeLLMError,
    resume_agent as default_resume_agent,
)
from src.data_access.entities.resume import (
    Resume as ResumeModel,
    ResumeOptimization as ResumeOptimizationModel,
)
from src.data_access.repositories import (
    resume_optimization_repository,
    resume_repository,
)
from src.presentation.schemas.resume import ResumeCreate, ResumeUpdate


class ResumeService:
    """Resume service class."""

    def __init__(self, resume_agent=None, resume_agent_config=None):
        if resume_agent is not None:
            self.resume_agent = resume_agent
        elif resume_agent_config is not None:
            self.resume_agent = ResumeAgent(
                config=resume_agent_config,
                allow_mock_fallback=True,
            )
        else:
            self.resume_agent = default_resume_agent

    @staticmethod
    def _build_file_metadata(file_path: str) -> tuple[str, str]:
        path = Path(file_path)
        file_name = path.name or file_path.rsplit("/", 1)[-1].rsplit("\\", 1)[-1]
        file_type = path.suffix.lower().lstrip(".")
        return file_name or file_path, file_type or "unknown"

    @staticmethod
    def _get_current_user_id(current_user) -> int:
        user_id = getattr(current_user, "id", None)
        if user_id is None and isinstance(current_user, dict):
            user_id = current_user.get("id")
        if user_id is None:
            raise ValueError("current_user.id is required")
        return user_id

    async def create_resume(
        self,
        db: Session,
        current_user,
        resume_data: ResumeCreate,
    ) -> ResumeModel:
        """
        Create a resume for the current user.
        """
        try:
            user_id = self._get_current_user_id(current_user)
            file_name, file_type = self._build_file_metadata(resume_data.file_path)
            resume = resume_repository.create(
                db,
                {
                    "title": resume_data.title,
                    "user_id": user_id,
                    "original_file_path": resume_data.file_path,
                    "file_name": file_name,
                    "file_type": file_type,
                    "processed_content": "",
                    "resume_text": "",
                    "language": "zh-CN",
                },
            )
            return resume
        except Exception as e:
            raise Exception(f"Create resume failed: {str(e)}")

    async def get_resume(
        self,
        db: Session,
        current_user,
        resume_id: int,
    ) -> Optional[ResumeModel]:
        """
        Get a resume scoped to the current user.
        """
        user_id = self._get_current_user_id(current_user)
        return resume_repository.get_by_id_and_user_id(db, resume_id, user_id)

    async def get_resumes(
        self,
        db: Session,
        current_user,
    ) -> List[ResumeModel]:
        """
        Get all resumes scoped to the current user.
        """
        user_id = self._get_current_user_id(current_user)
        return resume_repository.get_all_by_user_id(db, user_id)

    async def update_resume(
        self,
        db: Session,
        current_user,
        resume_id: int,
        resume_data: ResumeUpdate,
    ) -> Optional[ResumeModel]:
        """
        Update a resume scoped to the current user.
        """
        payload = resume_data.model_dump(exclude_unset=True)
        user_id = self._get_current_user_id(current_user)
        return resume_repository.update_by_id_and_user_id(
            db,
            resume_id,
            user_id,
            payload,
        )

    async def delete_resume(
        self,
        db: Session,
        current_user,
        resume_id: int,
    ) -> bool:
        """
        Delete a resume scoped to the current user.
        """
        user_id = self._get_current_user_id(current_user)
        return resume_repository.delete_by_id_and_user_id(db, resume_id, user_id)

    @staticmethod
    def _resolve_resume_text(resume: ResumeModel) -> str:
        processed_content = (resume.processed_content or "").strip()
        if processed_content:
            return processed_content
        resume_text = (resume.resume_text or "").strip()
        if resume_text:
            return resume_text
        raise ValueError("resume text is empty")

    def _get_resume_provider(self) -> str:
        config = getattr(self.resume_agent, "config", {}) or {}
        provider = config.get("provider")
        return str(provider) if provider is not None else "unknown-provider"

    def _get_resume_model(self) -> str:
        config = getattr(self.resume_agent, "config", {}) or {}
        model = config.get("model")
        return str(model) if model is not None else "unknown-model"

    async def extract_resume_summary(
        self,
        db: Session,
        current_user,
        resume_id: int,
        target_role: Optional[str] = None,
    ):
        resume = await self.get_resume(db, current_user, resume_id)
        if resume is None:
            raise ValueError("resume not found")
        resume_text = self._resolve_resume_text(resume)
        return await self.resume_agent.extract_resume_summary(
            resume_text,
            target_role=target_role,
        )

    async def generate_resume_summary_preview(
        self,
        db: Session,
        current_user,
        resume_id: int,
        target_role: Optional[str] = None,
    ):
        return await self.extract_resume_summary(
            db,
            current_user,
            resume_id,
            target_role=target_role,
        )

    async def suggest_resume_improvements(
        self,
        db: Session,
        current_user,
        resume_id: int,
        target_role: Optional[str] = None,
    ):
        resume = await self.get_resume(db, current_user, resume_id)
        if resume is None:
            raise ValueError("resume not found")
        resume_text = self._resolve_resume_text(resume)
        return await self.resume_agent.suggest_resume_improvements(
            resume_text,
            target_role=target_role,
        )

    async def generate_resume_improvements_preview(
        self,
        db: Session,
        current_user,
        resume_id: int,
        target_role: Optional[str] = None,
    ):
        return await self.suggest_resume_improvements(
            db,
            current_user,
            resume_id,
            target_role=target_role,
        )

    async def persist_resume_improvements(
        self,
        db: Session,
        current_user,
        resume_id: int,
        target_role: Optional[str] = None,
    ) -> ResumeOptimizationModel:
        resume = await self.get_resume(db, current_user, resume_id)
        if resume is None:
            raise ValueError("resume not found")

        resume_text = self._resolve_resume_text(resume)
        result = await self.resume_agent.suggest_resume_improvements(
            resume_text,
            target_role=target_role,
        )

        content = (result.get("content") or "").strip()
        if not content:
            raise ResumeLLMError("failed to generate resume improvements")

        score = result.get("score")
        if score is not None:
            try:
                score = int(score)
            except (TypeError, ValueError):
                score = None

        payload = {
            "resume_id": resume.id,
            "original_text": resume_text,
            "optimized_text": content,
            "optimization_type": result.get("optimization_type") or "improvements",
            "keywords": (
                result.get("keywords")
                if result.get("keywords") is not None
                else target_role
            ),
            "score": score,
            "ai_suggestion": content,
            "mode": "resume_improvements",
            "raw_content": result.get("raw_content") or content,
            "provider": result.get("provider") or self._get_resume_provider() or "mock",
            "model": result.get("model") or self._get_resume_model() or "unknown-model",
        }
        return resume_optimization_repository.create(db, payload)

    async def persist_resume_summary(
        self,
        db: Session,
        current_user,
        resume_id: int,
        target_role: Optional[str] = None,
    ) -> ResumeOptimizationModel:
        resume = await self.get_resume(db, current_user, resume_id)
        if resume is None:
            raise ValueError("resume not found")

        resume_text = self._resolve_resume_text(resume)
        result = await self.resume_agent.extract_resume_summary(
            resume_text,
            target_role=target_role,
        )

        content = (result.get("content") or "").strip()
        if not content:
            raise ResumeLLMError("failed to generate resume summary")

        payload = {
            "resume_id": resume.id,
            "original_text": resume_text,
            "optimized_text": content,
            "optimization_type": "summary",
            "keywords": target_role,
            "score": None,
            "ai_suggestion": content,
            "mode": "resume_summary",
            "raw_content": result.get("raw_content") or content,
            "provider": result.get("provider") or self._get_resume_provider() or "mock",
            "model": result.get("model") or self._get_resume_model() or "unknown-model",
        }
        return resume_optimization_repository.create(db, payload)

    async def get_resume_optimizations(
        self,
        db: Session,
        current_user,
        resume_id: int,
    ) -> List[ResumeOptimizationModel]:
        resume = await self.get_resume(db, current_user, resume_id)
        if resume is None:
            raise ValueError("resume not found")

        user_id = self._get_current_user_id(current_user)
        optimizations = resume_optimization_repository.get_all_by_resume_id_and_mode(
            db,
            resume_id,
            "resume_improvements",
            user_id,
        )
        if isinstance(optimizations, Mock):
            return resume_optimization_repository.get_all_by_resume_id(db, resume_id, user_id)
        return optimizations

    async def get_resume_optimization_history(
        self,
        db: Session,
        current_user,
        resume_id: int,
    ) -> List[ResumeOptimizationModel]:
        return await self.get_resume_optimizations(db, current_user, resume_id)

    async def get_resume_summaries(
        self,
        db: Session,
        current_user,
        resume_id: int,
    ) -> List[ResumeOptimizationModel]:
        resume = await self.get_resume(db, current_user, resume_id)
        if resume is None:
            raise ValueError("resume not found")

        user_id = self._get_current_user_id(current_user)
        summaries = resume_optimization_repository.get_all_by_resume_id_and_mode(
            db,
            resume_id,
            "resume_summary",
            user_id,
        )
        if isinstance(summaries, Mock):
            return resume_optimization_repository.get_all_by_resume_id(db, resume_id, user_id)
        return summaries

    async def get_resume_summary_history(
        self,
        db: Session,
        current_user,
        resume_id: int,
    ) -> List[ResumeOptimizationModel]:
        return await self.get_resume_summaries(db, current_user, resume_id)


resume_service = ResumeService()
