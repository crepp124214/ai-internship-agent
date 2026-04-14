"""End-to-end tests for the complete demo user chain."""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend.infrastructure.database.session import Base, get_db
from backend.main import app


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
    """Full demo chain: login -> resumes -> jobs -> interview -> report."""

    def test_demo_login_and_resume_flow(self, client):
        """Login with demo credentials and create a resume."""
        # 1. Register user
        register_resp = client.post(
            "/api/v1/users/",
            json={
                "username": "demo",
                "email": "demo@example.com",
                "password": "demo123",
                "name": "Demo User",
            },
        )
        assert register_resp.status_code == 200
        user = register_resp.json()
        assert user["username"] == "demo"

        # 2. Login
        login_resp = client.post(
            "/api/v1/auth/login",
            json={"username": "demo", "password": "demo123"},
        )
        assert login_resp.status_code == 200
        token = login_resp.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # 3. Create resume
        resume_resp = client.post(
            "/api/v1/resumes/",
            json={"title": "My Resume", "file_path": "/tmp/resume.pdf"},
            headers=headers,
        )
        assert resume_resp.status_code == 200
        resume_id = resume_resp.json()["id"]

        # 4. List resumes
        list_resp = client.get("/api/v1/resumes/", headers=headers)
        assert list_resp.status_code == 200
        resume_ids = [r["id"] for r in list_resp.json()]
        assert resume_id in resume_ids

    def test_demo_job_search_flow(self, client):
        """Login and list jobs."""
        # Register
        register_resp = client.post(
            "/api/v1/users/",
            json={
                "username": "demo2",
                "email": "demo2@example.com",
                "password": "demo123",
                "name": "Demo User 2",
            },
        )
        assert register_resp.status_code == 200

        # Login
        login_resp = client.post(
            "/api/v1/auth/login",
            json={"username": "demo2", "password": "demo123"},
        )
        assert login_resp.status_code == 200
        token = login_resp.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # List jobs (no auth required)
        jobs_resp = client.get("/api/v1/jobs/")
        assert jobs_resp.status_code == 200

    def test_demo_interview_session_flow(self, client):
        """Login and create an interview session."""
        # Register
        register_resp = client.post(
            "/api/v1/users/",
            json={
                "username": "demo3",
                "email": "demo3@example.com",
                "password": "demo123",
                "name": "Demo User 3",
            },
        )
        assert register_resp.status_code == 200

        # Login
        login_resp = client.post(
            "/api/v1/auth/login",
            json={"username": "demo3", "password": "demo123"},
        )
        assert login_resp.status_code == 200
        token = login_resp.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # Create interview session
        session_resp = client.post(
            "/api/v1/interview/sessions/",
            json={"job_id": None, "session_type": "technical", "duration": 30, "total_questions": 3},
            headers=headers,
        )
        assert session_resp.status_code == 200
        session = session_resp.json()
        assert session["session_type"] == "technical"
        assert session["duration"] == 30
        assert session["total_questions"] == 3

        # List sessions
        list_resp = client.get("/api/v1/interview/sessions/", headers=headers)
        assert list_resp.status_code == 200
        session_ids = [s["id"] for s in list_resp.json()]
        assert session["id"] in session_ids

    def test_demo_protected_routes_require_auth(self, client):
        """Verify protected routes reject unauthenticated requests."""
        # Resume routes
        resume_get = client.get("/api/v1/resumes/")
        assert resume_get.status_code == 401

        resume_post = client.post("/api/v1/resumes/", json={"title": "Test"})
        assert resume_post.status_code == 401

        # Interview routes
        interview_get = client.get("/api/v1/interview/sessions/")
        assert interview_get.status_code == 401

        interview_post = client.post(
            "/api/v1/interview/sessions/",
            json={"job_id": None, "session_type": "technical"},
        )
        assert interview_post.status_code == 401
