"""Tracker API integration tests."""

from datetime import datetime
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from src.data_access.database import Base, get_db
from src.data_access.entities.tracker import TrackerAdvice
from src.data_access.repositories.job_repository import job_repository
from src.data_access.repositories.resume_repository import resume_repository
from src.data_access.repositories.tracker_repository import tracker_repository
from src.data_access.repositories.user_repository import user_repository
from src.presentation.api.deps import get_current_user
from src.presentation.api.v1.tracker import router as tracker_router


engine = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

app = FastAPI()
app.include_router(tracker_router, prefix="/api/v1/tracker", tags=["tracker"])


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


def _seed_resume(db, user_id, title, processed_content="", resume_text=""):
    return resume_repository.create(
        db,
        {
            "user_id": user_id,
            "title": title,
            "original_file_path": f"/tmp/{title}.pdf",
            "file_name": f"{title}.pdf",
            "file_type": "pdf",
            "processed_content": processed_content,
            "resume_text": resume_text,
            "language": "en-US",
        },
    )


def _seed_job(db, title):
    return job_repository.create(
        db,
        {
            "title": title,
            "company": "Test Company",
            "location": "Remote",
            "source": "manual",
        },
    )


def _set_current_user(user_id):
    app.dependency_overrides[get_current_user] = lambda: SimpleNamespace(id=user_id)


def _create_application(client, user_id, job_id, resume_id, status="applied", notes=""):
    _set_current_user(user_id)
    response = client.post(
        "/api/v1/tracker/applications/",
        json={
            "job_id": job_id,
            "resume_id": resume_id,
            "status": status,
            "notes": notes,
        },
    )
    assert response.status_code == 200
    return response.json()


def _seed_tracker_advice(db, application_id, summary):
    record = TrackerAdvice(
        application_id=application_id,
        summary=summary,
        next_steps=["Email recruiter"],
        risks=["No response"],
        raw_content=f"Summary: {summary}",
        provider="mock",
        model="mock-model",
        created_at=datetime(2026, 3, 28, 12, 0, 0),
        updated_at=datetime(2026, 3, 28, 12, 0, 0),
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return record


def test_tracker_api_scopes_records_by_current_user_and_keeps_404s(db_session, client):
    user_1 = _seed_user(db_session, "user1", "user1@example.com")
    user_2 = _seed_user(db_session, "user2", "user2@example.com")
    job = _seed_job(db_session, "Tracker Job")
    resume_1 = _seed_resume(db_session, user_1.id, "resume-one")
    resume_2 = _seed_resume(db_session, user_2.id, "resume-two")

    _set_current_user(user_1.id)
    response = client.post(
        "/api/v1/tracker/applications/",
        json={
            "job_id": job.id,
            "resume_id": resume_1.id,
            "status": "applied",
            "notes": "user one application",
        },
    )
    assert response.status_code == 200
    user_1_application = response.json()

    _set_current_user(user_2.id)
    response = client.post(
        "/api/v1/tracker/applications/",
        json={
            "job_id": job.id,
            "resume_id": resume_2.id,
            "status": "accepted",
            "notes": "user two application",
        },
    )
    assert response.status_code == 200
    user_2_application = response.json()

    _set_current_user(user_1.id)
    response = client.get("/api/v1/tracker/applications/")
    assert response.status_code == 200
    applications = response.json()
    assert len(applications) == 1
    assert applications[0]["id"] == user_1_application["id"]

    response = client.get("/api/v1/tracker/applications/status/applied")
    assert response.status_code == 200
    applications = response.json()
    assert len(applications) == 1
    assert applications[0]["id"] == user_1_application["id"]

    response = client.put(
        f"/api/v1/tracker/applications/{user_2_application['id']}",
        json={"status": "reviewing", "notes": "not your record"},
    )
    assert response.status_code == 404

    response = client.delete(f"/api/v1/tracker/applications/{user_2_application['id']}")
    assert response.status_code == 404


def test_tracker_api_generates_application_advice_without_persisting(db_session, client):
    user = _seed_user(db_session, "tracker-advice-user", "tracker-advice-user@example.com")
    job = _seed_job(db_session, "Tracker Advice Job")
    resume = _seed_resume(
        db_session,
        user.id,
        "tracker-advice-resume",
        processed_content="Built APIs",
    )
    application = _create_application(
        client,
        user.id,
        job.id,
        resume.id,
        status="applied",
        notes="Need advice",
    )
    with patch(
        "src.presentation.api.v1.tracker.tracker_service.generate_tracker_advice_preview",
        new=AsyncMock(
            return_value={
                "mode": "tracker_advice",
                "application_id": application["id"],
                "summary": "Follow up soon.",
                "next_steps": ["Email recruiter", "Tailor resume keywords"],
                "risks": ["Slow response from company"],
                "raw_content": "Summary: Follow up soon.",
                "provider": "mock",
                "model": "mock-model",
            }
        ),
    ):
        _set_current_user(user.id)
        response = client.post(f"/api/v1/tracker/applications/{application['id']}/advice/")

    assert response.status_code == 200
    payload = response.json()
    assert payload["mode"] == "tracker_advice"
    assert payload["application_id"] == application["id"]
    assert payload["raw_content"] == "Summary: Follow up soon."
    assert payload["provider"] == "mock"
    assert payload["model"] == "mock-model"
    assert tracker_repository.get_by_id_and_user_id(db_session, application["id"], user.id) is not None
    assert db_session.query(TrackerAdvice).filter_by(application_id=application["id"]).count() == 0


def test_tracker_api_persists_application_advice(db_session, client):
    user = _seed_user(db_session, "tracker-persist-user", "tracker-persist-user@example.com")
    job = _seed_job(db_session, "Tracker Persist Job")
    resume = _seed_resume(
        db_session,
        user.id,
        "tracker-persist-resume",
        processed_content="Built APIs",
    )
    application = _create_application(client, user.id, job.id, resume.id, notes="Persist it")
    with patch(
        "src.presentation.api.v1.tracker.tracker_service.persist_application_advice",
        new=AsyncMock(
        return_value=SimpleNamespace(
                id=501,
                application_id=application["id"],
                mode="tracker_advice",
                summary="Follow up this week.",
                next_steps=["Email recruiter"],
                risks=["No response"],
                raw_content="Summary: Follow up this week.",
                provider="mock",
                model="mock-model",
                created_at=datetime(2026, 3, 28, 12, 0, 0),
                updated_at=datetime(2026, 3, 28, 12, 0, 0),
            )
        ),
    ):
        _set_current_user(user.id)
        response = client.post(f"/api/v1/tracker/applications/{application['id']}/advice/persist/")

    assert response.status_code == 200
    payload = response.json()
    assert payload["mode"] == "tracker_advice"
    assert payload["application_id"] == application["id"]
    assert payload["summary"] == "Follow up this week."
    assert payload["next_steps"] == ["Email recruiter"]
    assert payload["risks"] == ["No response"]


def test_tracker_api_lists_persisted_advice_history(db_session, client):
    user = _seed_user(db_session, "tracker-history-user", "tracker-history-user@example.com")
    job = _seed_job(db_session, "Tracker History Job")
    resume = _seed_resume(db_session, user.id, "tracker-history-resume", processed_content="Built APIs")
    application = _create_application(client, user.id, job.id, resume.id, notes="History")
    _seed_tracker_advice(db_session, application["id"], "First summary")
    _seed_tracker_advice(db_session, application["id"], "Second summary")

    _set_current_user(user.id)
    response = client.get(f"/api/v1/tracker/applications/{application['id']}/advice-history/")

    assert response.status_code == 200
    payload = response.json()
    assert len(payload) == 2
    assert {item["summary"] for item in payload} == {"First summary", "Second summary"}
    assert {item["application_id"] for item in payload} == {application["id"]}


def test_tracker_api_returns_404_for_missing_application(db_session, client):
    user = _seed_user(db_session, "tracker-missing-user", "tracker-missing-user@example.com")
    job = _seed_job(db_session, "Tracker Missing Job")
    resume = _seed_resume(db_session, user.id, "tracker-missing-resume", processed_content="Built APIs")
    application = _create_application(client, user.id, job.id, resume.id, notes="Need advice")
    with patch(
        "src.presentation.api.v1.tracker.tracker_service.generate_tracker_advice_preview",
        new=AsyncMock(side_effect=ValueError("application not found")),
    ):
        _set_current_user(user.id)
        response = client.post(f"/api/v1/tracker/applications/{application['id']}/advice/")

    assert response.status_code == 404
    assert response.json()["detail"] == "Application not found"


def test_tracker_api_returns_404_for_missing_application_during_persist(db_session, client):
    user = _seed_user(db_session, "tracker-persist-missing", "tracker-persist-missing@example.com")
    _set_current_user(user.id)
    with patch(
        "src.presentation.api.v1.tracker.tracker_service.persist_application_advice",
        new=AsyncMock(side_effect=ValueError("application not found")),
    ):
        response = client.post("/api/v1/tracker/applications/999/advice/persist/")

    assert response.status_code == 404
    assert response.json()["detail"] == "Application not found"


def test_tracker_api_returns_400_for_missing_context(db_session, client):
    user = _seed_user(db_session, "tracker-context-user", "tracker-context-user@example.com")
    job = _seed_job(db_session, "Tracker Context Job")
    resume = _seed_resume(db_session, user.id, "tracker-context-resume")
    application = _create_application(client, user.id, job.id, resume.id, notes="Need advice")
    with patch(
        "src.presentation.api.v1.tracker.tracker_service.generate_tracker_advice_preview",
        new=AsyncMock(side_effect=ValueError("required context is missing")),
    ):
        _set_current_user(user.id)
        response = client.post(f"/api/v1/tracker/applications/{application['id']}/advice/")

    assert response.status_code == 400
    assert response.json()["detail"] == "required context is missing"


def test_tracker_api_rejects_creating_application_with_unowned_resume(db_session, client):
    user_1 = _seed_user(db_session, "tracker-owner-a", "tracker-owner-a@example.com")
    user_2 = _seed_user(db_session, "tracker-owner-b", "tracker-owner-b@example.com")
    job = _seed_job(db_session, "Tracker Ownership Job")
    resume_2 = _seed_resume(
        db_session,
        user_2.id,
        "tracker-unowned-resume",
        processed_content="Owned by another user",
    )

    _set_current_user(user_1.id)
    response = client.post(
        "/api/v1/tracker/applications/",
        json={
            "job_id": job.id,
            "resume_id": resume_2.id,
            "status": "applied",
            "notes": "should fail",
        },
    )

    assert response.status_code == 404
    assert response.json()["detail"] == "Resume not found"


def test_tracker_api_returns_500_for_provider_failure(db_session, client):
    user = _seed_user(db_session, "tracker-provider-user", "tracker-provider-user@example.com")
    job = _seed_job(db_session, "Tracker Provider Job")
    resume = _seed_resume(db_session, user.id, "tracker-provider-resume", processed_content="Built APIs")
    application = _create_application(client, user.id, job.id, resume.id, notes="Need advice")
    with patch(
        "src.presentation.api.v1.tracker.tracker_service.persist_application_advice",
        new=AsyncMock(side_effect=RuntimeError("provider exploded")),
    ):
        _set_current_user(user.id)
        response = client.post(f"/api/v1/tracker/applications/{application['id']}/advice/persist/")

    assert response.status_code == 500
    assert response.json()["detail"] == "Tracker advice persistence failed"
