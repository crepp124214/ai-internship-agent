"""Tracker business logic."""

from datetime import datetime
from typing import List, Optional

from sqlalchemy.orm import Session

from src.business_logic.agents.tracker_agent import (
    TrackerAgent,
    tracker_agent as default_tracker_agent,
)
from src.data_access.entities.job import Job as JobModel
from src.data_access.entities.job import JobApplication as JobApplicationModel
from src.data_access.entities.tracker import TrackerAdvice as TrackerAdviceModel
from src.data_access.repositories import resume_repository
from src.data_access.repositories.job_repository import job_repository
from src.data_access.repositories.tracker_advice_repository import tracker_advice_repository
from src.data_access.repositories.tracker_repository import tracker_repository
from src.presentation.schemas.tracker import ApplicationTrackerCreate, ApplicationTrackerUpdate


class TrackerService:
    def __init__(self, tracker_agent=None, tracker_agent_config=None):
        if tracker_agent is not None:
            self.tracker_agent = tracker_agent
        elif tracker_agent_config is not None:
            self.tracker_agent = TrackerAgent(
                config=tracker_agent_config,
                allow_mock_fallback=True,
            )
        else:
            self.tracker_agent = default_tracker_agent

    async def create_application(
        self,
        db: Session,
        application_data: ApplicationTrackerCreate,
        current_user_id: int,
    ) -> JobApplicationModel:
        try:
            return tracker_repository.create(
                db,
                {
                    "job_id": application_data.job_id,
                    "resume_id": application_data.resume_id,
                    "status": application_data.status,
                    "notes": application_data.notes,
                    "user_id": current_user_id,
                    "status_updated_at": datetime.now(),
                },
            )
        except Exception as exc:
            raise Exception(f"Create application failed: {exc}") from exc

    async def get_application(
        self, db: Session, application_id: int, current_user_id: int
    ) -> Optional[JobApplicationModel]:
        return tracker_repository.get_by_id_and_user_id(db, application_id, current_user_id)

    async def get_applications(
        self, db: Session, current_user_id: int
    ) -> List[JobApplicationModel]:
        return tracker_repository.get_by_user_id(db, current_user_id)

    async def update_application(
        self,
        db: Session,
        application_id: int,
        application_data: ApplicationTrackerUpdate,
        current_user_id: int,
    ) -> Optional[JobApplicationModel]:
        existing_application = await self.get_application(db, application_id, current_user_id)
        if not existing_application:
            return None

        update_data = application_data.model_dump(exclude_unset=True)
        if "status" in update_data and update_data["status"] != existing_application.status:
            update_data["status_updated_at"] = datetime.now()

        return tracker_repository.update_by_id_and_user_id(
            db, application_id, current_user_id, update_data
        )

    async def delete_application(self, db: Session, application_id: int, current_user_id: int) -> bool:
        return tracker_repository.delete_by_id_and_user_id(db, application_id, current_user_id)

    async def get_applications_by_status(
        self, db: Session, current_user_id: int, status: str
    ) -> List[JobApplicationModel]:
        return tracker_repository.get_by_user_id_and_status(db, current_user_id, status)

    @staticmethod
    def _build_application_context(application: JobApplicationModel) -> str:
        parts = [
            f"Application ID: {getattr(application, 'id', '')}",
            f"Job ID: {getattr(application, 'job_id', '')}",
            f"Resume ID: {getattr(application, 'resume_id', '')}",
            f"Status: {getattr(application, 'status', '') or ''}",
            f"Notes: {getattr(application, 'notes', '') or ''}",
            f"Applied At: {getattr(application, 'application_date', '') or ''}",
            f"Status Updated At: {getattr(application, 'status_updated_at', '') or ''}",
        ]
        return "\n".join(parts)

    @staticmethod
    def _build_job_context(job: JobModel) -> str:
        parts = [
            f"Title: {getattr(job, 'title', '') or ''}",
            f"Company: {getattr(job, 'company', '') or ''}",
            f"Location: {getattr(job, 'location', '') or ''}",
            f"Description: {getattr(job, 'description', '') or ''}",
            f"Requirements: {getattr(job, 'requirements', '') or ''}",
            f"Salary: {getattr(job, 'salary', '') or ''}",
            f"Work type: {getattr(job, 'work_type', '') or ''}",
            f"Experience: {getattr(job, 'experience', '') or ''}",
            f"Education: {getattr(job, 'education', '') or ''}",
            f"Welfare: {getattr(job, 'welfare', '') or ''}",
            f"Tags: {getattr(job, 'tags', '') or ''}",
            f"Source: {getattr(job, 'source', '') or ''}",
        ]
        return "\n".join(parts)

    @staticmethod
    def _resolve_resume_text(resume) -> str:
        processed_content = (getattr(resume, "processed_content", "") or "").strip()
        if processed_content:
            return processed_content
        resume_text = (getattr(resume, "resume_text", "") or "").strip()
        if resume_text:
            return resume_text
        raise ValueError("resume text is empty")

    def _get_tracker_provider(self) -> Optional[str]:
        config = getattr(self.tracker_agent, "config", {}) or {}
        provider = config.get("provider")
        return str(provider) if provider is not None else None

    def _get_tracker_model(self) -> Optional[str]:
        config = getattr(self.tracker_agent, "config", {}) or {}
        model = config.get("model")
        return str(model) if model is not None else None

    async def generate_application_advice(
        self,
        db: Session,
        application_id: int,
        current_user_id: int,
    ):
        application = await self.get_application(db, application_id, current_user_id)
        if not application:
            raise ValueError("application not found")

        job = job_repository.get_by_id(db, application.job_id)
        resume = resume_repository.get_by_id_and_user_id(db, application.resume_id, current_user_id)
        if not job or not resume:
            raise ValueError("required context is missing")

        application_context = self._build_application_context(application)
        job_context = self._build_job_context(job)
        resume_context = self._resolve_resume_text(resume)

        try:
            result = await self.tracker_agent.advise_next_steps(
                application_context=application_context,
                job_context=job_context,
                resume_context=resume_context,
            )
        except Exception as exc:  # pragma: no cover
            raise RuntimeError("failed to generate tracker advice") from exc

        return {
            "mode": result.get("mode", "tracker_advice"),
            "application_id": application_id,
            "summary": result["summary"],
            "next_steps": result["next_steps"],
            "risks": result["risks"],
            "raw_content": result.get("raw_content", ""),
            "provider": self._get_tracker_provider(),
            "model": self._get_tracker_model(),
        }

    async def generate_tracker_advice_preview(
        self,
        db: Session,
        application_id: int,
        current_user_id: int,
    ):
        return await self.generate_application_advice(
            db,
            application_id,
            current_user_id,
        )

    async def persist_application_advice(
        self,
        db: Session,
        application_id: int,
        current_user_id: int,
    ) -> TrackerAdviceModel:
        application = await self.get_application(db, application_id, current_user_id)
        if not application:
            raise ValueError("application not found")

        result = await self.generate_application_advice(db, application_id, current_user_id)
        return tracker_advice_repository.create(
            db,
            {
                "application_id": application_id,
                "mode": result.get("mode", "tracker_advice"),
                "summary": result["summary"],
                "next_steps": result["next_steps"],
                "risks": result["risks"],
                "raw_content": result.get("raw_content", ""),
                "provider": result.get("provider"),
                "model": result.get("model"),
            },
        )

    async def get_application_advice_history(
        self,
        db: Session,
        application_id: int,
        current_user_id: int,
    ) -> List[TrackerAdviceModel]:
        application = await self.get_application(db, application_id, current_user_id)
        if not application:
            raise ValueError("application not found")
        return tracker_advice_repository.get_all_by_application_id_and_user_id(
            db,
            application_id,
            current_user_id,
        )

    async def get_tracker_advice_history(
        self,
        db: Session,
        application_id: int,
        current_user_id: int,
    ) -> List[TrackerAdviceModel]:
        return await self.get_application_advice_history(
            db,
            application_id,
            current_user_id,
        )


tracker_service = TrackerService()
