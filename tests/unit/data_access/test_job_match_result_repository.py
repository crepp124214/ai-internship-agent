"""Job match result repository tests."""

from datetime import datetime, timedelta

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.data_access.database import Base
from src.data_access.entities.job import JobMatchResult
from src.data_access.repositories.job_match_result_repository import (
    job_match_result_repository,
)
from src.data_access.repositories.job_repository import job_repository
from src.data_access.repositories.resume_repository import resume_repository
from src.data_access.repositories.user_repository import user_repository


class TestJobMatchResultRepository:
    def setup_method(self):
        self.engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(bind=self.engine)
        self.SessionLocal = sessionmaker(bind=self.engine)

    def teardown_method(self):
        Base.metadata.drop_all(bind=self.engine)

    def _seed_user_resume(self, db, username: str, email: str):
        user = user_repository.create(
            db,
            {
                "username": username,
                "email": email,
                "password_hash": "hashed-password",
                "name": username,
            },
        )
        resume = resume_repository.create(
            db,
            {
                "title": f"{username}-resume",
                "user_id": user.id,
                "original_file_path": "/tmp/resume.pdf",
                "file_name": "resume.pdf",
                "file_type": "pdf",
                "processed_content": "Resume text",
                "resume_text": "Resume text",
                "language": "en-US",
            },
        )
        return user, resume

    def _seed_job(self, db):
        return job_repository.create(
            db,
            {
                "title": "Backend Intern",
                "company": "Example Co",
                "location": "Remote",
                "source": "manual",
            },
        )

    def test_create_job_match_result_record(self):
        db = self.SessionLocal()
        _, resume = self._seed_user_resume(db, "job_match_repo_user", "job_match_repo_user@example.com")
        job = self._seed_job(db)

        result = job_match_result_repository.create(
            db,
            {
                "job_id": job.id,
                "resume_id": resume.id,
                "mode": "job_match",
                "score": 87,
                "feedback": "Strong alignment with backend internship requirements.",
                "raw_content": "Score: 87",
                "provider": "mock",
                "model": "mock-model",
            },
        )

        assert result.id is not None
        assert result.job_id == job.id
        assert result.mode == "job_match"
        assert result.provider == "mock"
        db.close()

    def test_get_all_by_job_id_and_user_id_returns_latest_first(self):
        db = self.SessionLocal()
        user, resume = self._seed_user_resume(
            db,
            "job_match_repo_order",
            "job_match_repo_order@example.com",
        )
        job = self._seed_job(db)
        older = JobMatchResult(
            job_id=job.id,
            resume_id=resume.id,
            mode="job_match",
            score=74,
            feedback="Older feedback",
            raw_content="Older raw",
            provider="mock",
            model="mock-model",
            created_at=datetime.now() - timedelta(days=1),
        )
        newer = JobMatchResult(
            job_id=job.id,
            resume_id=resume.id,
            mode="job_match",
            score=91,
            feedback="Newer feedback",
            raw_content="Newer raw",
            provider="mock",
            model="mock-model",
            created_at=datetime.now(),
        )
        db.add_all([older, newer])
        db.commit()

        records = job_match_result_repository.get_all_by_job_id_and_user_id(
            db,
            job.id,
            user.id,
        )

        assert [record.feedback for record in records] == ["Newer feedback", "Older feedback"]
        db.close()

    def test_get_all_by_job_id_and_user_id_scopes_by_resume_owner(self):
        db = self.SessionLocal()
        user_1, resume_1 = self._seed_user_resume(
            db,
            "job_match_repo_owner_1",
            "job_match_repo_owner_1@example.com",
        )
        user_2, resume_2 = self._seed_user_resume(
            db,
            "job_match_repo_owner_2",
            "job_match_repo_owner_2@example.com",
        )
        job = self._seed_job(db)

        job_match_result_repository.create(
            db,
            {
                "job_id": job.id,
                "resume_id": resume_1.id,
                "mode": "job_match",
                "score": 82,
                "feedback": "Owner one feedback",
                "raw_content": "Owner one raw",
                "provider": "mock",
                "model": "mock-model",
            },
        )
        job_match_result_repository.create(
            db,
            {
                "job_id": job.id,
                "resume_id": resume_2.id,
                "mode": "job_match",
                "score": 83,
                "feedback": "Owner two feedback",
                "raw_content": "Owner two raw",
                "provider": "mock",
                "model": "mock-model",
            },
        )

        records = job_match_result_repository.get_all_by_job_id_and_user_id(
            db,
            job.id,
            user_1.id,
        )

        assert len(records) == 1
        assert records[0].resume_id == resume_1.id
        records_for_user_2 = job_match_result_repository.get_all_by_job_id_and_user_id(
            db,
            job.id,
            user_2.id,
        )
        assert len(records_for_user_2) == 1
        assert records_for_user_2[0].resume_id == resume_2.id
        db.close()
