"""Repository unit tests aligned with current data models."""

from sqlalchemy import Column, Integer, String, create_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from src.data_access.entities.interview import (
    InterviewQuestion,
    InterviewRecord,
    InterviewSession,
)
from src.data_access.entities.job import Job
from src.data_access.entities.resume import Resume
from src.data_access.entities.user import User
from src.data_access.repositories.base_repository import BaseRepository, create_repository


RepositoryTestBase = declarative_base()


class RepositoryModel(RepositoryTestBase):
    __tablename__ = "test_models"

    id = Column(Integer, primary_key=True)
    name = Column(String(50))
    value = Column(String(100))


class TestBaseRepository:
    def setup_method(self):
        self.engine = create_engine("sqlite:///:memory:")
        RepositoryTestBase.metadata.create_all(bind=self.engine)
        self.SessionLocal = sessionmaker(bind=self.engine)
        self.repository = BaseRepository(RepositoryModel)

    def teardown_method(self):
        RepositoryTestBase.metadata.drop_all(bind=self.engine)

    def test_get_by_id(self):
        db = self.SessionLocal()
        obj = RepositoryModel(name="test1", value="value1")
        db.add(obj)
        db.commit()
        db.refresh(obj)

        result = self.repository.get_by_id(db, obj.id)

        assert result is not None
        assert result.name == "test1"
        assert result.value == "value1"
        db.close()

    def test_get_all(self):
        db = self.SessionLocal()
        for i in range(3):
            db.add(RepositoryModel(name=f"test{i}", value=f"value{i}"))
        db.commit()

        results = self.repository.get_all(db)

        assert len(results) == 3
        db.close()

    def test_get_by_field(self):
        db = self.SessionLocal()
        db.add_all(
            [
                RepositoryModel(name="same", value="a"),
                RepositoryModel(name="same", value="b"),
                RepositoryModel(name="other", value="c"),
            ]
        )
        db.commit()

        results = self.repository.get_by_field(db, "name", "same")

        assert len(results) == 2
        db.close()

    def test_create_update_delete(self):
        db = self.SessionLocal()
        created = self.repository.create(db, {"name": "test", "value": "v1"})
        updated = self.repository.update(db, created.id, {"value": "v2"})
        deleted = self.repository.delete(db, created.id)

        assert created.id is not None
        assert updated.value == "v2"
        assert deleted is True
        assert self.repository.get_by_id(db, created.id) is None
        db.close()

    def test_count(self):
        db = self.SessionLocal()
        for i in range(5):
            db.add(RepositoryModel(name=f"test{i}", value=f"value{i}"))
        db.commit()

        assert self.repository.count(db) == 5
        db.close()


class TestCreateRepository:
    def test_create_repository_instance(self):
        repository = create_repository(RepositoryModel)

        assert repository is not None
        assert repository.model == RepositoryModel

    def test_created_repository_functionality(self):
        engine = create_engine("sqlite:///:memory:")
        RepositoryTestBase.metadata.create_all(bind=engine)
        SessionLocal = sessionmaker(bind=engine)
        repository = create_repository(RepositoryModel)
        db = SessionLocal()

        result = repository.create(db, {"name": "test", "value": "value1"})
        retrieved = repository.get_by_id(db, result.id)

        assert retrieved is not None
        assert retrieved.name == "test"

        db.close()
        RepositoryTestBase.metadata.drop_all(bind=engine)


class TestModelRepositories:
    def setup_method(self):
        self.engine = create_engine("sqlite:///:memory:")
        from src.data_access.database import Base

        Base.metadata.create_all(bind=self.engine)
        self.SessionLocal = sessionmaker(bind=self.engine)

        from src.data_access.repositories.user_repository import user_repository
        from src.data_access.repositories.resume_repository import resume_repository
        from src.data_access.repositories.job_repository import job_repository
        from src.data_access.repositories.interview_repository import (
            interview_question_repository,
            interview_record_repository,
            interview_session_repository,
        )

        self.user_repository = user_repository
        self.resume_repository = resume_repository
        self.job_repository = job_repository
        self.interview_question_repository = interview_question_repository
        self.interview_record_repository = interview_record_repository
        self.interview_session_repository = interview_session_repository

    def teardown_method(self):
        from src.data_access.database import Base

        Base.metadata.drop_all(bind=self.engine)

    def test_create_user(self):
        db = self.SessionLocal()
        user = self.user_repository.create(
            db,
            {
                "username": "testuser",
                "email": "test@example.com",
                "password_hash": "hashed_password",
                "name": "Test User",
            },
        )

        assert user is not None
        assert user.username == "testuser"
        db.close()

    def test_create_resume(self):
        db = self.SessionLocal()
        resume = self.resume_repository.create(
            db,
            {
                "title": "My Resume",
                "user_id": 1,
                "file_name": "resume.pdf",
                "file_type": "pdf",
                "original_file_path": "/path/to/resume.pdf",
                "processed_content": "",
                "resume_text": "",
                "language": "zh-CN",
            },
        )

        assert resume is not None
        assert resume.file_name == "resume.pdf"
        db.close()

    def test_get_resumes_by_user_id(self):
        db = self.SessionLocal()
        for i in range(3):
            self.resume_repository.create(
                db,
                {
                    "title": f"Resume {i}",
                    "user_id": 1,
                    "file_name": f"resume{i}.pdf",
                    "file_type": "pdf",
                    "original_file_path": f"/path/to/resume{i}.pdf",
                    "processed_content": "",
                    "resume_text": "",
                    "language": "zh-CN",
                },
            )

        resumes = self.resume_repository.get_by_field(db, "user_id", 1)

        assert len(resumes) == 3
        db.close()

    def test_create_job(self):
        db = self.SessionLocal()
        job = self.job_repository.create(
            db,
            {
                "title": "Software Engineer Intern",
                "company": "Test Company",
                "location": "Beijing",
                "salary": "10k-15k",
                "description": "Job description",
                "requirements": "Job requirements",
                "welfare": "Benefits",
                "source_url": "https://example.com/job/1",
                "source": "test",
            },
        )

        assert job is not None
        assert job.source_url == "https://example.com/job/1"
        db.close()

    def test_get_jobs_by_company(self):
        db = self.SessionLocal()
        for i in range(2):
            self.job_repository.create(
                db,
                {
                    "title": f"Job {i}",
                    "company": "Test Company",
                    "location": "Beijing",
                    "salary": "10k-15k",
                    "description": "Job description",
                    "requirements": "Job requirements",
                    "welfare": "Benefits",
                    "source_url": "https://example.com/job/1",
                    "source": "test",
                },
            )

        jobs = self.job_repository.get_by_field(db, "company", "Test Company")

        assert len(jobs) == 2
        db.close()

    def test_create_interview_question(self):
        db = self.SessionLocal()
        question = self.interview_question_repository.create(
            db,
            {
                "question_type": "technical",
                "difficulty": "medium",
                "question_text": "Explain dependency injection.",
                "category": "backend",
                "tags": "python,fastapi",
            },
        )

        assert question is not None
        assert question.category == "backend"
        db.close()

    def test_get_interview_questions_by_category(self):
        db = self.SessionLocal()
        for i in range(2):
            self.interview_question_repository.create(
                db,
                {
                    "question_type": "technical",
                    "difficulty": "medium",
                    "question_text": f"Question {i}",
                    "category": "backend",
                    "tags": "python",
                },
            )

        questions = self.interview_question_repository.get_by_field(db, "category", "backend")

        assert len(questions) == 2
        db.close()

    def test_create_interview_record(self):
        db = self.SessionLocal()
        record = self.interview_record_repository.create(
            db,
            {
                "user_id": 1,
                "job_id": 1,
                "question_id": 1,
                "user_answer": "My answer",
                "ai_evaluation": "Looks good",
                "score": 88,
                "feedback": "Clear and structured",
            },
        )

        assert record is not None
        assert record.score == 88
        db.close()

    def test_get_interview_sessions_by_completed(self):
        db = self.SessionLocal()
        for _ in range(2):
            self.interview_session_repository.create(
                db,
                {
                    "user_id": 1,
                    "job_id": 1,
                    "session_type": "technical",
                    "duration": 30,
                    "total_questions": 5,
                    "answered_questions": 3,
                    "average_score": 80,
                    "completed": False,
                },
            )

        sessions = self.interview_session_repository.get_by_field(db, "completed", False)

        assert len(sessions) == 2
        db.close()
