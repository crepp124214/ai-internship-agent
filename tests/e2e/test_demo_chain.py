"""End-to-end tests for the official demo chain: Login -> Dashboard -> Resume -> Jobs -> Interview -> Tracker."""

import pytest
from unittest.mock import AsyncMock

from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from src.business_logic.interview import interview_service
from src.business_logic.job import job_service
from src.business_logic.resume import resume_service
from src.business_logic.tracker import tracker_service
from src.business_logic.tracker import tracker_service
from src.data_access.database import Base, get_db
from src.main import app


TEST_DATABASE_URL = "sqlite://"
engine = create_engine(
    TEST_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture
def test_db():
    """Provide an isolated in-memory database session."""
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(bind=engine)


@pytest.fixture
def client(test_db):
    """Provide a FastAPI test client wired to the test database."""

    def override_get_db():
        try:
            yield test_db
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


class TestDemoChain:
    """Full demo chain: register -> login -> me -> resumes -> jobs -> interview -> tracker."""

    def test_demo_chain(self, client: TestClient):
        """
        Official demo chain covered by this test:

        1. Register demo user
        2. Login -> get access token
        3. GET /users/me -> verify current user
        4. Create a resume -> verify it belongs to user
        5. POST /resumes/{id}/summary/ -> mock AI summary preview
        6. Create a job
        7. POST /jobs/{id}/match/ -> mock AI job match preview
        8. POST /interview/questions/generate/ -> mock interview questions
        9. GET /tracker/applications/ -> empty list for new user
        10. GET /health -> healthy
        11. GET /ready -> ready
        """
        # ── 1. Register demo user ──────────────────────────────────────────────
        register_resp = client.post(
            "/api/v1/users/",
            json={
                "username": "demouser",
                "email": "demo@example.com",
                "password": "demo123",
                "name": "Portfolio Demo User",
                "phone": "13800138000",
                "bio": "Demo user for walkthrough",
            },
        )
        assert register_resp.status_code == 200, f"Register failed: {register_resp.text}"
        user = register_resp.json()
        user_id = user["id"]
        assert user["username"] == "demouser"

        # ── 2. Login ─────────────────────────────────────────────────────────
        login_resp = client.post(
            "/api/v1/users/login/",
            json={"username": "demouser", "password": "demo123"},
        )
        assert login_resp.status_code == 200, f"Login failed: {login_resp.text}"
        token_payload = login_resp.json()
        assert token_payload["token_type"] == "bearer"
        assert token_payload["access_token"]
        access_token = token_payload["access_token"]
        auth_headers = {"Authorization": f"Bearer {access_token}"}

        # ── 3. GET /users/me ──────────────────────────────────────────────────
        me_resp = client.get("/api/v1/users/me", headers=auth_headers)
        assert me_resp.status_code == 200, f"/me failed: {me_resp.text}"
        me = me_resp.json()
        assert me["username"] == "demouser"
        assert me["name"] == "Portfolio Demo User"

        # ── 4. Create a resume ────────────────────────────────────────────────
        create_resume_resp = client.post(
            "/api/v1/resumes/",
            json={"title": "Demo Resume", "file_path": "/tmp/demo-resume.pdf"},
            headers=auth_headers,
        )
        assert create_resume_resp.status_code == 200, f"Create resume failed: {create_resume_resp.text}"
        resume = create_resume_resp.json()
        resume_id = resume["id"]
        assert resume["user_id"] == user_id

        # Update resume with content so the AI service has text to work with
        update_resume_resp = client.put(
            f"/api/v1/resumes/{resume_id}",
            json={
                "processed_content": (
                    "Experienced backend engineer proficient in Python, FastAPI, "
                    "and SQLAlchemy with strong database design skills."
                ),
                "resume_text": (
                    "Experienced backend engineer proficient in Python, FastAPI, "
                    "and SQLAlchemy with strong database design skills."
                ),
            },
            headers=auth_headers,
        )
        assert update_resume_resp.status_code == 200

        # ── 5. Resume summary preview ──────────────────────────────────────────
        original_resume_summary = resume_service.generate_resume_summary_preview
        resume_service.generate_resume_summary_preview = AsyncMock(
            return_value={
                "mode": "summary",
                "target_role": "Backend Intern",
                "content": "Demo resume summary content.",
                "raw_content": "Summary: Demo resume summary content.",
                "provider": "mock",
                "model": "mock-model",
            }
        )
        try:
            summary_resp = client.post(
                f"/api/v1/resumes/{resume_id}/summary/",
                json={"target_role": "Backend Intern"},
                headers=auth_headers,
            )
            assert summary_resp.status_code == 200, f"Summary failed: {summary_resp.text}"
            summary = summary_resp.json()
            assert summary["mode"] == "summary"
            assert summary["resume_id"] == resume_id
            assert summary["content"]
        finally:
            resume_service.generate_resume_summary_preview = original_resume_summary

        # ── 6. Create a job ───────────────────────────────────────────────────
        create_job_resp = client.post(
            "/api/v1/jobs/",
            json={
                "title": "Backend Engineer Intern",
                "company": "TechCorp",
                "location": "Beijing",
                "description": (
                    "We are looking for a backend engineer intern proficient in "
                    "Python, FastAPI, and SQLAlchemy to help build our internship "
                    "tracking platform."
                ),
                "requirements": "Python, FastAPI, SQLAlchemy",
                "salary": "8k-12k",
                "work_type": "intern",
                "experience": "0-1 year",
                "education": "Bachelor",
                "welfare": "Remote",
                "tags": "python,fastapi,sqlalchemy",
                "source": "internal",
                "source_url": "https://example.com/job/1",
                "source_id": "job-1",
            },
            headers=auth_headers,
        )
        assert create_job_resp.status_code == 200, f"Create job failed: {create_job_resp.text}"
        job = create_job_resp.json()
        job_id = job["id"]

        # ── 7. Job match preview ───────────────────────────────────────────────
        original_job_match = job_service.generate_job_match_preview
        job_service.generate_job_match_preview = AsyncMock(
            return_value={
                "mode": "job_match",
                "job_id": job_id,
                "resume_id": resume_id,
                "score": 85,
                "feedback": "Strong match for the backend intern role.",
                "raw_content": "Match score: 85",
                "provider": "mock",
                "model": "mock-model",
            }
        )
        try:
            match_resp = client.post(
                f"/api/v1/jobs/{job_id}/match/",
                json={"resume_id": resume_id},
                headers=auth_headers,
            )
            assert match_resp.status_code == 200, f"Match failed: {match_resp.text}"
            match = match_resp.json()
            assert match["mode"] == "job_match"
            assert match["score"] == 85
        finally:
            job_service.generate_job_match_preview = original_job_match

        # ── 8. Interview questions preview ─────────────────────────────────────
        # Note: POST /interview/questions/generate/ expects job_context (string),
        # NOT job_id. This is the correct API contract.
        original_interview_questions = interview_service.generate_interview_questions_preview
        interview_service.generate_interview_questions_preview = AsyncMock(
            return_value={
                "mode": "question_generation",
                "job_context": "Backend Engineer Intern at TechCorp",
                "resume_context": None,
                "count": 5,
                "questions": [
                    {
                        "question_number": 1,
                        "question_text": "What is your experience with FastAPI?",
                        "question_type": "technical",
                        "difficulty": "medium",
                        "category": "backend",
                    },
                    {
                        "question_number": 2,
                        "question_text": "How do you handle database migrations?",
                        "question_type": "technical",
                        "difficulty": "medium",
                        "category": "database",
                    },
                    {
                        "question_number": 3,
                        "question_text": "Describe a project you built with Python.",
                        "question_type": "behavioral",
                        "difficulty": "easy",
                        "category": "experience",
                    },
                    {
                        "question_number": 4,
                        "question_text": "What is your understanding of SQLAlchemy ORM?",
                        "question_type": "technical",
                        "difficulty": "hard",
                        "category": "database",
                    },
                    {
                        "question_number": 5,
                        "question_text": "How do you test your backend code?",
                        "question_type": "technical",
                        "difficulty": "medium",
                        "category": "testing",
                    },
                ],
                "raw_content": "Generated 5 interview questions.",
                "provider": "mock",
                "model": "mock-model",
            }
        )
        try:
            questions_resp = client.post(
                "/api/v1/interview/questions/generate/",
                json={
                    "job_context": "Backend Engineer Intern at TechCorp - Python, FastAPI, SQLAlchemy",
                    "resume_id": resume_id,
                    "count": 5,
                },
                headers=auth_headers,
            )
            assert questions_resp.status_code == 200, f"Questions failed: {questions_resp.text}"
            questions = questions_resp.json()
            assert questions["mode"] == "question_generation"
            assert len(questions["questions"]) == 5
        finally:
            interview_service.generate_interview_questions_preview = original_interview_questions

        # ── 9. Create tracker application ────────────────────────────────────
        create_app_resp = client.post(
            "/api/v1/tracker/applications/",
            json={
                "job_id": job_id,
                "resume_id": resume_id,
                "status": "applied",
                "notes": "Applied via demo walkthrough",
            },
            headers=auth_headers,
        )
        assert create_app_resp.status_code == 200, f"Create application failed: {create_app_resp.text}"
        application = create_app_resp.json()
        application_id = application["id"]
        assert application["user_id"] == user_id
        assert application["status"] == "applied"

        # ── 10. Tracker advice preview ─────────────────────────────────────────
        original_tracker_preview = tracker_service.generate_tracker_advice_preview
        tracker_service.generate_tracker_advice_preview = AsyncMock(
            return_value={
                "mode": "tracker_advice",
                "application_id": application_id,
                "summary": "Strong match for the backend intern role. Consider following up within a week.",
                "next_steps": [
                    "Send a follow-up email within 3-5 days",
                    "Prepare for a potential technical interview",
                    "Review the company's tech stack",
                ],
                "risks": [
                    "Competitive role - apply elsewhere as well",
                ],
                "raw_content": "Tracker advice generated.",
                "provider": "mock",
                "model": "mock-model",
            }
        )
        try:
            advice_resp = client.post(
                f"/api/v1/tracker/applications/{application_id}/advice/",
                headers=auth_headers,
            )
            assert advice_resp.status_code == 200, f"Advice preview failed: {advice_resp.text}"
            advice = advice_resp.json()
            assert advice["mode"] == "tracker_advice"
            assert advice["application_id"] == application_id
            assert len(advice["next_steps"]) == 3
        finally:
            tracker_service.generate_tracker_advice_preview = original_tracker_preview

        # ── 11. Persist tracker advice ─────────────────────────────────────────
        original_persist = tracker_service.persist_application_advice
        tracker_service.persist_application_advice = AsyncMock(
            return_value={
                "id": 1,
                "application_id": application_id,
                "mode": "tracker_advice",
                "summary": "Strong match for the backend intern role. Consider following up within a week.",
                "next_steps": '["Send a follow-up email within 3-5 days", "Prepare for a potential technical interview", "Review the company\'s tech stack"]',
                "risks": '["Competitive role - apply elsewhere as well"]',
                "raw_content": "Tracker advice persisted.",
                "provider": "mock",
                "model": "mock-model",
                "created_at": "2026-04-02T00:00:00",
                "updated_at": "2026-04-02T00:00:00",
            }
        )
        try:
            persist_resp = client.post(
                f"/api/v1/tracker/applications/{application_id}/advice/persist/",
                headers=auth_headers,
            )
            assert persist_resp.status_code == 200, f"Persist advice failed: {persist_resp.text}"
            persisted = persist_resp.json()
            assert persisted["mode"] == "tracker_advice"
            assert persisted["application_id"] == application_id
        finally:
            tracker_service.persist_application_advice = original_persist

        # ── 12. Tracker advice history ─────────────────────────────────────────
        original_history = tracker_service.get_tracker_advice_history
        tracker_service.get_tracker_advice_history = AsyncMock(
            return_value=[
                {
                    "id": 1,
                    "application_id": application_id,
                    "mode": "tracker_advice",
                    "summary": "Strong match for the backend intern role.",
                    "next_steps": '["Send a follow-up email"]',
                    "risks": '["Competitive role"]',
                    "raw_content": "Tracker advice persisted.",
                    "provider": "mock",
                    "model": "mock-model",
                    "created_at": "2026-04-02T00:00:00",
                    "updated_at": "2026-04-02T00:00:00",
                }
            ]
        )
        try:
            history_resp = client.get(
                f"/api/v1/tracker/applications/{application_id}/advice-history/",
                headers=auth_headers,
            )
            assert history_resp.status_code == 200, f"Advice history failed: {history_resp.text}"
            history = history_resp.json()
            assert isinstance(history, list)
            assert len(history) >= 1
        finally:
            tracker_service.get_tracker_advice_history = original_history

        # ── 13. Health and ready ─────────────────────────────────────────────
        health_resp = client.get("/health")
        assert health_resp.status_code == 200
        assert health_resp.json()["status"] == "healthy"

        ready_resp = client.get("/ready")
        assert ready_resp.status_code == 200
        assert ready_resp.json()["status"] == "ready"
