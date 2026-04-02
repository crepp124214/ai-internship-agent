"""Integration tests for basic repository/database behavior."""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from src.data_access.database import Base
from src.data_access.entities.interview import InterviewSession
from src.data_access.entities.job import Job
from src.data_access.entities.resume import Resume
from src.data_access.entities.user import User
from src.data_access.repositories.base_repository import BaseRepository


TEST_DATABASE_URL = "sqlite:///:memory:"
engine = create_engine(TEST_DATABASE_URL, connect_args={"check_same_thread": False})
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture
def test_db():
    """Create a fresh in-memory database session for each test."""
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


class TestDatabaseOperations:
    def test_create_tables(self):
        Base.metadata.create_all(bind=engine)
        assert engine is not None

    def test_drop_tables(self):
        Base.metadata.create_all(bind=engine)
        Base.metadata.drop_all(bind=engine)


class TestUserRepository:
    def test_create_user(self, test_db):
        user_repository = BaseRepository(User)
        user_data = {
            "username": "testuser",
            "email": "test@example.com",
            "password_hash": "hashed_password",
            "name": "Test User",
            "phone": "13800138000",
            "bio": "Test profile",
        }

        user = user_repository.create(test_db, user_data)

        assert user is not None
        assert user.id is not None
        assert user.username == "testuser"
        assert user.email == "test@example.com"

    def test_get_user_by_id(self, test_db):
        user_repository = BaseRepository(User)
        created_user = user_repository.create(
            test_db,
            {
                "username": "testuser",
                "email": "test@example.com",
                "password_hash": "hashed_password",
                "name": "Test User",
            },
        )

        retrieved_user = user_repository.get_by_id(test_db, created_user.id)

        assert retrieved_user is not None
        assert retrieved_user.id == created_user.id
        assert retrieved_user.username == "testuser"

    def test_get_user_by_username(self, test_db):
        user_repository = BaseRepository(User)
        user_repository.create(
            test_db,
            {
                "username": "testuser",
                "email": "test@example.com",
                "password_hash": "hashed_password",
                "name": "Test User",
            },
        )

        users = user_repository.get_by_field(test_db, "username", "testuser")

        assert len(users) == 1
        assert users[0].username == "testuser"

    def test_update_user(self, test_db):
        user_repository = BaseRepository(User)
        user = user_repository.create(
            test_db,
            {
                "username": "testuser",
                "email": "test@example.com",
                "password_hash": "hashed_password",
                "name": "Test User",
            },
        )

        updated_user = user_repository.update(test_db, user.id, {"name": "Updated User"})

        assert updated_user is not None
        assert updated_user.name == "Updated User"
        assert updated_user.username == "testuser"

    def test_delete_user(self, test_db):
        user_repository = BaseRepository(User)
        user = user_repository.create(
            test_db,
            {
                "username": "testuser",
                "email": "test@example.com",
                "password_hash": "hashed_password",
                "name": "Test User",
            },
        )

        deleted = user_repository.delete(test_db, user.id)

        assert deleted is True
        assert user_repository.get_by_id(test_db, user.id) is None


class TestResumeRepository:
    def test_create_resume(self, test_db):
        resume_repository = BaseRepository(Resume)
        resume_data = {
            "title": "My Resume",
            "user_id": 1,
            "file_name": "resume.pdf",
            "file_type": "pdf",
            "original_file_path": "/path/to/resume.pdf",
            "processed_content": "",
            "resume_text": "",
            "language": "zh-CN",
        }

        resume = resume_repository.create(test_db, resume_data)

        assert resume is not None
        assert resume.id is not None
        assert resume.title == "My Resume"

    def test_get_resume_by_id(self, test_db):
        resume_repository = BaseRepository(Resume)
        created_resume = resume_repository.create(
            test_db,
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

        retrieved_resume = resume_repository.get_by_id(test_db, created_resume.id)

        assert retrieved_resume is not None
        assert retrieved_resume.id == created_resume.id
        assert retrieved_resume.title == "My Resume"

    def test_update_resume(self, test_db):
        resume_repository = BaseRepository(Resume)
        resume = resume_repository.create(
            test_db,
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

        updated_resume = resume_repository.update(
            test_db,
            resume.id,
            {"title": "Updated Resume", "processed_content": "processed"},
        )

        assert updated_resume is not None
        assert updated_resume.title == "Updated Resume"
        assert updated_resume.processed_content == "processed"


class TestJobRepository:
    def test_create_job(self, test_db):
        job_repository = BaseRepository(Job)
        job_data = {
            "title": "Software Engineer Intern",
            "company": "Test Company",
            "location": "Beijing",
            "salary": "10k-15k",
            "description": "Job description",
            "requirements": "Job requirements",
            "welfare": "Benefits",
            "source_url": "https://example.com/job/1",
            "source": "test",
        }

        job = job_repository.create(test_db, job_data)

        assert job is not None
        assert job.id is not None
        assert job.title == "Software Engineer Intern"
        assert job.company == "Test Company"

    def test_get_job_by_company(self, test_db):
        job_repository = BaseRepository(Job)
        job_repository.create(
            test_db,
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

        jobs = job_repository.get_by_field(test_db, "company", "Test Company")

        assert len(jobs) == 1
        assert jobs[0].company == "Test Company"


class TestInterviewRepository:
    def test_create_interview_session(self, test_db):
        interview_repository = BaseRepository(InterviewSession)
        interview_data = {
            "user_id": 1,
            "job_id": 1,
            "session_type": "technical",
            "duration": 30,
            "total_questions": 5,
            "answered_questions": 0,
            "average_score": 0,
            "completed": False,
        }

        interview = interview_repository.create(test_db, interview_data)

        assert interview is not None
        assert interview.id is not None
        assert interview.session_type == "technical"

    def test_get_interview_by_completed(self, test_db):
        interview_repository = BaseRepository(InterviewSession)
        interview_repository.create(
            test_db,
            {
                "user_id": 1,
                "job_id": 1,
                "session_type": "technical",
                "duration": 30,
                "total_questions": 5,
                "answered_questions": 0,
                "average_score": 0,
                "completed": False,
            },
        )

        interviews = interview_repository.get_by_field(test_db, "completed", False)

        assert len(interviews) == 1
        assert interviews[0].completed is False
