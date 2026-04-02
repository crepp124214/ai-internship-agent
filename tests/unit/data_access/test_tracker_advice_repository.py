"""Tracker advice repository tests."""

from datetime import datetime, timedelta

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.data_access.database import Base
from src.data_access.entities.tracker import TrackerAdvice
from src.data_access.repositories.job_repository import job_repository
from src.data_access.repositories.resume_repository import resume_repository
from src.data_access.repositories.tracker_advice_repository import tracker_advice_repository
from src.data_access.repositories.tracker_repository import tracker_repository
from src.data_access.repositories.user_repository import user_repository


class TestTrackerAdviceRepository:
    def setup_method(self):
        self.engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(bind=self.engine)
        self.SessionLocal = sessionmaker(bind=self.engine)

    def teardown_method(self):
        Base.metadata.drop_all(bind=self.engine)

    def _seed_application(self, db, username: str, email: str):
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
        job = job_repository.create(
            db,
            {
                "title": "Backend Intern",
                "company": "Example Co",
                "location": "Remote",
                "source": "manual",
            },
        )
        application = tracker_repository.create(
            db,
            {
                "job_id": job.id,
                "resume_id": resume.id,
                "status": "applied",
                "notes": "Initial notes",
                "user_id": user.id,
            },
        )
        return user, application

    def test_create_tracker_advice_record(self):
        db = self.SessionLocal()
        _, application = self._seed_application(db, "tracker_repo_user", "tracker_repo_user@example.com")

        advice = tracker_advice_repository.create(
            db,
            {
                "application_id": application.id,
                "summary": "Follow up this week.",
                "next_steps": '["Email recruiter"]',
                "risks": '["No referral"]',
                "raw_content": "Summary: Follow up this week.",
                "provider": "mock",
                "model": "mock-model",
            },
        )

        assert advice.id is not None
        assert advice.application_id == application.id
        assert advice.provider == "mock"
        db.close()

    def test_get_all_by_application_id_and_user_id_returns_latest_first(self):
        db = self.SessionLocal()
        user, application = self._seed_application(db, "tracker_repo_order", "tracker_repo_order@example.com")
        older = TrackerAdvice(
            application_id=application.id,
            summary="Older summary",
            next_steps='["Older step"]',
            risks='["Older risk"]',
            raw_content="Older",
            provider="mock",
            model="mock-model",
            created_at=datetime.now() - timedelta(days=1),
        )
        newer = TrackerAdvice(
            application_id=application.id,
            summary="Newer summary",
            next_steps='["Newer step"]',
            risks='["Newer risk"]',
            raw_content="Newer",
            provider="mock",
            model="mock-model",
            created_at=datetime.now(),
        )
        db.add_all([older, newer])
        db.commit()

        records = tracker_advice_repository.get_all_by_application_id_and_user_id(
            db,
            application.id,
            user.id,
        )

        assert [record.summary for record in records] == ["Newer summary", "Older summary"]
        db.close()

    def test_get_all_by_application_id_and_user_id_scopes_by_owner(self):
        db = self.SessionLocal()
        user_1, application_1 = self._seed_application(
            db,
            "tracker_repo_owner_1",
            "tracker_repo_owner_1@example.com",
        )
        user_2, application_2 = self._seed_application(
            db,
            "tracker_repo_owner_2",
            "tracker_repo_owner_2@example.com",
        )

        tracker_advice_repository.create(
            db,
            {
                "application_id": application_1.id,
                "summary": "Owner one summary",
                "next_steps": '["Owner one step"]',
                "risks": '["Owner one risk"]',
                "raw_content": "Owner one",
                "provider": "mock",
                "model": "mock-model",
            },
        )
        tracker_advice_repository.create(
            db,
            {
                "application_id": application_2.id,
                "summary": "Owner two summary",
                "next_steps": '["Owner two step"]',
                "risks": '["Owner two risk"]',
                "raw_content": "Owner two",
                "provider": "mock",
                "model": "mock-model",
            },
        )

        records = tracker_advice_repository.get_all_by_application_id_and_user_id(
            db,
            application_1.id,
            user_1.id,
        )

        assert len(records) == 1
        assert records[0].application_id == application_1.id
        assert tracker_advice_repository.get_all_by_application_id_and_user_id(
            db,
            application_1.id,
            user_2.id,
        ) == []
        db.close()
