"""Resume optimization repository tests."""

from datetime import datetime, timedelta

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.data_access.database import Base
from src.data_access.entities.resume import ResumeOptimization
from src.data_access.repositories.resume_optimization_repository import (
    resume_optimization_repository,
)
from src.data_access.repositories.resume_repository import resume_repository
from src.data_access.repositories.user_repository import user_repository


class TestResumeOptimizationRepository:
    def setup_method(self):
        self.engine = create_engine("sqlite:///:memory:")
        Base.metadata.create_all(bind=self.engine)
        self.SessionLocal = sessionmaker(bind=self.engine)

    def teardown_method(self):
        Base.metadata.drop_all(bind=self.engine)

    def _seed_resume(self, db, username: str, email: str):
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

    def test_create_resume_optimization_record(self):
        db = self.SessionLocal()
        _, resume = self._seed_resume(db, "resume_repo_user", "resume_repo_user@example.com")

        optimization = resume_optimization_repository.create(
            db,
            {
                "resume_id": resume.id,
                "original_text": "Original text",
                "optimized_text": "Improved text",
                "optimization_type": "improvements",
                "keywords": "python,fastapi",
                "score": 88,
                "ai_suggestion": "Tighten project bullets.",
                "mode": "resume_improvements",
                "raw_content": "Summary: Tighten project bullets.",
                "provider": "mock",
                "model": "mock-model",
            },
        )

        assert optimization.id is not None
        assert optimization.resume_id == resume.id
        assert optimization.mode == "resume_improvements"
        assert optimization.provider == "mock"
        db.close()

    def test_get_all_by_resume_id_returns_latest_first(self):
        db = self.SessionLocal()
        user, resume = self._seed_resume(
            db,
            "resume_repo_order",
            "resume_repo_order@example.com",
        )
        older = ResumeOptimization(
            resume_id=resume.id,
            original_text="Older original",
            optimized_text="Older optimized",
            optimization_type="improvements",
            keywords="older",
            score=72,
            ai_suggestion="Older suggestion",
            mode="resume_improvements",
            raw_content="Older raw",
            provider="mock",
            model="mock-model",
            created_at=datetime.now() - timedelta(days=1),
        )
        newer = ResumeOptimization(
            resume_id=resume.id,
            original_text="Newer original",
            optimized_text="Newer optimized",
            optimization_type="improvements",
            keywords="newer",
            score=92,
            ai_suggestion="Newer suggestion",
            mode="resume_improvements",
            raw_content="Newer raw",
            provider="mock",
            model="mock-model",
            created_at=datetime.now(),
        )
        db.add_all([older, newer])
        db.commit()

        records = resume_optimization_repository.get_all_by_resume_id_and_user_id(
            db,
            resume.id,
            user.id,
        )

        assert [record.optimized_text for record in records] == [
            "Newer optimized",
            "Older optimized",
        ]
        db.close()

    def test_get_all_by_resume_id_scopes_by_owner(self):
        db = self.SessionLocal()
        user_1, resume_1 = self._seed_resume(
            db,
            "resume_repo_owner_1",
            "resume_repo_owner_1@example.com",
        )
        user_2, resume_2 = self._seed_resume(
            db,
            "resume_repo_owner_2",
            "resume_repo_owner_2@example.com",
        )

        resume_optimization_repository.create(
            db,
            {
                "resume_id": resume_1.id,
                "original_text": "Owner one original",
                "optimized_text": "Owner one optimized",
                "optimization_type": "improvements",
                "keywords": "owner-one",
                "score": 80,
                "ai_suggestion": "Owner one suggestion",
                "mode": "resume_improvements",
                "raw_content": "Owner one raw",
                "provider": "mock",
                "model": "mock-model",
            },
        )
        resume_optimization_repository.create(
            db,
            {
                "resume_id": resume_2.id,
                "original_text": "Owner two original",
                "optimized_text": "Owner two optimized",
                "optimization_type": "improvements",
                "keywords": "owner-two",
                "score": 81,
                "ai_suggestion": "Owner two suggestion",
                "mode": "resume_improvements",
                "raw_content": "Owner two raw",
                "provider": "mock",
                "model": "mock-model",
            },
        )

        records = resume_optimization_repository.get_all_by_resume_id_and_user_id(
            db,
            resume_1.id,
            user_1.id,
        )

        assert len(records) == 1
        assert records[0].resume_id == resume_1.id
        assert resume_optimization_repository.get_all_by_resume_id_and_user_id(
            db,
            resume_1.id,
            user_2.id,
        ) == []
        db.close()

    def test_get_all_by_resume_id_and_mode_filters_to_requested_mode(self):
        db = self.SessionLocal()
        user, resume = self._seed_resume(
            db,
            "resume_repo_modes",
            "resume_repo_modes@example.com",
        )

        resume_optimization_repository.create(
            db,
            {
                "resume_id": resume.id,
                "original_text": "Original text",
                "optimized_text": "Summary text",
                "optimization_type": "summary",
                "keywords": "backend engineer",
                "score": None,
                "ai_suggestion": "Summary text",
                "mode": "resume_summary",
                "raw_content": "Summary raw",
                "provider": "mock",
                "model": "mock-model",
            },
        )
        resume_optimization_repository.create(
            db,
            {
                "resume_id": resume.id,
                "original_text": "Original text",
                "optimized_text": "Improvements text",
                "optimization_type": "content",
                "keywords": "python,fastapi",
                "score": 88,
                "ai_suggestion": "Improvements text",
                "mode": "resume_improvements",
                "raw_content": "Improvements raw",
                "provider": "mock",
                "model": "mock-model",
            },
        )

        summary_records = resume_optimization_repository.get_all_by_resume_id_and_mode(
            db,
            resume.id,
            "resume_summary",
            user.id,
        )
        improvement_records = resume_optimization_repository.get_all_by_resume_id_and_mode(
            db,
            resume.id,
            "resume_improvements",
            user.id,
        )

        assert [record.mode for record in summary_records] == ["resume_summary"]
        assert [record.mode for record in improvement_records] == ["resume_improvements"]
        db.close()
