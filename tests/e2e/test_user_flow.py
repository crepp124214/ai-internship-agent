"""End-to-end tests for the minimal protected user flow."""

import pytest
from unittest.mock import AsyncMock
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from src.business_logic.resume import resume_service
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


class TestUserFlow:
    """Minimal user flow coverage for registration, login, and protected actions."""

    def test_user_registration_login_and_current_user_flow(self, client):
        register_response = client.post(
            "/api/v1/users/",
            json={
                "username": "testuser",
                "email": "test@example.com",
                "password": "password123",
                "name": "Test User",
                "phone": "13800138000",
                "bio": "A basic user for auth testing",
            },
        )

        assert register_response.status_code == 200
        created_user = register_response.json()
        assert created_user["username"] == "testuser"
        assert "password_hash" not in created_user

        login_response = client.post(
            "/api/v1/users/login/",
            json={"username": "testuser", "password": "password123"},
        )

        assert login_response.status_code == 200
        token_payload = login_response.json()
        assert token_payload["token_type"] == "bearer"
        assert token_payload["access_token"]

        me_response = client.get(
            "/api/v1/users/me",
            headers={"Authorization": f"Bearer {token_payload['access_token']}"},
        )

        assert me_response.status_code == 200
        payload = me_response.json()
        assert payload["id"] == created_user["id"]
        assert payload["username"] == "testuser"
        assert payload["email"] == "test@example.com"
        assert payload["name"] == "Test User"

    def test_login_allows_access_to_protected_resume_ai_flow(self, client):
        register_response = client.post(
            "/api/v1/users/",
            json={
                "username": "resumeauth",
                "email": "resumeauth@example.com",
                "password": "password123",
                "name": "Resume Auth",
            },
        )
        user_id = register_response.json()["id"]

        login_response = client.post(
            "/api/v1/users/login/",
            json={"username": "resumeauth", "password": "password123"},
        )
        access_token = login_response.json()["access_token"]
        auth_headers = {"Authorization": f"Bearer {access_token}"}

        create_resume_response = client.post(
            "/api/v1/resumes/",
            json={"title": "Resume Auth CV", "file_path": "/tmp/resume-auth.pdf"},
            headers=auth_headers,
        )

        assert create_resume_response.status_code == 200
        resume_id = create_resume_response.json()["id"]
        assert create_resume_response.json()["user_id"] == user_id

        update_resume_response = client.put(
            f"/api/v1/resumes/{resume_id}",
            json={"processed_content": "Built backend systems with FastAPI and SQLAlchemy."},
            headers=auth_headers,
        )
        assert update_resume_response.status_code == 200

        original_method = resume_service.generate_resume_summary_preview
        resume_service.generate_resume_summary_preview = AsyncMock(
            return_value={
                "mode": "summary",
                "target_role": "backend engineer",
                "content": "Strong backend-focused candidate.",
                "raw_content": "Summary: Strong backend-focused candidate.",
                "provider": "mock",
                "model": "mock-model",
            }
        )

        try:
            summary_response = client.post(
                f"/api/v1/resumes/{resume_id}/summary/",
                json={"target_role": "backend engineer"},
                headers=auth_headers,
            )
        finally:
            resume_service.generate_resume_summary_preview = original_method

        assert summary_response.status_code == 200
        assert summary_response.json()["mode"] == "summary"
        assert summary_response.json()["resume_id"] == resume_id

    def test_protected_route_rejects_missing_token(self, client):
        response = client.get("/api/v1/users/me")

        assert response.status_code == 401
        assert response.json()["detail"] == "Not authenticated"

    def test_login_rejects_invalid_password(self, client):
        client.post(
            "/api/v1/users/",
            json={
                "username": "wrongpass",
                "email": "wrongpass@example.com",
                "password": "password123",
                "name": "Wrong Pass",
            },
        )

        login_response = client.post(
            "/api/v1/users/login/",
            json={"username": "wrongpass", "password": "not-the-right-password"},
        )

        assert login_response.status_code == 401
        assert login_response.json()["detail"] == "Invalid username or password"

    def test_missing_user_routes_return_404(self, client):
        get_response = client.get("/api/v1/users/999999")
        assert get_response.status_code == 404

        update_response = client.put("/api/v1/users/999999", json={"name": "Missing"})
        assert update_response.status_code == 404

        delete_response = client.delete("/api/v1/users/999999")
        assert delete_response.status_code == 404
