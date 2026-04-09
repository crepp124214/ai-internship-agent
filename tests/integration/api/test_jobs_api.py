"""Jobs API integration tests."""

from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from src.business_logic.job import job_service
from src.data_access.database import Base, get_db
from src.data_access.repositories.job_repository import job_repository
from src.data_access.repositories.resume_repository import resume_repository
from src.data_access.repositories.user_repository import user_repository
from src.main import app
from src.presentation.api.deps import get_current_user


engine = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture(scope="module", autouse=True)
def setup_database():
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture
def db_session():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


@pytest.fixture
def client(db_session):
    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as test_client:
        yield test_client
    app.dependency_overrides.clear()


def _set_current_user(user_id):
    app.dependency_overrides[get_current_user] = lambda: SimpleNamespace(id=user_id)


def _seed_user(db, username, email):
    return user_repository.create(
        db,
        {
            "username": username,
            "email": email,
            "password_hash": "hashed-password",
            "name": username,
        },
    )


def _seed_job(db):
    return job_repository.create(
        db,
        {
            "title": "Backend Intern",
            "company": "Test Co",
            "location": "Beijing",
            "description": "Build APIs",
            "requirements": "Python, FastAPI",
            "salary": "10k-15k",
            "work_type": "internship",
            "experience": "0-1 year",
            "education": "Bachelor",
            "welfare": "Remote",
            "tags": "python,fastapi",
            "source": "test",
            "source_url": "https://example.com/job/1",
            "source_id": "job-1",
            "is_active": True,
        },
    )


def _seed_resume(db, user_id, resume_text="Built APIs with FastAPI"):
    return resume_repository.create(
        db,
        {
            "title": "Resume",
            "user_id": user_id,
            "original_file_path": "/tmp/resume.pdf",
            "file_name": "resume.pdf",
            "file_type": "pdf",
            "processed_content": "",
            "resume_text": resume_text,
            "language": "zh-CN",
        },
    )


def test_jobs_create_requires_authentication(client):
    response = client.post(
        "/api/v1/jobs/",
        json={
            "title": "Backend Intern",
            "company": "Test Co",
            "location": "Beijing",
            "description": "Build APIs",
            "requirements": "Python, FastAPI",
            "salary": "10k-15k",
            "work_type": "internship",
            "experience": "0-1 year",
            "education": "Bachelor",
            "welfare": "Remote",
            "tags": "python,fastapi",
            "source": "test",
            "source_url": "https://example.com/job/1",
            "source_id": "job-1",
        },
    )

    assert response.status_code == 401


def test_jobs_create_succeeds_with_authenticated_user(db_session, client):
    user = _seed_user(db_session, "job_creator", "job_creator@example.com")
    _set_current_user(user.id)

    response = client.post(
        "/api/v1/jobs/",
        json={
            "title": "Backend Intern",
            "company": "Test Co",
            "location": "Beijing",
            "description": "Build APIs",
            "requirements": "Python, FastAPI",
            "salary": "10k-15k",
            "work_type": "internship",
            "experience": "0-1 year",
            "education": "Bachelor",
            "welfare": "Remote",
            "tags": "python,fastapi",
            "source": "test",
            "source_url": "https://example.com/job/1",
            "source_id": "job-1",
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["title"] == "Backend Intern"
    assert payload["company"] == "Test Co"


def test_jobs_update_propagates_not_found(client):
    _set_current_user(999)
    with patch("src.presentation.api.v1.jobs.job_service.update_job", new=AsyncMock(return_value=None)):
        response = client.put(
            "/api/v1/jobs/999",
            json={"is_active": False},
        )

    assert response.status_code == 404
    # 统一错误格式: code, message, retryable
    body = response.json()
    assert body["code"] == "RESOURCE_NOT_FOUND"
    assert "岗位不存在" in body["message"]


def test_jobs_update_requires_authentication(db_session, client):
    job = _seed_job(db_session)

    response = client.put(
        f"/api/v1/jobs/{job.id}",
        json={"title": "anonymous update"},
    )

    assert response.status_code == 401


def test_jobs_delete_propagates_not_found(client):
    _set_current_user(999)
    with patch("src.presentation.api.v1.jobs.job_service.delete_job", new=AsyncMock(return_value=False)):
        response = client.delete("/api/v1/jobs/999")

    assert response.status_code == 404
    # 统一错误格式: code, message, retryable
    body = response.json()
    assert body["code"] == "RESOURCE_NOT_FOUND"
    assert "岗位不存在" in body["message"]


def test_jobs_delete_requires_authentication(db_session, client):
    job = _seed_job(db_session)

    response = client.delete(f"/api/v1/jobs/{job.id}")

    assert response.status_code == 401


def test_jobs_match_endpoint_returns_structured_result(db_session, client):
    user = _seed_user(db_session, "user1", "user1@example.com")
    job = _seed_job(db_session)
    resume = _seed_resume(db_session, user.id)
    _set_current_user(user.id)

    with patch(
        "src.presentation.api.v1.jobs.job_service.generate_job_match_preview",
        new=AsyncMock(
            return_value=SimpleNamespace(
                mode="job_match",
                job_id=job.id,
                resume_id=resume.id,
                score=88,
                feedback="Strong fit",
                raw_content="Score: 88\nFeedback: Strong fit.",
                provider="mock",
                model="mock-model",
            )
        ),
        create=True,
    ):
        response = client.post(
            f"/api/v1/jobs/{job.id}/match/",
            json={"resume_id": resume.id},
        )

    assert response.status_code == 200
    payload = response.json()
    assert payload["mode"] == "job_match"
    assert payload["job_id"] == job.id
    assert payload["resume_id"] == resume.id
    assert payload["score"] == 88
    assert payload["feedback"] == "Strong fit"
    assert payload["raw_content"] == "Score: 88\nFeedback: Strong fit."
    assert payload["provider"] == "mock"
    assert payload["model"] == "mock-model"


def test_jobs_match_endpoint_returns_404_for_missing_job(db_session, client):
    user = _seed_user(db_session, "user2", "user2@example.com")
    resume = _seed_resume(db_session, user.id)
    _set_current_user(user.id)

    with patch(
        "src.presentation.api.v1.jobs.job_service.generate_job_match_preview",
        new=AsyncMock(side_effect=ValueError("job not found")),
        create=True,
    ):
        response = client.post(
            "/api/v1/jobs/999/match/",
            json={"resume_id": resume.id},
        )

    assert response.status_code == 404
    # 统一错误格式: code, message, retryable
    body = response.json()
    assert body["code"] == "RESOURCE_NOT_FOUND"
    assert "job not found" in body["message"]


def test_jobs_match_endpoint_returns_404_for_unowned_resume(db_session, client):
    owner = _seed_user(db_session, "owner", "owner@example.com")
    other = _seed_user(db_session, "other", "other@example.com")
    job = _seed_job(db_session)
    resume = _seed_resume(db_session, other.id)
    _set_current_user(owner.id)

    with patch(
        "src.presentation.api.v1.jobs.job_service.generate_job_match_preview",
        new=AsyncMock(side_effect=ValueError("resume not found")),
        create=True,
    ):
        response = client.post(
            f"/api/v1/jobs/{job.id}/match/",
            json={"resume_id": resume.id},
        )

    assert response.status_code == 404
    # 统一错误格式: code, message, retryable
    body = response.json()
    assert body["code"] == "RESOURCE_NOT_FOUND"
    assert "resume not found" in body["message"]


def test_jobs_match_endpoint_returns_400_for_empty_resume_text(db_session, client):
    user = _seed_user(db_session, "user3", "user3@example.com")
    job = _seed_job(db_session)
    resume = _seed_resume(db_session, user.id, resume_text="")
    _set_current_user(user.id)

    with patch(
        "src.presentation.api.v1.jobs.job_service.generate_job_match_preview",
        new=AsyncMock(side_effect=ValueError("resume text is empty")),
        create=True,
    ):
        response = client.post(
            f"/api/v1/jobs/{job.id}/match/",
            json={"resume_id": resume.id},
        )

    assert response.status_code == 400
    # 统一错误格式: code, message, retryable
    body = response.json()
    assert body["code"] == "BAD_REQUEST"
    assert "resume text is empty" in body["message"]


def test_jobs_match_endpoint_returns_500_for_provider_failure(db_session, client):
    user = _seed_user(db_session, "user4", "user4@example.com")
    job = _seed_job(db_session)
    resume = _seed_resume(db_session, user.id)
    _set_current_user(user.id)

    with patch(
        "src.presentation.api.v1.jobs.job_service.generate_job_match_preview",
        new=AsyncMock(side_effect=RuntimeError("provider failure")),
        create=True,
    ):
        response = client.post(
            f"/api/v1/jobs/{job.id}/match/",
            json={"resume_id": resume.id},
        )

    assert response.status_code == 500
    # 统一错误格式: code, message, retryable
    # 未知异常隐藏内部细节
    body = response.json()
    assert body["code"] == "INTERNAL_ERROR"
    assert body["retryable"] is True


def test_jobs_match_persist_endpoint_returns_created_record(db_session, client):
    user = _seed_user(db_session, "user5", "user5@example.com")
    job = _seed_job(db_session)
    resume = _seed_resume(db_session, user.id)
    _set_current_user(user.id)

    with patch(
        "src.presentation.api.v1.jobs.job_service.match_job_to_resume",
        new=AsyncMock(
            return_value={
                "mode": "job_match",
                "job_id": job.id,
                "resume_id": resume.id,
                "score": 91,
                "feedback": "Great fit",
                "raw_content": "Score: 91\nFeedback: Great fit.",
                "provider": "mock",
                "model": "mock-model",
            }
        ),
        create=True,
    ):
        response = client.post(
            f"/api/v1/jobs/{job.id}/match/persist/",
            json={"resume_id": resume.id},
        )

    assert response.status_code == 200
    payload = response.json()
    assert payload["job_id"] == job.id
    assert payload["resume_id"] == resume.id
    assert payload["mode"] == "job_match"
    assert payload["score"] == 91
    assert payload["feedback"] == "Great fit"
    assert payload["raw_content"] == "Score: 91\nFeedback: Great fit."
    assert payload["provider"] == "mock"
    assert payload["model"] == "mock-model"


def test_jobs_match_history_endpoint_returns_scoped_records(db_session, client):
    user_1 = _seed_user(db_session, "user6", "user6@example.com")
    user_2 = _seed_user(db_session, "user7", "user7@example.com")
    job = _seed_job(db_session)
    resume_1 = _seed_resume(db_session, user_1.id, resume_text="Built APIs")
    resume_2 = _seed_resume(db_session, user_2.id, resume_text="Built APIs")

    _set_current_user(user_1.id)
    with patch(
        "src.presentation.api.v1.jobs.job_service.match_job_to_resume",
        new=AsyncMock(
            return_value={
                "mode": "job_match",
                "job_id": job.id,
                "resume_id": resume_1.id,
                "score": 87,
                "feedback": "Strong fit",
                "raw_content": "Score: 87\nFeedback: Strong fit.",
                "provider": "mock",
                "model": "mock-model",
            }
        ),
        create=True,
    ):
        first_response = client.post(
            f"/api/v1/jobs/{job.id}/match/persist/",
            json={"resume_id": resume_1.id},
        )

    assert first_response.status_code == 200
    first_record = first_response.json()

    _set_current_user(user_2.id)
    with patch(
        "src.presentation.api.v1.jobs.job_service.match_job_to_resume",
        new=AsyncMock(
            return_value={
                "mode": "job_match",
                "job_id": job.id,
                "resume_id": resume_2.id,
                "score": 73,
                "feedback": "Good fit",
                "raw_content": "Score: 73\nFeedback: Good fit.",
                "provider": "mock",
                "model": "mock-model",
            }
        ),
        create=True,
    ):
        second_response = client.post(
            f"/api/v1/jobs/{job.id}/match/persist/",
            json={"resume_id": resume_2.id},
        )

    assert second_response.status_code == 200

    _set_current_user(user_1.id)
    response = client.get(f"/api/v1/jobs/{job.id}/match-history/")

    assert response.status_code == 200
    payload = response.json()
    assert len(payload) == 1
    assert payload[0]["id"] == first_record["id"]
    assert payload[0]["job_id"] == job.id
    assert payload[0]["resume_id"] == resume_1.id


def test_jobs_match_persist_endpoint_returns_404_for_missing_job(db_session, client):
    user = _seed_user(db_session, "user8", "user8@example.com")
    resume = _seed_resume(db_session, user.id)
    _set_current_user(user.id)

    with patch(
        "src.presentation.api.v1.jobs.job_service.persist_job_match",
        new=AsyncMock(side_effect=ValueError("job not found")),
        create=True,
    ):
        response = client.post(
            "/api/v1/jobs/999/match/persist/",
            json={"resume_id": resume.id},
        )

    assert response.status_code == 404
    # 统一错误格式: code, message, retryable
    body = response.json()
    assert body["code"] == "RESOURCE_NOT_FOUND"
    assert "job not found" in body["message"]


def test_jobs_match_persist_endpoint_returns_404_for_unowned_resume(db_session, client):
    owner = _seed_user(db_session, "owner2", "owner2@example.com")
    other = _seed_user(db_session, "other2", "other2@example.com")
    job = _seed_job(db_session)
    resume = _seed_resume(db_session, other.id)
    _set_current_user(owner.id)

    with patch(
        "src.presentation.api.v1.jobs.job_service.persist_job_match",
        new=AsyncMock(side_effect=ValueError("resume not found")),
        create=True,
    ):
        response = client.post(
            f"/api/v1/jobs/{job.id}/match/persist/",
            json={"resume_id": resume.id},
        )

    assert response.status_code == 404
    # 统一错误格式: code, message, retryable
    body = response.json()
    assert body["code"] == "RESOURCE_NOT_FOUND"
    assert "resume not found" in body["message"]


def test_jobs_match_persist_endpoint_returns_400_for_empty_resume_text(db_session, client):
    user = _seed_user(db_session, "user9", "user9@example.com")
    job = _seed_job(db_session)
    resume = _seed_resume(db_session, user.id, resume_text="")
    _set_current_user(user.id)

    with patch(
        "src.presentation.api.v1.jobs.job_service.persist_job_match",
        new=AsyncMock(side_effect=ValueError("resume text is empty")),
        create=True,
    ):
        response = client.post(
            f"/api/v1/jobs/{job.id}/match/persist/",
            json={"resume_id": resume.id},
        )

    assert response.status_code == 400
    # 统一错误格式: code, message, retryable
    body = response.json()
    assert body["code"] == "BAD_REQUEST"
    assert "resume text is empty" in body["message"]


def test_jobs_match_persist_endpoint_returns_500_for_provider_failure(db_session, client):
    user = _seed_user(db_session, "user10", "user10@example.com")
    job = _seed_job(db_session)
    resume = _seed_resume(db_session, user.id)
    _set_current_user(user.id)

    with patch(
        "src.presentation.api.v1.jobs.job_service.persist_job_match",
        new=AsyncMock(side_effect=RuntimeError("provider failure")),
        create=True,
    ):
        response = client.post(
            f"/api/v1/jobs/{job.id}/match/persist/",
            json={"resume_id": resume.id},
        )

    assert response.status_code == 500
    # 统一错误格式: code, message, retryable
    # 未知异常隐藏内部细节
    body = response.json()
    assert body["code"] == "INTERNAL_ERROR"
    assert body["retryable"] is True


def test_jobs_match_history_endpoint_returns_404_for_missing_job(db_session, client):
    user = _seed_user(db_session, "user11", "user11@example.com")
    _set_current_user(user.id)

    with patch(
        "src.presentation.api.v1.jobs.job_service.get_job_match_history",
        new=AsyncMock(side_effect=ValueError("job not found")),
        create=True,
    ):
        response = client.get("/api/v1/jobs/999/match-history/")

    assert response.status_code == 404
    # 统一错误格式: code, message, retryable
    body = response.json()
    assert body["code"] == "RESOURCE_NOT_FOUND"
    assert "job not found" in body["message"]


def test_save_external_job_requires_authentication(client):
    response = client.post(
        "/api/v1/jobs/save-external",
        json={
            "title": "Backend Intern",
            "company": "Example Corp",
            "location": "Beijing",
            "description": "Build APIs with FastAPI",
        },
    )
    assert response.status_code == 401


def test_save_external_job_succeeds_with_valid_payload(db_session, client):
    user = _seed_user(db_session, "ext_job_user", "ext_job_user@example.com")
    _set_current_user(user.id)

    response = client.post(
        "/api/v1/jobs/save-external",
        json={
            "title": "Backend Intern",
            "company": "Example Corp",
            "location": "Beijing",
            "description": "Build APIs with FastAPI and SQLAlchemy",
            "source_url": "https://example.com/jobs/123",
        },
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["title"] == "Backend Intern"
    assert payload["company"] == "Example Corp"
    assert payload["location"] == "Beijing"
    assert payload["source_url"] == "https://example.com/jobs/123"


def test_save_external_job_requires_title(db_session, client):
    user = _seed_user(db_session, "ext_job_user2", "ext_job_user2@example.com")
    _set_current_user(user.id)

    response = client.post(
        "/api/v1/jobs/save-external",
        json={
            "title": "",
            "company": "Example Corp",
            "location": "Beijing",
            "description": "Build APIs",
        },
    )
    assert response.status_code == 422  # Pydantic validation before business logic


def test_save_external_job_requires_company(db_session, client):
    user = _seed_user(db_session, "ext_job_user3", "ext_job_user3@example.com")
    _set_current_user(user.id)

    response = client.post(
        "/api/v1/jobs/save-external",
        json={
            "title": "Backend Intern",
            "company": "",
            "location": "Beijing",
            "description": "Build APIs",
        },
    )
    assert response.status_code == 422  # Pydantic validation before business logic


def test_save_external_job_requires_location(db_session, client):
    user = _seed_user(db_session, "ext_job_user4", "ext_job_user4@example.com")
    _set_current_user(user.id)

    response = client.post(
        "/api/v1/jobs/save-external",
        json={
            "title": "Backend Intern",
            "company": "Example Corp",
            "location": "",
            "description": "Build APIs",
        },
    )
    assert response.status_code == 422  # Pydantic validation before business logic


def test_save_external_job_requires_description(db_session, client):
    user = _seed_user(db_session, "ext_job_user5", "ext_job_user5@example.com")
    _set_current_user(user.id)

    response = client.post(
        "/api/v1/jobs/save-external",
        json={
            "title": "Backend Intern",
            "company": "Example Corp",
            "location": "Beijing",
            "description": "",
        },
    )
    assert response.status_code == 422  # Pydantic validation before business logic


def test_save_external_job_trims_whitespace(db_session, client):
    user = _seed_user(db_session, "ext_job_user6", "ext_job_user6@example.com")
    _set_current_user(user.id)

    response = client.post(
        "/api/v1/jobs/save-external",
        json={
            "title": "  Backend Intern  ",
            "company": "  Example Corp  ",
            "location": "  Beijing  ",
            "description": "  Build APIs  ",
        },
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["title"] == "Backend Intern"
    assert payload["company"] == "Example Corp"
    assert payload["location"] == "Beijing"
