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
                status="fallback",
                fallback_used=True,
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
    assert payload["status"] == "fallback"
    assert payload["fallback_used"] is True


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


def test_recommended_jobs_returns_structured_results(db_session, client):
    """Test GET /jobs/recommended/ returns structured RecommendedJob list."""
    # Clear any existing jobs from previous tests
    for job in job_repository.get_all(db_session):
        job_repository.delete(db_session, job.id)
    db_session.commit()

    job1 = job_repository.create(
        db_session,
        {
            "title": "Backend Intern",
            "company": "TechCorp",
            "location": "Beijing",
            "description": "Build APIs with FastAPI",
            "requirements": "Python",
            "salary": "10k-15k",
            "work_type": "internship",
            "experience": "0-1 year",
            "education": "Bachelor",
            "welfare": "Remote",
            "tags": "python,fastapi",
            "source": "test",
            "source_url": "https://techcorp.com/jobs/1",
            "source_id": "tc-1",
            "is_active": True,
        },
    )
    job2 = job_repository.create(
        db_session,
        {
            "title": "Frontend Intern",
            "company": "WebStudio",
            "location": "Shanghai",
            "description": "Build React components",
            "requirements": "JavaScript, React",
            "salary": "8k-12k",
            "work_type": "internship",
            "experience": "0-1 year",
            "education": "Bachelor",
            "welfare": "Hybrid",
            "tags": "react,javascript",
            "source": "test",
            "source_url": "https://webstudio.com/jobs/2",
            "source_id": "ws-2",
            "is_active": True,
        },
    )

    response = client.get("/api/v1/jobs/recommended/", params={"goal_summary": "backend intern"})

    assert response.status_code == 200
    payload = response.json()
    assert isinstance(payload, list)
    assert len(payload) == 2

    # Verify structure
    job = payload[0]
    assert "id" in job
    assert "title" in job
    assert "company" in job
    assert "location" in job
    assert "work_type" in job
    assert "tags" in job
    assert "recommendation_score" in job
    assert "official_url" in job  # mapped from source_url
    assert "summary" in job

    # Verify official_url is mapped from source_url
    assert job["official_url"] == "https://techcorp.com/jobs/1"
    assert job["tags"] == ["python", "fastapi"]

    # Verify recommendation_score is present and valid
    assert isinstance(job["recommendation_score"], int)
    assert 0 <= job["recommendation_score"] <= 100


def test_recommended_jobs_returns_up_to_5_results(db_session, client):
    """Test GET /jobs/recommended/ returns at most 5 jobs."""
    # Clear any existing jobs from previous tests
    for job in job_repository.get_all(db_session):
        job_repository.delete(db_session, job.id)
    db_session.commit()

    # Create 7 jobs
    for i in range(7):
        job_repository.create(
            db_session,
            {
                "title": f"Job {i}",
                "company": f"Company {i}",
                "location": "Beijing",
                "description": f"Description for job {i}",
                "requirements": "Python",
                "salary": "10k",
                "work_type": "internship",
                "experience": "0-1 year",
                "education": "Bachelor",
                "welfare": "Remote",
                "tags": "python",
                "source": "test",
                "source_url": f"https://example.com/jobs/{i}",
                "source_id": f"job-{i}",
                "is_active": True,
            },
        )

    response = client.get("/api/v1/jobs/recommended/")

    assert response.status_code == 200
    payload = response.json()
    assert len(payload) <= 5


def test_recommended_jobs_returns_empty_when_no_jobs(db_session, client):
    """Test GET /jobs/recommended/ returns empty list when no jobs exist."""
    # Clear any existing jobs from previous tests
    for job in job_repository.get_all(db_session):
        job_repository.delete(db_session, job.id)
    db_session.commit()

    response = client.get("/api/v1/jobs/recommended/", params={"goal_summary": "backend"})

    assert response.status_code == 200
    payload = response.json()
    assert payload == []


def test_recommended_jobs_passes_goal_summary_to_service(client):
    with patch(
        "src.presentation.api.v1.jobs.job_service.get_recommended_jobs",
        new=AsyncMock(return_value=[]),
    ) as mock_service:
        response = client.get(
            "/api/v1/jobs/recommended/",
            params={"goal_summary": "DevOps engineer Hangzhou"},
        )

    assert response.status_code == 200
    _, kwargs = mock_service.await_args
    assert kwargs["goal_summary"] == "DevOps engineer Hangzhou"
    assert kwargs["limit"] == 5


def test_jobs_update_job_is_active_toggle(db_session, client):
    """Integration test: update is_active field to mark job as ended."""
    user = _seed_user(db_session, "job_updater", "job_updater@example.com")
    job = _seed_job(db_session)
    _set_current_user(user.id)

    # Initially active
    assert job.is_active is True

    # Update to inactive (ended)
    response = client.put(
        f"/api/v1/jobs/{job.id}",
        json={"is_active": False},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["id"] == job.id
    assert payload["is_active"] is False


def test_jobs_update_job_title(db_session, client):
    """Integration test: update job title."""
    user = _seed_user(db_session, "job_title_updater", "job_title_updater@example.com")
    job = _seed_job(db_session)
    _set_current_user(user.id)

    response = client.put(
        f"/api/v1/jobs/{job.id}",
        json={"title": "Frontend Intern Updated"},
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["title"] == "Frontend Intern Updated"
    assert payload["company"] == "Test Co"  # unchanged


def test_jobs_delete_job_succeeds(db_session, client):
    """Integration test: delete an existing job."""
    user = _seed_user(db_session, "job_deleter", "job_deleter@example.com")
    job = _seed_job(db_session)
    _set_current_user(user.id)

    response = client.delete(f"/api/v1/jobs/{job.id}")
    assert response.status_code == 204

    # Verify job is gone
    get_response = client.get(f"/api/v1/jobs/{job.id}")
    assert get_response.status_code == 404


def test_jobs_delete_job_returns_404_for_nonexistent(db_session, client):
    """Delete returns 404 for non-existent job ID."""
    user = _seed_user(db_session, "job_deleter2", "job_deleter2@example.com")
    _set_current_user(user.id)

    response = client.delete("/api/v1/jobs/99999")
    assert response.status_code == 404
    body = response.json()
    assert body["code"] == "RESOURCE_NOT_FOUND"


def test_create_application_requires_authentication(db_session, client):
    job = _seed_job(db_session)
    user = _seed_user(db_session, "applicant_auth", "applicant_auth@example.com")
    resume = _seed_resume(db_session, user.id)

    response = client.post(
        "/api/v1/jobs/applications/",
        json={"job_id": job.id, "resume_id": resume.id, "notes": "submitted"},
    )

    assert response.status_code == 401


def test_create_application_succeeds_for_owned_resume(db_session, client):
    user = _seed_user(db_session, "applicant_ok", "applicant_ok@example.com")
    job = _seed_job(db_session)
    resume = _seed_resume(db_session, user.id)
    _set_current_user(user.id)

    response = client.post(
        "/api/v1/jobs/applications/",
        json={"job_id": job.id, "resume_id": resume.id, "notes": "already applied"},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["user_id"] == user.id
    assert payload["job_id"] == job.id
    assert payload["resume_id"] == resume.id
    assert payload["status"] == "applied"
    assert payload["notes"] == "already applied"


def test_create_application_returns_404_for_missing_job(db_session, client):
    user = _seed_user(db_session, "applicant_missing_job", "applicant_missing_job@example.com")
    resume = _seed_resume(db_session, user.id)
    _set_current_user(user.id)

    response = client.post(
        "/api/v1/jobs/applications/",
        json={"job_id": 999, "resume_id": resume.id},
    )

    assert response.status_code == 404
    body = response.json()
    assert body["code"] == "RESOURCE_NOT_FOUND"
    assert "job not found" in body["message"]


def test_create_application_returns_404_for_unowned_resume(db_session, client):
    owner = _seed_user(db_session, "applicant_owner", "applicant_owner@example.com")
    other = _seed_user(db_session, "applicant_other", "applicant_other@example.com")
    job = _seed_job(db_session)
    resume = _seed_resume(db_session, other.id)
    _set_current_user(owner.id)

    response = client.post(
        "/api/v1/jobs/applications/",
        json={"job_id": job.id, "resume_id": resume.id},
    )

    assert response.status_code == 404
    body = response.json()
    assert body["code"] == "RESOURCE_NOT_FOUND"
    assert "resume not found" in body["message"]


def test_list_applications_returns_current_user_records_only(db_session, client):
    owner = _seed_user(db_session, "applicant_list_owner", "applicant_list_owner@example.com")
    other = _seed_user(db_session, "applicant_list_other", "applicant_list_other@example.com")
    job1 = _seed_job(db_session)
    job2 = job_repository.create(
        db_session,
        {
            "title": "Platform Intern",
            "company": "Infra Co",
            "location": "Shanghai",
            "description": "Work on infra",
            "requirements": "Python, Linux",
            "salary": "12k-18k",
            "work_type": "internship",
            "experience": "0-1 year",
            "education": "Bachelor",
            "welfare": "Hybrid",
            "tags": "python,linux",
            "source": "test",
            "source_url": "https://example.com/job/2",
            "source_id": "job-2",
            "is_active": True,
        },
    )
    resume1 = _seed_resume(db_session, owner.id)
    resume2 = _seed_resume(db_session, other.id)

    _set_current_user(owner.id)
    first = client.post(
        "/api/v1/jobs/applications/",
        json={"job_id": job1.id, "resume_id": resume1.id, "notes": "owner"},
    )
    assert first.status_code == 200

    _set_current_user(other.id)
    second = client.post(
        "/api/v1/jobs/applications/",
        json={"job_id": job2.id, "resume_id": resume2.id, "notes": "other"},
    )
    assert second.status_code == 200

    _set_current_user(owner.id)
    response = client.get("/api/v1/jobs/applications/")

    assert response.status_code == 200
    payload = response.json()
    assert len(payload) == 1
    assert payload[0]["user_id"] == owner.id
    assert payload[0]["job_id"] == job1.id
    assert payload[0]["notes"] == "owner"
