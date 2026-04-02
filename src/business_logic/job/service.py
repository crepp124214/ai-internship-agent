"""Job service - handles job-related business logic."""

from __future__ import annotations

from datetime import datetime
from typing import List, Optional

from sqlalchemy.orm import Session

from src.business_logic.agents.job_agent import (
    JobAgent,
    job_agent as default_job_agent,
)
from src.data_access.entities.job import Job as JobModel
from src.data_access.entities.job import JobMatchResult as JobMatchResultModel
from src.data_access.repositories import resume_repository
from src.data_access.repositories.job_match_result_repository import (
    job_match_result_repository,
)
from src.data_access.repositories.job_repository import job_repository
from src.presentation.schemas.job import JobCreate, JobUpdate


class JobService:
    """Job service class."""

    def __init__(self, job_agent=None, job_agent_config=None):
        if job_agent is not None:
            self.job_agent = job_agent
        elif job_agent_config is not None:
            self.job_agent = JobAgent(
                config=job_agent_config,
                allow_mock_fallback=True,
            )
        else:
            self.job_agent = default_job_agent

    async def create_job(self, db: Session, job_data: JobCreate) -> JobModel:
        try:
            return job_repository.create(
                db,
                {
                    "title": job_data.title,
                    "company": job_data.company,
                    "location": job_data.location,
                    "description": job_data.description,
                    "requirements": job_data.requirements,
                    "salary": job_data.salary,
                    "work_type": job_data.work_type,
                    "experience": job_data.experience,
                    "education": job_data.education,
                    "welfare": job_data.welfare,
                    "tags": job_data.tags,
                    "source": job_data.source,
                    "source_url": job_data.source_url,
                    "source_id": job_data.source_id,
                    "is_active": True,
                },
            )
        except Exception as e:
            raise Exception(f"Create job failed: {str(e)}")

    async def get_job(self, db: Session, job_id: int) -> Optional[JobModel]:
        return job_repository.get_by_id(db, job_id)

    async def get_jobs(self, db: Session) -> List[JobModel]:
        return job_repository.get_all(db)

    async def update_job(
        self, db: Session, job_id: int, job_data: JobUpdate
    ) -> Optional[JobModel]:
        return job_repository.update(db, job_id, job_data.model_dump(exclude_unset=True))

    async def delete_job(self, db: Session, job_id: int) -> bool:
        return job_repository.delete(db, job_id)

    async def search_jobs(
        self, db: Session, keyword: str = None, location: str = None
    ) -> List[JobModel]:
        jobs = job_repository.get_all(db)

        normalized_keyword = keyword.strip().lower() if keyword else None
        normalized_location = location.strip().lower() if location else None

        if not normalized_keyword and not normalized_location:
            return jobs

        def matches(job: JobModel) -> bool:
            if normalized_keyword:
                searchable_fields = [
                    job.title,
                    job.company,
                    job.location,
                    job.description,
                    job.requirements,
                    job.tags,
                ]
                if not any(
                    field and normalized_keyword in field.lower()
                    for field in searchable_fields
                ):
                    return False

            if normalized_location and (
                not job.location or normalized_location not in job.location.lower()
            ):
                return False

            return True

        return [job for job in jobs if matches(job)]

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
            f"Source URL: {getattr(job, 'source_url', '') or ''}",
            f"Source ID: {getattr(job, 'source_id', '') or ''}",
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

    def _get_job_provider(self) -> Optional[str]:
        config = getattr(self.job_agent, "config", {}) or {}
        provider = config.get("provider")
        return str(provider) if provider is not None else None

    def _get_job_model(self) -> Optional[str]:
        config = getattr(self.job_agent, "config", {}) or {}
        model = config.get("model")
        return str(model) if model is not None else None

    async def match_job_to_resume(
        self,
        db: Session,
        job_id: int,
        resume_id: int,
        current_user_id: int,
    ):
        job = job_repository.get_by_id(db, job_id)
        if job is None:
            raise ValueError("job not found")

        resume = resume_repository.get_by_id_and_user_id(db, resume_id, current_user_id)
        if resume is None:
            raise ValueError("resume not found")

        job_context = self._build_job_context(job)
        resume_context = self._resolve_resume_text(resume)
        result = await self.job_agent.match_job_to_resume(
            job_context=job_context,
            resume_context=resume_context,
        )

        return {
            "mode": result.get("mode", "job_match"),
            "job_id": job_id,
            "resume_id": resume_id,
            "score": result["score"],
            "feedback": result["feedback"],
            "raw_content": result.get("raw_content", ""),
            "provider": self._get_job_provider() or "mock",
            "model": self._get_job_model() or "unknown-model",
            "matched_at": datetime.now(),
        }

    async def generate_job_match_preview(
        self,
        db: Session,
        job_id: int,
        resume_id: int,
        current_user_id: int,
    ):
        return await self.match_job_to_resume(
            db,
            job_id=job_id,
            resume_id=resume_id,
            current_user_id=current_user_id,
        )

    async def persist_job_match(
        self,
        db: Session,
        job_id: int,
        resume_id: int,
        current_user_id: int,
    ) -> JobMatchResultModel:
        result = await self.match_job_to_resume(
            db,
            job_id=job_id,
            resume_id=resume_id,
            current_user_id=current_user_id,
        )

        return job_match_result_repository.create(
            db,
            {
                "job_id": job_id,
                "resume_id": resume_id,
                "mode": result.get("mode", "job_match"),
                "score": result["score"],
                "feedback": result["feedback"],
                "raw_content": result.get("raw_content", ""),
                "provider": result.get("provider") or self._get_job_provider() or "mock",
                "model": result.get("model") or self._get_job_model() or "unknown-model",
            },
        )

    async def get_job_match_history(
        self,
        db: Session,
        job_id: int,
        current_user_id: int,
    ) -> List[JobMatchResultModel]:
        job = await self.get_job(db, job_id)
        if job is None:
            raise ValueError("job not found")
        return job_match_result_repository.get_all_by_job_id_and_user_id(
            db,
            job_id,
            current_user_id,
        )


job_service = JobService()
